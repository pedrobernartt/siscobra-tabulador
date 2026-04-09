"""
Categorias especiais de unidades — mapeamento para tabulações Siscobra.
Usado quando NÃO há conversa de WhatsApp: o operador seleciona a categoria
e o sistema exibe as opções válidas com templates do descritivo.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpcaoTabulacao:
    situacao: str
    situacao_codigo: int
    complemento: str
    complemento_codigo: int
    quando_usar: str          # gatilho resumido
    template: str             # template do descritivo com [CAMPOS]
    exemplo: str              # exemplo preenchido do manual


@dataclass
class SubCategoria:
    nome: str
    opcoes: list[OpcaoTabulacao]


@dataclass
class Categoria:
    nome: str
    descricao: str
    subcategorias: list[SubCategoria]   # se vazio, usa opcoes direto
    opcoes: list[OpcaoTabulacao]        # usadas quando não há subcategorias


# ── Definição de todas as categorias ─────────────────────────────────────────

CATEGORIAS: list[Categoria] = [

    Categoria(
        nome="Direto nos autos — não aceita ser cobrado",
        descricao="Devedor recusa contato extrajudicial e quer tratar a questão apenas pelo processo judicial.",
        subcategorias=[],
        opcoes=[
            OpcaoTabulacao(
                situacao="Contato",
                situacao_codigo=26,
                complemento="Sem interesse",
                complemento_codigo=2,
                quando_usar="Devedor atendeu e declarou que não quer negociar fora do processo.",
                template=(
                    "Devedor informou que trata os débitos diretamente nos autos do processo nº [NÚMERO]. "
                    "Declarou não aceitar contato extrajudicial de cobrança. "
                    "Encerrado o atendimento sem proposta aceita."
                ),
                exemplo=(
                    "Devedor informou que trata os débitos diretamente nos autos do processo nº 0001234-56.2024.8.16.0001. "
                    "Declarou não aceitar contato extrajudicial de cobrança e que seu advogado cuida do caso. "
                    "Encerrado o atendimento sem proposta aceita."
                ),
            ),
            OpcaoTabulacao(
                situacao="Contato com terceiros",
                situacao_codigo=6,
                complemento="Representante legal (Advogado)",
                complemento_codigo=4,
                quando_usar="Quem respondeu foi o advogado do devedor, informando que não haverá negociação extrajudicial.",
                template=(
                    "Atendimento realizado pelo advogado do cliente — Dr(a). [NOME] OAB [NÚMERO]. "
                    "Informou que o processo tramita nos autos nº [NÚMERO DO PROCESSO] e que "
                    "não será aceita cobrança extrajudicial. Encerrado o atendimento."
                ),
                exemplo=(
                    "Atendimento realizado pelo advogado do cliente — Dr. Carlos Menezes OAB 98.765/PR. "
                    "Informou que o processo tramita nos autos nº 0002345-67.2024.8.16.0001 e que "
                    "todas as tratativas devem ocorrer exclusivamente nos autos. Encerrado o atendimento."
                ),
            ),
        ],
    ),

    Categoria(
        nome="Ag. Execução / Pendente Minuta",
        descricao="Negociação em andamento com acordo firmado ou minuta pendente de assinatura/cumprimento.",
        subcategorias=[],
        opcoes=[
            OpcaoTabulacao(
                situacao="Contato",
                situacao_codigo=26,
                complemento="Proposta",
                complemento_codigo=1,
                quando_usar="Proposta aceita, minuta elaborada ou em elaboração, aguardando assinatura ou primeira parcela.",
                template=(
                    "Devedor em processo de negociação. "
                    "Minuta de acordo [elaborada / pendente de elaboração] aguardando assinatura. "
                    "Proposta firmada: entrada R$ [VALOR] em [DATA] + [N]x de R$ [VALOR]. "
                    "Processo [suspenso / em fase de execução] aguardando cumprimento."
                ),
                exemplo=(
                    "Devedor em processo de negociação. "
                    "Minuta de acordo elaborada e enviada para assinatura via ZapSign. "
                    "Proposta firmada: entrada R$ 2.000,00 em 10/04/2026 + 11x de R$ 504,36. "
                    "Processo suspenso aguardando confirmação da primeira parcela."
                ),
            ),
            OpcaoTabulacao(
                situacao="Contato",
                situacao_codigo=26,
                complemento="Terceiros",
                complemento_codigo=4,
                quando_usar="Devedor participou da negociação mas a decisão/assinatura depende de cônjuge, sócio ou advogado.",
                template=(
                    "Devedor em processo de negociação. "
                    "Minuta pendente — assinatura depende de [cônjuge / sócio / advogado — NOME se informado]. "
                    "Proposta: entrada R$ [VALOR] em [DATA] + [N]x de R$ [VALOR]. "
                    "Aguardando retorno do decisor até [DATA]."
                ),
                exemplo=(
                    "Devedor em processo de negociação. "
                    "Minuta pendente — assinatura depende do cônjuge, que retorna de viagem em 15/04/2026. "
                    "Proposta: entrada R$ 1.500,00 em 30/04/2026 + 5x de R$ 620,00. "
                    "Aguardando retorno do decisor até 16/04/2026."
                ),
            ),
        ],
    ),

    Categoria(
        nome="Busca na matrícula — contato Lemit",
        descricao="Sem contato com o devedor. Encaminhado ao Lemit para busca cadastral via matrícula do imóvel.",
        subcategorias=[],
        opcoes=[
            OpcaoTabulacao(
                situacao="Contato",
                situacao_codigo=26,
                complemento="Sem sucesso",
                complemento_codigo=3,
                quando_usar="Não foi possível localizar ou contatar o devedor. Caso encaminhado para busca via matrícula.",
                template=(
                    "Ausência de contato com o devedor após [N] tentativas. "
                    "Encaminhado ao setor Lemit para busca cadastral via matrícula do imóvel. "
                    "Aguardando retorno com novos dados de contato."
                ),
                exemplo=(
                    "Ausência de contato com o devedor após 5 tentativas em canais distintos. "
                    "Encaminhado ao setor Lemit para busca cadastral via matrícula do imóvel. "
                    "Aguardando retorno com novos dados de contato."
                ),
            ),
        ],
    ),

    Categoria(
        nome="Unidade s/ matrícula — contato Lemit",
        descricao="Unidade sem matrícula localizada. Encaminhado ao Lemit para busca cadastral alternativa.",
        subcategorias=[],
        opcoes=[
            OpcaoTabulacao(
                situacao="Contato",
                situacao_codigo=26,
                complemento="Sem sucesso",
                complemento_codigo=3,
                quando_usar="Unidade não possui matrícula identificada. Impossível localizar o responsável pelos meios usuais.",
                template=(
                    "Unidade sem matrícula identificada no sistema. "
                    "Ausência de contato com o devedor. "
                    "Encaminhado ao setor Lemit para busca cadastral alternativa. "
                    "Aguardando retorno."
                ),
                exemplo=(
                    "Unidade sem matrícula identificada no sistema. "
                    "Ausência de contato com o devedor após tentativas por WhatsApp e ligação. "
                    "Encaminhado ao setor Lemit para busca cadastral alternativa. "
                    "Aguardando retorno."
                ),
            ),
        ],
    ),

    Categoria(
        nome="Leilão — aguardando valor entrar",
        descricao="Imóvel arrematado em leilão judicial. Aguardando liberação do valor para quitação dos débitos.",
        subcategorias=[
            SubCategoria(
                nome="Com arrematante",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato com terceiros",
                        situacao_codigo=6,
                        complemento="Novo proprietário",
                        complemento_codigo=3,
                        quando_usar="Arrematante entrou em contato ou foi notificado sobre os débitos condominiais.",
                        template=(
                            "Unidade arrematada em leilão judicial (proc. nº [NÚMERO]). "
                            "Arrematante [NOME se disponível] notificado dos débitos condominiais (R$ [VALOR]). "
                            "Aguardando liberação do valor do leilão para quitação dos débitos condominiais."
                        ),
                        exemplo=(
                            "Unidade arrematada em leilão judicial (proc. nº 0003456-78.2023.8.16.0001). "
                            "Arrematante Carlos Eduardo notificado dos débitos condominiais (R$ 18.432,50). "
                            "Aguardando liberação do valor do leilão para quitação dos débitos condominiais."
                        ),
                    ),
                    OpcaoTabulacao(
                        situacao="Dúvidas gerais",
                        situacao_codigo=3,
                        complemento="Solicitação CND",
                        complemento_codigo=6,
                        quando_usar="Arrematante solicitou CND para regularização do imóvel.",
                        template=(
                            "Arrematante solicitou Certidão Negativa de Débitos para regularização do imóvel. "
                            "Informado que a CND será emitida após liberação do valor do leilão "
                            "(R$ [VALOR]) na conta do escritório. Proc. nº [NÚMERO]."
                        ),
                        exemplo=(
                            "Arrematante solicitou Certidão Negativa de Débitos para regularização do imóvel. "
                            "Informado que a CND será emitida após liberação do valor do leilão "
                            "(R$ 18.432,50) na conta do escritório. Proc. nº 0003456-78.2023.8.16.0001."
                        ),
                    ),
                ],
            ),
            SubCategoria(
                nome="Sem arrematante",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato",
                        situacao_codigo=26,
                        complemento="Sem sucesso",
                        complemento_codigo=3,
                        quando_usar="Leilão ainda não homologado ou arrematante não definido. Devedor sem contato.",
                        template=(
                            "Unidade em processo de leilão judicial (proc. nº [NÚMERO]). "
                            "Devedor sem contato efetivo. "
                            "Aguardando [realização / homologação] do leilão para resolução dos débitos condominiais."
                        ),
                        exemplo=(
                            "Unidade em processo de leilão judicial (proc. nº 0003456-78.2023.8.16.0001). "
                            "Devedor sem contato efetivo após múltiplas tentativas. "
                            "Aguardando homologação do leilão para resolução dos débitos condominiais."
                        ),
                    ),
                ],
            ),
        ],
        opcoes=[],
    ),

    Categoria(
        nome="Bloqueio / Depósito cobre débito",
        descricao="Existe bloqueio ou depósito judicial cujo valor cobre os débitos condominiais.",
        subcategorias=[],
        opcoes=[
            OpcaoTabulacao(
                situacao="Recusa acordo",
                situacao_codigo=9,
                complemento="Alega pagamento",
                complemento_codigo=1,
                quando_usar="Devedor ou seu advogado alega que o bloqueio/depósito judicial já quita os débitos.",
                template=(
                    "Processo com bloqueio/depósito judicial que cobre os débitos condominiais "
                    "(R$ [VALOR], proc. nº [NÚMERO]). "
                    "Devedor [informou / advogado informou] que o valor está depositado nos autos. "
                    "Aguardando liberação judicial para baixa dos débitos."
                ),
                exemplo=(
                    "Processo com bloqueio/depósito judicial que cobre os débitos condominiais "
                    "(R$ 12.850,00, proc. nº 0004567-89.2023.8.16.0001). "
                    "Advogado do devedor informou que o valor está depositado nos autos. "
                    "Aguardando liberação judicial para baixa dos débitos."
                ),
            ),
            OpcaoTabulacao(
                situacao="Dúvidas gerais",
                situacao_codigo=3,
                complemento="Solicitação CND",
                complemento_codigo=6,
                quando_usar="Cliente solicita CND aguardando a liberação do bloqueio/depósito para quitação.",
                template=(
                    "Cliente solicitou Certidão Negativa de Débitos. "
                    "Informado que a CND será emitida após liberação do depósito judicial "
                    "(R$ [VALOR], proc. nº [NÚMERO]) para quitação dos débitos condominiais."
                ),
                exemplo=(
                    "Cliente solicitou Certidão Negativa de Débitos. "
                    "Informado que a CND será emitida após liberação do depósito judicial "
                    "(R$ 12.850,00, proc. nº 0004567-89.2023.8.16.0001) para quitação dos débitos condominiais."
                ),
            ),
        ],
    ),

    Categoria(
        nome="Construtora",
        descricao="Devedor é uma construtora ou incorporadora.",
        subcategorias=[
            SubCategoria(
                nome="Sem retorno / sem contato",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato",
                        situacao_codigo=26,
                        complemento="Sem sucesso",
                        complemento_codigo=3,
                        quando_usar="Construtora não responde às tentativas de contato.",
                        template=(
                            "Devedor (construtora [NOME]) sem retorno após múltiplas tentativas de contato "
                            "realizadas em [DATAS]. "
                            "Proposta de quitação encaminhada por [e-mail / WhatsApp]. "
                            "Negociação encerrada sem êxito."
                        ),
                        exemplo=(
                            "Devedor (construtora Horizonte Empreendimentos Ltda.) sem retorno após "
                            "tentativas de contato em 01/04, 03/04 e 07/04/2026. "
                            "Proposta de quitação encaminhada por e-mail. "
                            "Negociação encerrada sem êxito."
                        ),
                    ),
                ],
            ),
            SubCategoria(
                nome="Recusa negociar",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato",
                        situacao_codigo=26,
                        complemento="Sem interesse",
                        complemento_codigo=2,
                        quando_usar="Representante da construtora declarou que não irá negociar.",
                        template=(
                            "Representante da construtora [NOME] declarou desinteresse na negociação. "
                            "Informou que a questão será tratada [nos autos / por advogado / pelo departamento jurídico]. "
                            "Encerrado o atendimento sem proposta aceita."
                        ),
                        exemplo=(
                            "Representante da construtora Alpha Construções declarou desinteresse na negociação. "
                            "Informou que a questão será tratada pelo departamento jurídico da empresa. "
                            "Encerrado o atendimento sem proposta aceita."
                        ),
                    ),
                ],
            ),
            SubCategoria(
                nome="Representada por advogado",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato com terceiros",
                        situacao_codigo=6,
                        complemento="Representante legal (Advogado)",
                        complemento_codigo=4,
                        quando_usar="Atendimento realizado pelo advogado da construtora.",
                        template=(
                            "Atendimento realizado pelo advogado da construtora [NOME DA CONSTRUTORA] — "
                            "Dr(a). [NOME] OAB [NÚMERO]. "
                            "Solicitou [valores atualizados / proposta de acordo / cópia do processo]. "
                            "[Levantamento R$ [VALOR] enviado / proposta apresentada / aguardando instrução do cliente]."
                        ),
                        exemplo=(
                            "Atendimento realizado pelo advogado da construtora Beta Incorporações — "
                            "Dr. Rodrigo Alves OAB 12.345/PR. "
                            "Solicitou valores atualizados e proposta parcelada. "
                            "Levantamento R$ 34.210,00 enviado e proposta apresentada. Aguardando retorno."
                        ),
                    ),
                ],
            ),
        ],
        opcoes=[],
    ),

    Categoria(
        nome="Banco",
        descricao="Imóvel vinculado a banco (financiamento, execução bancária ou leilão do banco).",
        subcategorias=[
            SubCategoria(
                nome="Com arrematante (banco arrematou)",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato com terceiros",
                        situacao_codigo=6,
                        complemento="Novo proprietário",
                        complemento_codigo=3,
                        quando_usar="O banco arrematou o imóvel em leilão e agora é o detentor do bem.",
                        template=(
                            "Imóvel arrematado pelo [NOME DO BANCO] em leilão judicial (proc. nº [NÚMERO]). "
                            "Instituição notificada dos débitos condominiais (R$ [VALOR]). "
                            "Aguardando posicionamento do banco quanto à quitação dos débitos."
                        ),
                        exemplo=(
                            "Imóvel arrematado pelo Banco Bradesco S.A. em leilão judicial (proc. nº 0005678-90.2022.8.16.0001). "
                            "Instituição notificada dos débitos condominiais (R$ 22.450,00). "
                            "Aguardando posicionamento do banco quanto à quitação dos débitos."
                        ),
                    ),
                    OpcaoTabulacao(
                        situacao="Contato com terceiros",
                        situacao_codigo=6,
                        complemento="Representante legal (Advogado)",
                        complemento_codigo=4,
                        quando_usar="O setor jurídico do banco respondeu ao contato.",
                        template=(
                            "Atendimento realizado pelo setor jurídico do [NOME DO BANCO] — "
                            "Dr(a). [NOME] / [e-mail / telefone do jurídico]. "
                            "Notificado sobre os débitos condominiais (R$ [VALOR]). "
                            "Aguardando posicionamento formal da instituição."
                        ),
                        exemplo=(
                            "Atendimento realizado pelo setor jurídico do Banco Itaú S.A. — "
                            "Dra. Fernanda Castro / juridico@itau.com.br. "
                            "Notificado sobre os débitos condominiais (R$ 22.450,00). "
                            "Aguardando posicionamento formal da instituição."
                        ),
                    ),
                ],
            ),
            SubCategoria(
                nome="Sem arrematante (banco credor, imóvel não arrematado)",
                opcoes=[
                    OpcaoTabulacao(
                        situacao="Contato com terceiros",
                        situacao_codigo=6,
                        complemento="Representante legal (Advogado)",
                        complemento_codigo=4,
                        quando_usar="Banco é credor hipotecário e seu jurídico respondeu sobre os débitos.",
                        template=(
                            "Atendimento realizado pelo representante jurídico do [NOME DO BANCO]. "
                            "Banco figura como credor hipotecário no imóvel (proc. nº [NÚMERO]). "
                            "Notificado dos débitos condominiais (R$ [VALOR]). "
                            "Aguardando definição da situação do imóvel (leilão / dação)."
                        ),
                        exemplo=(
                            "Atendimento realizado pelo representante jurídico do Banco Caixa S.A. "
                            "Banco figura como credor hipotecário no imóvel (proc. nº 0006789-01.2021.8.16.0001). "
                            "Notificado dos débitos condominiais (R$ 15.670,00). "
                            "Aguardando definição da situação do imóvel para leilão."
                        ),
                    ),
                    OpcaoTabulacao(
                        situacao="Contato",
                        situacao_codigo=26,
                        complemento="Sem sucesso",
                        complemento_codigo=3,
                        quando_usar="Banco não responde. Imóvel sem devedor localizado e sem arrematante.",
                        template=(
                            "Imóvel vinculado ao [NOME DO BANCO] como credor. "
                            "Ausência de retorno da instituição após tentativas de contato em [DATAS]. "
                            "Encaminhado para acompanhamento do processo nº [NÚMERO]."
                        ),
                        exemplo=(
                            "Imóvel vinculado ao Banco Santander como credor hipotecário. "
                            "Ausência de retorno da instituição após tentativas de contato em 01/04 e 04/04/2026. "
                            "Encaminhado para acompanhamento do processo nº 0007890-12.2021.8.16.0001."
                        ),
                    ),
                ],
            ),
        ],
        opcoes=[],
    ),

    Categoria(
        nome="Não cobrar",
        descricao="Unidade com instrução de suspensão de cobrança.",
        subcategorias=[],
        opcoes=[
            OpcaoTabulacao(
                situacao="Dúvidas gerais",
                situacao_codigo=3,
                complemento="Cliente adimplente",
                complemento_codigo=7,
                quando_usar="Unidade com instrução administrativa de não cobrar. Registro obrigatório no Siscobra.",
                template=(
                    "Unidade com instrução de suspensão de cobrança. "
                    "Motivo: [acordo judicial vigente / determinação do escritório / débito em discussão / outro]. "
                    "Sem ação de cobrança realizada. Aguardando orientação da administradora/escritório."
                ),
                exemplo=(
                    "Unidade com instrução de suspensão de cobrança. "
                    "Motivo: acordo judicial vigente com pagamento sendo realizado via cartório. "
                    "Sem ação de cobrança realizada. Aguardando orientação da administradora."
                ),
            ),
        ],
    ),
]


# ── Acesso rápido ─────────────────────────────────────────────────────────────

def listar_nomes_categorias() -> list[str]:
    return [c.nome for c in CATEGORIAS]


def obter_categoria(nome: str) -> Categoria | None:
    return next((c for c in CATEGORIAS if c.nome == nome), None)
