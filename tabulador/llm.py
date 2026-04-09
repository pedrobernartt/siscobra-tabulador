"""
Wrapper da chamada à API Anthropic.
Implementa prompt caching, retry em JSON malformado e cálculo de custo.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import anthropic
from dotenv import load_dotenv

from .prompt import montar_system_prompt
from .taxonomia import validar_par

load_dotenv()


def _obter_api_key() -> str:
    """Lê a API key do st.secrets (Streamlit Cloud) ou do .env (local)."""
    try:
        import streamlit as st
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


# ── Configuração ──────────────────────────────────────────────────────────────

_MODELO_PADRAO = os.getenv("MODEL_NAME", "claude-sonnet-4-5")

# Preços por milhão de tokens (USD) — atualizar se a Anthropic mudar
_PRECOS: dict[str, dict[str, float]] = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0, "cache_write": 1.0, "cache_read": 0.08},
}

_PRECO_FALLBACK = {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30}


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


def _calcular_custo(
    modelo: str,
    tokens_input: int,
    tokens_output: int,
    tokens_cache_write: int,
    tokens_cache_read: int,
) -> float:
    """Calcula o custo estimado em USD."""
    precos = _PRECOS.get(modelo, _PRECO_FALLBACK)
    custo = (
        (tokens_input / 1_000_000) * precos["input"]
        + (tokens_output / 1_000_000) * precos["output"]
        + (tokens_cache_write / 1_000_000) * precos["cache_write"]
        + (tokens_cache_read / 1_000_000) * precos["cache_read"]
    )
    return round(custo, 6)


def _parsear_resposta(texto: str) -> dict:
    """
    Tenta parsear o JSON retornado pelo LLM.
    Remove blocos de markdown se o modelo os incluir por engano.
    """
    texto = texto.strip()
    # Remove ```json ... ``` se presente
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


def tabular(conversa_formatada: str, modelo: str | None = None) -> ResultadoTabulacao:
    """
    Envia a conversa ao LLM e retorna a tabulação estruturada.
    Em caso de JSON malformado, faz um re-prompt uma vez.
    """
    modelo = modelo or _MODELO_PADRAO
    client = anthropic.Anthropic(api_key=_obter_api_key())
    system_prompt = montar_system_prompt()
    inicio = time.time()

    def _chamar_api(mensagens: list[dict]) -> anthropic.types.Message:
        return client.messages.create(
            model=modelo,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},  # Prompt caching
                }
            ],
            messages=mensagens,
        )

    mensagens_usuario: list[dict] = [
        {
            "role": "user",
            "content": (
                "Analise o conteúdo abaixo (pode ser um export do WhatsApp com timestamps "
                "ou um resumo/narrativa da conversa) e retorne a tabulação em JSON conforme instruído.\n\n"
                f"```\n{conversa_formatada}\n```"
            ),
        }
    ]

    resposta = _chamar_api(mensagens_usuario)
    texto_resposta = resposta.content[0].text

    # Tenta parsear; se falhar, faz re-prompt uma vez
    try:
        dados = _parsear_resposta(texto_resposta)
        _validar_estrutura(dados)
    except (json.JSONDecodeError, ValueError) as erro_original:
        # Re-prompt pedindo correção
        mensagens_usuario.append({"role": "assistant", "content": texto_resposta})
        mensagens_usuario.append(
            {
                "role": "user",
                "content": (
                    f"O JSON retornado é inválido: {erro_original}. "
                    "Corrija e retorne APENAS o JSON válido, sem markdown."
                ),
            }
        )
        resposta = _chamar_api(mensagens_usuario)
        texto_resposta = resposta.content[0].text
        dados = _parsear_resposta(texto_resposta)
        _validar_estrutura(dados)

    tempo = round(time.time() - inicio, 2)

    # Extrai contadores de tokens (com suporte a prompt caching)
    uso = resposta.usage
    tokens_input = getattr(uso, "input_tokens", 0)
    tokens_output = getattr(uso, "output_tokens", 0)
    tokens_cache_write = getattr(uso, "cache_creation_input_tokens", 0)
    tokens_cache_read = getattr(uso, "cache_read_input_tokens", 0)

    custo = _calcular_custo(modelo, tokens_input, tokens_output, tokens_cache_write, tokens_cache_read)

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
        tokens_cache_write=tokens_cache_write,
        tokens_cache_read=tokens_cache_read,
        custo_usd=custo,
        modelo=modelo,
        tempo_segundos=tempo,
    )
