"""
Wrapper multi-provedor da chamada ao LLM.

Provedores suportados:
  - gemini    → Google Gemini (POSSUI CAMADA GRATUITA). Usa o endpoint compatível
                com a API da OpenAI, então funciona com o SDK `openai`.
  - openai    → GPT (API da OpenAI).
  - anthropic → Claude (legado, pago).

A chave de API é colada na aba Configurações (salva em config.json) ou lida do
ambiente/.env. O system prompt é o mesmo para todos os provedores (prompt.py).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from .config import carregar_config, obter_chave
from .prompt import montar_system_prompt
from .taxonomia import validar_par

load_dotenv()


# ── Catálogo de provedores ────────────────────────────────────────────────────
# tipo: "openai" usa o SDK openai (Gemini reutiliza esse SDK via base_url);
#       "anthropic" usa o SDK anthropic.

PROVEDORES: dict[str, dict] = {
    "gemini": {
        "label": "Google Gemini — possui camada GRATUITA",
        "tipo": "openai",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "modelo_padrao": "gemini-2.5-flash",
        "modelos_sugeridos": ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-2.5-flash-lite"],
        "link_chave": "https://aistudio.google.com/apikey",
    },
    "openai": {
        "label": "OpenAI (GPT)",
        "tipo": "openai",
        "base_url": None,  # usa o endpoint padrão da OpenAI
        "modelo_padrao": "gpt-4o-mini",
        "modelos_sugeridos": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
        "link_chave": "https://platform.openai.com/api-keys",
    },
    "anthropic": {
        "label": "Anthropic (Claude) — pago",
        "tipo": "anthropic",
        "base_url": None,
        "modelo_padrao": "claude-sonnet-4-5",
        "modelos_sugeridos": ["claude-sonnet-4-5", "claude-haiku-4-5-20251001"],
        "link_chave": "https://console.anthropic.com/settings/keys",
    },
}


# Preços por milhão de tokens (USD), só para estimativa no histórico.
# Modelos gratuitos (Gemini free tier) ficam em 0.
_PRECOS: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.0, "output": 0.0},
    "gemini-2.5-flash-lite": {"input": 0.0, "output": 0.0},
    "gemini-3.5-flash": {"input": 0.0, "output": 0.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
}
_PRECO_FALLBACK = {"input": 0.0, "output": 0.0}


@dataclass
class ResultadoTabulacao:
    situacao_atual: str
    situacao_codigo: int
    complemento: str
    complemento_codigo: int
    descritivo: str
    confianca: str
    observacoes_para_operador: str | None
    tokens_input: int
    tokens_output: int
    tokens_cache_write: int
    tokens_cache_read: int
    custo_usd: float
    modelo: str
    tempo_segundos: float


def _calcular_custo(modelo: str, tokens_input: int, tokens_output: int) -> float:
    """Estimativa simples de custo em USD (0 para modelos gratuitos)."""
    precos = _PRECOS.get(modelo, _PRECO_FALLBACK)
    custo = (
        (tokens_input / 1_000_000) * precos["input"]
        + (tokens_output / 1_000_000) * precos["output"]
    )
    return round(custo, 6)


def _parsear_resposta(texto: str) -> dict:
    """
    Tenta parsear o JSON retornado pelo LLM.
    Remove blocos de markdown (```json ... ```) se o modelo os incluir.
    """
    texto = (texto or "").strip()
    if texto.startswith("```"):
        linhas = texto.splitlines()
        texto = "\n".join(linhas[1:-1] if linhas[-1].strip() == "```" else linhas[1:])
    return json.loads(texto)


def _validar_estrutura(dados: dict) -> None:
    """Valida campos obrigatórios e a combinação situacao/complemento."""
    campos = ["situacao_atual", "situacao_codigo", "complemento", "complemento_codigo", "descritivo", "confianca"]
    for campo in campos:
        if campo not in dados:
            raise ValueError(f"Campo obrigatório ausente no JSON: {campo}")

    confianca_valida = {"alta", "media", "baixa"}
    if dados["confianca"] not in confianca_valida:
        raise ValueError(f"Valor inválido para 'confianca': {dados['confianca']}")

    if not validar_par(dados["situacao_atual"], dados["complemento"]):
        raise ValueError(
            f"Par inválido na taxonomia: '{dados['situacao_atual']}' / '{dados['complemento']}'. "
            "Verifique os nomes exatos da taxonomia."
        )


# ── Clientes por provedor ─────────────────────────────────────────────────────

def _criar_enviador(spec: dict, modelo: str, chave: str, system_prompt: str):
    """
    Retorna uma função enviar(mensagens) -> (texto, tokens_input, tokens_output)
    específica do provedor. 'mensagens' é a lista no formato role/content.
    """
    if spec["tipo"] == "openai":
        from openai import OpenAI

        kwargs = {"api_key": chave}
        if spec.get("base_url"):
            kwargs["base_url"] = spec["base_url"]
        client = OpenAI(**kwargs)

        def enviar(mensagens: list[dict]) -> tuple[str, int, int]:
            resposta = client.chat.completions.create(
                model=modelo,
                messages=[{"role": "system", "content": system_prompt}, *mensagens],
                max_tokens=1024,
                temperature=0,
                response_format={"type": "json_object"},
            )
            texto = resposta.choices[0].message.content or ""
            uso = getattr(resposta, "usage", None)
            ti = getattr(uso, "prompt_tokens", 0) or 0
            to = getattr(uso, "completion_tokens", 0) or 0
            return texto, ti, to

        return enviar

    # anthropic
    import anthropic

    client = anthropic.Anthropic(api_key=chave)

    def enviar(mensagens: list[dict]) -> tuple[str, int, int]:
        resposta = client.messages.create(
            model=modelo,
            max_tokens=1024,
            system=system_prompt,
            messages=mensagens,
        )
        texto = resposta.content[0].text
        uso = resposta.usage
        ti = getattr(uso, "input_tokens", 0) or 0
        to = getattr(uso, "output_tokens", 0) or 0
        return texto, ti, to

    return enviar


def tabular(
    conversa_formatada: str,
    provedor: str | None = None,
    modelo: str | None = None,
    chave: str | None = None,
) -> ResultadoTabulacao:
    """
    Envia a conversa ao LLM do provedor escolhido e retorna a tabulação estruturada.
    Em caso de JSON malformado ou par inválido, faz um re-prompt uma vez.
    """
    config = carregar_config()
    provedor = provedor or config.get("provedor", "gemini")
    spec = PROVEDORES.get(provedor) or PROVEDORES["gemini"]
    modelo = modelo or config.get("modelo") or spec["modelo_padrao"]
    chave = chave or obter_chave(provedor)

    if not chave:
        raise RuntimeError(
            f"Nenhuma chave de API configurada para o provedor '{provedor}'. "
            "Abra a aba Configurações, cole a chave e salve."
        )

    system_prompt = montar_system_prompt()
    enviar = _criar_enviador(spec, modelo, chave, system_prompt)
    inicio = time.time()

    mensagens: list[dict] = [
        {
            "role": "user",
            "content": (
                "Analise o conteúdo abaixo (pode ser um export do WhatsApp com timestamps "
                "ou um resumo/narrativa da conversa) e retorne a tabulação em JSON conforme instruído.\n\n"
                f"```\n{conversa_formatada}\n```"
            ),
        }
    ]

    texto, tokens_input, tokens_output = enviar(mensagens)

    try:
        dados = _parsear_resposta(texto)
        _validar_estrutura(dados)
    except (json.JSONDecodeError, ValueError) as erro_original:
        mensagens.append({"role": "assistant", "content": texto})
        mensagens.append(
            {
                "role": "user",
                "content": (
                    f"O JSON retornado é inválido: {erro_original}. "
                    "Corrija e retorne APENAS o JSON válido, sem markdown."
                ),
            }
        )
        texto, ti2, to2 = enviar(mensagens)
        tokens_input += ti2
        tokens_output += to2
        dados = _parsear_resposta(texto)
        _validar_estrutura(dados)

    tempo = round(time.time() - inicio, 2)
    custo = _calcular_custo(modelo, tokens_input, tokens_output)

    return ResultadoTabulacao(
        situacao_atual=dados["situacao_atual"],
        situacao_codigo=dados["situacao_codigo"],
        complemento=dados["complemento"],
        complemento_codigo=dados["complemento_codigo"],
        descritivo=dados["descritivo"],
        confianca=dados["confianca"],
        observacoes_para_operador=dados.get("observacoes_para_operador"),
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tokens_cache_write=0,
        tokens_cache_read=0,
        custo_usd=custo,
        modelo=f"{provedor}:{modelo}",
        tempo_segundos=tempo,
    )
