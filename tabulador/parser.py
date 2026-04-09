"""
Parser de conversas para o tabulador Siscobra.
Suporta dois formatos de input:
  1. Export bruto do WhatsApp (DD/MM/AAAA HH:MM - Remetente: texto)
  2. Timeline copiada do Kommo CRM (com eventos de sistema misturados)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .config import obter_operadores


# ── Formato WhatsApp ──────────────────────────────────────────────────────────

_WA_CABECALHO = re.compile(
    r"^(\d{2}/\d{2}/\d{4} \d{2}:\d{2}) - ([^:]+): (.*)$"
)

_WA_AVISOS_IGNORAR = {
    "as mensagens e as ligações são protegidas com a criptografia de ponta a ponta",
    "messages and calls are end-to-end encrypted",
}


# ── Formato Kommo ─────────────────────────────────────────────────────────────

_KOMMO_TS = re.compile(
    r"^(\d{2}/\d{2}/\d{4} \d{2}:\d{2}|(?:Hoje|Ontem) \d{2}:\d{2})$"
)

# Linhas de sistema que devem ser ignoradas
_KOMMO_RUIDO = re.compile(
    r"""^(
        SalesBot |
        Movido\ para: |
        de\ [A-ZA-záéíóú] |
        ^Conversa\ *$ |
        ^Conversa\ №\ |
        ^Conversa\ A\d+ |
        ^№\  |
        Campo\ alterado: |
        ^Expandir$ |
        ^Entregue$ |
        ^Ler$ |
        ^Acompanhar |
        ^Excluir$ |
        ^Editar$ |
        de\ Robot\ para |
        O\ valor\ do\ campo |
        marcada\ como\ respondida |
        \d+\ eventos? |
        NÃO\ ESQUECER\ TABULAÇÃO |
        Retorno\ de\ Termo: |
        SOLUG\ \d+ |
        ^Hoje$ |
        ^Ontem$ |
        ^\d{2}/\d{2}/\d{4}$ |
        ^Em\ Interação$ |
        ^PROPOSTA\ ENVIADA$ |
        ^UNIDADE\ SEM\ RETORNO |
        ^minuta |
        ^PLANEJAMENTO$ |
        ^\d{1,2}\ \d{2}/\d{2}/\d{4}\  |
        ^de\ Robot |
        ^Robot |
        ^para\ [A-Z] |
        ^Resumir$ |
        ^Fechar\ conversa$ |
        ^Colocar\ em\ espera$ |
        ^Download$ |
        ^\.$ |
        ^SOLUG\ \d+$
    )""",
    re.VERBOSE | re.IGNORECASE,
)


@dataclass
class Mensagem:
    timestamp: str
    remetente: str
    texto: str
    eh_operador: bool


# ── WhatsApp parser ───────────────────────────────────────────────────────────

def _wa_eh_operador(remetente: str) -> bool:
    operadores = obter_operadores()
    nome = remetente.strip().lower()
    if "+55" in nome:
        return False
    if any(n in nome for n in operadores):
        return True
    return not bool(re.search(r"\d", nome))


def _wa_deve_ignorar(texto: str) -> bool:
    t = texto.strip().lower()
    return any(aviso in t for aviso in _WA_AVISOS_IGNORAR)


def _parsear_whatsapp(texto_bruto: str) -> list[Mensagem]:
    linhas = texto_bruto.splitlines()
    mensagens: list[Mensagem] = []
    msg_atual: dict | None = None

    for linha in linhas:
        match = _WA_CABECALHO.match(linha)
        if match:
            if msg_atual and not _wa_deve_ignorar(msg_atual["texto"]):
                mensagens.append(Mensagem(
                    timestamp=msg_atual["timestamp"],
                    remetente=msg_atual["remetente"],
                    texto=msg_atual["texto"].strip(),
                    eh_operador=_wa_eh_operador(msg_atual["remetente"]),
                ))
            ts, remetente, texto = match.group(1), match.group(2), match.group(3)
            msg_atual = {"timestamp": ts, "remetente": remetente, "texto": texto}
        else:
            if msg_atual is not None:
                msg_atual["texto"] += "\n" + linha

    if msg_atual and not _wa_deve_ignorar(msg_atual["texto"]):
        mensagens.append(Mensagem(
            timestamp=msg_atual["timestamp"],
            remetente=msg_atual["remetente"],
            texto=msg_atual["texto"].strip(),
            eh_operador=_wa_eh_operador(msg_atual["remetente"]),
        ))

    return mensagens


# ── Kommo parser ──────────────────────────────────────────────────────────────

def _kommo_eh_operador(linha: str) -> bool:
    """
    Identifica se uma linha é o nome de um operador.
    Verifica a lista configurada e o padrão ALL-CAPS (ex: LIZ, JANAINA).
    """
    operadores = obter_operadores()
    l = linha.strip().lower()
    if l in operadores:
        return True
    # ALL-CAPS com só letras e espaços = nome de operador (padrão Kommo)
    if re.match(r"^[A-ZÁÉÍÓÚÃÕÇ ]+$", linha.strip()) and 2 <= len(linha.strip()) <= 40:
        return True
    return False


def _kommo_eh_nome(linha: str) -> bool:
    """
    Heurística: linha parece ser um nome próprio (cliente ou operador).
    Exclui linhas que claramente são conteúdo de mensagem.
    """
    linha = linha.strip()
    if not linha or not linha[0].isalpha():
        return False
    # Linhas com pontuação de mensagem não são nomes
    if any(c in linha for c in [":", "http", "?", "!", ".", ",", "🔹", "•", "»", "«", "*"]):
        return False
    # Máximo ~4 palavras para ser um nome
    palavras = linha.split()
    if len(palavras) > 5:
        return False
    # Deve ter pelo menos a primeira letra maiúscula
    return linha[0].isupper()


def _bloco_tem_entregue(linhas: list[str]) -> bool:
    """
    'Entregue' no Kommo indica mensagem enviada pelo operador (confirmação de entrega).
    """
    return any(l.strip().lower() == "entregue" for l in linhas)


def _parsear_kommo(texto_bruto: str) -> list[Mensagem]:
    """
    Parser para a timeline copiada do Kommo CRM.
    Lógica de detecção operador/cliente:
      1. Nome na lista de operadores ou ALL-CAPS → operador
      2. 'Entregue' no bloco sem nome de operador → operador (mensagem direta)
      3. Nome que parece próprio mas não é operador → cliente
      4. Sem nome + sem Entregue → cliente (mensagem recebida do WhatsApp)
    """
    linhas = [l.strip() for l in texto_bruto.splitlines()]

    # Divide em blocos por timestamp
    blocos: list[tuple[str, list[str]]] = []
    ts_atual: str | None = None
    linhas_bloco: list[str] = []

    for linha in linhas:
        if not linha:
            continue
        if _KOMMO_TS.match(linha):
            if ts_atual is not None:
                blocos.append((ts_atual, linhas_bloco))
            ts_atual = linha
            linhas_bloco = []
        else:
            linhas_bloco.append(linha)

    if ts_atual is not None:
        blocos.append((ts_atual, linhas_bloco))

    mensagens: list[Mensagem] = []

    for ts, block_linhas in blocos:
        tem_entregue = _bloco_tem_entregue(block_linhas)

        # Remove ruído (incluindo "Entregue" e "Ler" que já foram verificados acima)
        limpas = [l for l in block_linhas if l and not _KOMMO_RUIDO.match(l)]

        if not limpas:
            continue

        primeira = limpas[0]

        # Determina remetente e conteúdo
        if _kommo_eh_nome(primeira):
            remetente = primeira
            conteudo = limpas[1:]
            eh_op = _kommo_eh_operador(primeira)
        else:
            # Sem nome explícito: usa "Entregue" para determinar direção
            remetente = "Operador" if tem_entregue else "Cliente"
            conteudo = limpas
            eh_op = tem_entregue

        texto = "\n".join(conteudo).strip()
        if not texto:
            continue

        # Descarta blocos que, após limpeza, só têm ruído na primeira linha
        if _KOMMO_RUIDO.match(texto.splitlines()[0]):
            continue

        mensagens.append(Mensagem(
            timestamp=ts,
            remetente=remetente,
            texto=texto,
            eh_operador=eh_op,
        ))

    return mensagens


# ── Interface pública ─────────────────────────────────────────────────────────

def tem_formato_whatsapp(texto: str) -> bool:
    for linha in texto.splitlines()[:15]:
        if _WA_CABECALHO.match(linha.strip()):
            return True
    return False


def tem_formato_kommo(texto: str) -> bool:
    return bool(re.search(r"SalesBot|Conversa\s*№|Movido para:|WhatsApp Business|WhatsApp Lite|Entregue", texto))


def parsear_conversa(texto_bruto: str) -> list[Mensagem]:
    """Detecta o formato e parseia a conversa."""
    if tem_formato_whatsapp(texto_bruto):
        return _parsear_whatsapp(texto_bruto)
    if tem_formato_kommo(texto_bruto):
        return _parsear_kommo(texto_bruto)
    return []


def formatar_para_llm(mensagens: list[Mensagem]) -> str:
    linhas: list[str] = []
    for msg in mensagens:
        prefixo = "[OPERADOR]" if msg.eh_operador else "[CLIENTE]"
        linhas.append(f"{msg.timestamp} {prefixo} {msg.remetente}: {msg.texto}")
    return "\n".join(linhas)
