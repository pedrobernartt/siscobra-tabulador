"""
Taxonomia do Siscobra — fonte da verdade.
Toda combinação Situação/Complemento válida está aqui.
"""
from __future__ import annotations

from pydantic import BaseModel


class Complemento(BaseModel):
    codigo: int
    nome: str
    quando_usar: str


class SituacaoAtual(BaseModel):
    codigo: int
    nome: str
    descricao: str
    complementos: list[Complemento]


# ── Taxonomia completa ────────────────────────────────────────────────────────

TAXONOMIA: list[SituacaoAtual] = [
    SituacaoAtual(
        codigo=26,
        nome="Contato",
        descricao=(
            "Use quando houve interação efetiva com o cliente DEVEDOR (não terceiro) "
            "e a conversa avançou para alguma resolução, proposta ou conclusão."
        ),
        complementos=[
            Complemento(
                codigo=1,
                nome="Proposta",
                quando_usar=(
                    "Cliente pediu condições, operador apresentou proposta, "
                    "cliente está analisando ou negociação está ativa."
                ),
            ),
            Complemento(
                codigo=2,
                nome="Sem interesse",
                quando_usar=(
                    "Cliente declarou que NÃO quer negociar "
                    "(vai resolver no judicial, vai contratar advogado, recusou tudo)."
                ),
            ),
            Complemento(
                codigo=3,
                nome="Sem sucesso",
                quando_usar=(
                    "Proposta foi apresentada e cliente NÃO retornou "
                    "após tentativas de follow-up."
                ),
            ),
            Complemento(
                codigo=4,
                nome="Terceiros",
                quando_usar=(
                    "Cliente principal atendeu, mas a decisão depende de outra pessoa "
                    "(cônjuge, sócio, financeiro, advogado)."
                ),
            ),
        ],
    ),
    SituacaoAtual(
        codigo=6,
        nome="Contato com terceiros",
        descricao=(
            "Use quando NÃO foi o devedor que atendeu — quem respondeu é outra pessoa."
        ),
        complementos=[
            Complemento(
                codigo=1,
                nome="Desconhece a pessoa/cobrança",
                quando_usar=(
                    "Atendente afirma não conhecer o cliente "
                    "(número errado, mudança de titular do telefone)."
                ),
            ),
            Complemento(
                codigo=2,
                nome="Inquilino",
                quando_usar="Quem atendeu se identificou como inquilino/locatário.",
            ),
            Complemento(
                codigo=3,
                nome="Novo proprietário",
                quando_usar=(
                    "Atendente comprou o imóvel e diz não ser responsável "
                    "pelos débitos anteriores."
                ),
            ),
            Complemento(
                codigo=4,
                nome="Representante legal (Advogado)",
                quando_usar="Atendente se identificou como advogado(a) do cliente.",
            ),
            Complemento(
                codigo=5,
                nome="Recado",
                quando_usar=(
                    "Familiar/colega informou que o responsável não está "
                    "e aceitou recado."
                ),
            ),
        ],
    ),
    SituacaoAtual(
        codigo=3,
        nome="Dúvidas gerais",
        descricao=(
            "Use quando o foco da interação foi ESCLARECER uma dúvida, "
            "sem necessariamente avançar em negociação."
        ),
        complementos=[
            Complemento(
                codigo=2,
                nome="Dúvidas de preenchimento link Quita+",
                quando_usar=(
                    "Cliente recebeu o link Quita+ e tem dúvida no preenchimento "
                    "(cartões, parcelas, erro no checkout)."
                ),
            ),
            Complemento(
                codigo=3,
                nome="Encargos (juros/mora/HO)",
                quando_usar=(
                    "Cliente questiona juros, multa, honorários, custas — "
                    "pede memória de cálculo ou reclama do valor."
                ),
            ),
            Complemento(
                codigo=6,
                nome="Solicitação CND",
                quando_usar="Cliente pede Certidão Negativa de Débitos.",
            ),
            Complemento(
                codigo=7,
                nome="Cliente adimplente",
                quando_usar="Cliente em dia entrou em contato para tirar dúvida geral.",
            ),
        ],
    ),
    SituacaoAtual(
        codigo=9,
        nome="Recusa acordo",
        descricao=(
            "Use quando o cliente teve a proposta apresentada e RECUSOU o fechamento — "
            "diferente de 'Sem interesse' porque aqui houve análise da proposta."
        ),
        complementos=[
            Complemento(
                codigo=1,
                nome="Alega pagamento",
                quando_usar="Cliente afirma que já pagou os débitos cobrados.",
            ),
            Complemento(
                codigo=2,
                nome="Discorda do valor cobrado",
                quando_usar=(
                    "Cliente concorda que tem dívida mas discorda do valor "
                    "(encargos, honorários, competências)."
                ),
            ),
            Complemento(
                codigo=3,
                nome="Não informou o motivo",
                quando_usar="Cliente recusou e não quis explicar o porquê.",
            ),
            Complemento(
                codigo=4,
                nome="Sem previsão de pagamento",
                quando_usar=(
                    "Cliente recusou alegando dificuldade financeira sem data prevista."
                ),
            ),
        ],
    ),
]

# ── Índice para acesso rápido ─────────────────────────────────────────────────

_INDICE: dict[str, SituacaoAtual] = {s.nome: s for s in TAXONOMIA}
_INDICE_POR_CODIGO: dict[int, SituacaoAtual] = {s.codigo: s for s in TAXONOMIA}


def validar_par(situacao: str, complemento: str) -> bool:
    """Retorna True se a combinação situacao/complemento é válida na taxonomia."""
    sit = _INDICE.get(situacao)
    if sit is None:
        return False
    return any(c.nome == complemento for c in sit.complementos)


def listar_pares_validos() -> list[tuple[str, str]]:
    """Retorna todos os pares (situacao, complemento) válidos."""
    pares: list[tuple[str, str]] = []
    for sit in TAXONOMIA:
        for comp in sit.complementos:
            pares.append((sit.nome, comp.nome))
    return pares


def obter_situacao(nome: str) -> SituacaoAtual | None:
    """Retorna a SituacaoAtual pelo nome, ou None se não existir."""
    return _INDICE.get(nome)


def obter_situacao_por_codigo(codigo: int) -> SituacaoAtual | None:
    """Retorna a SituacaoAtual pelo código, ou None se não existir."""
    return _INDICE_POR_CODIGO.get(codigo)


def obter_complemento(situacao: str, complemento: str) -> Complemento | None:
    """Retorna o Complemento pelo nome dentro de uma Situação, ou None."""
    sit = _INDICE.get(situacao)
    if sit is None:
        return None
    for c in sit.complementos:
        if c.nome == complemento:
            return c
    return None


def gerar_tabela_markdown() -> str:
    """Gera representação Markdown da taxonomia para uso no system prompt."""
    linhas: list[str] = []
    for sit in TAXONOMIA:
        linhas.append(f"### Situação Atual: `{sit.nome}` (cód. {sit.codigo})")
        linhas.append(sit.descricao)
        linhas.append("")
        linhas.append("| Cód | Complemento | Quando usar |")
        linhas.append("|-----|-------------|-------------|")
        for comp in sit.complementos:
            linhas.append(f"| {comp.codigo} | {comp.nome} | {comp.quando_usar} |")
        linhas.append("")
    return "\n".join(linhas)
