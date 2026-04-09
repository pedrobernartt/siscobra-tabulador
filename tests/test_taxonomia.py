"""
Testes da taxonomia Siscobra.
Garante que todos os pares válidos são aceitos e inválidos são rejeitados.
Inclui cobertura para a Situação Acordo (v2).
"""
import pytest

from tabulador.taxonomia import (
    TAXONOMIA,
    gerar_tabela_markdown,
    listar_pares_validos,
    obter_complemento,
    obter_situacao,
    obter_situacao_por_codigo,
    validar_par,
)

# ── Pares válidos esperados ───────────────────────────────────────────────────

PARES_VALIDOS = [
    # Contato (26)
    ("Contato", "Proposta"),
    ("Contato", "Sem interesse"),
    ("Contato", "Sem sucesso"),
    ("Contato", "Terceiros"),
    # Acordo (2) — adicionado em v2
    ("Acordo", "Acordo com uso de Alvará CJ"),
    ("Acordo", "Acordo extrajudicial à vista CJ"),
    ("Acordo", "Acordo extrajudicial Parcelado CJ"),
    ("Acordo", "Acordo judicial à vista CJ"),
    ("Acordo", "Acordo judicial parcelado CJ"),
    # Contato com terceiros (6)
    ("Contato com terceiros", "Desconhece a pessoa/cobrança"),
    ("Contato com terceiros", "Inquilino"),
    ("Contato com terceiros", "Novo proprietário"),
    ("Contato com terceiros", "Representante legal (Advogado)"),
    ("Contato com terceiros", "Recado"),
    # Dúvidas gerais (3)
    ("Dúvidas gerais", "Dúvidas de preenchimento link Quita+"),
    ("Dúvidas gerais", "Encargos (juros/mora/HO)"),
    ("Dúvidas gerais", "Solicitação CND"),
    ("Dúvidas gerais", "Cliente adimplente"),
    # Recusa acordo (9)
    ("Recusa acordo", "Alega pagamento"),
    ("Recusa acordo", "Discorda do valor cobrado"),
    ("Recusa acordo", "Não informou o motivo"),
    ("Recusa acordo", "Sem previsão de pagamento"),
]

PARES_INVALIDOS = [
    # Complementos cruzados entre situações
    ("Contato", "Inquilino"),
    ("Contato com terceiros", "Proposta"),
    ("Dúvidas gerais", "Proposta"),
    ("Recusa acordo", "Proposta"),
    ("Recusa acordo", "Inquilino"),
    # Acordo com complementos de outras situações (crítico — v2)
    ("Acordo", "Proposta"),
    ("Acordo", "Sem interesse"),
    ("Acordo", "Inquilino"),
    ("Acordo", "Alega pagamento"),
    # Complementos de Acordo em situações erradas
    ("Contato", "Acordo judicial parcelado CJ"),
    ("Contato com terceiros", "Acordo extrajudicial Parcelado CJ"),
    ("Recusa acordo", "Acordo judicial à vista CJ"),
    # Situação inexistente
    ("Não existe", "Proposta"),
    ("", "Proposta"),
    # Complemento inexistente
    ("Contato", ""),
    ("Contato", "Aplicativo da administração"),
    ("Dúvidas gerais", "Solicitação de taxa abaixo de 29 dias"),
    ("Acordo", ""),
    ("Acordo", "Acordo parcelado"),  # nome incompleto — não existe
]


class TestValidarPar:
    def test_todos_pares_validos_sao_aceitos(self):
        for situacao, complemento in PARES_VALIDOS:
            assert validar_par(situacao, complemento), (
                f"Par válido rejeitado: '{situacao}' / '{complemento}'"
            )

    def test_pares_invalidos_sao_rejeitados(self):
        for situacao, complemento in PARES_INVALIDOS:
            assert not validar_par(situacao, complemento), (
                f"Par inválido aceito: '{situacao}' / '{complemento}'"
            )


class TestAcordoV2:
    """Testes específicos para a Situação Acordo adicionada na v2."""

    def test_cinco_complementos_de_acordo_sao_validos(self):
        complementos_acordo = [
            "Acordo com uso de Alvará CJ",
            "Acordo extrajudicial à vista CJ",
            "Acordo extrajudicial Parcelado CJ",
            "Acordo judicial à vista CJ",
            "Acordo judicial parcelado CJ",
        ]
        for comp in complementos_acordo:
            assert validar_par("Acordo", comp), (
                f"Complemento de Acordo rejeitado: '{comp}'"
            )

    def test_acordo_proposta_e_invalido(self):
        """Combinação cruzada crítica: Acordo + Proposta não existe."""
        assert not validar_par("Acordo", "Proposta")

    def test_contato_acordo_judicial_e_invalido(self):
        """Complemento de Acordo não pode ser usado em Contato."""
        assert not validar_par("Contato", "Acordo judicial à vista CJ")

    def test_acordo_codigo_2(self):
        sit = obter_situacao("Acordo")
        assert sit is not None
        assert sit.codigo == 2

    def test_acordo_tem_exatamente_cinco_complementos(self):
        sit = obter_situacao("Acordo")
        assert sit is not None
        assert len(sit.complementos) == 5

    def test_codigos_complementos_acordo(self):
        sit = obter_situacao("Acordo")
        codigos = {c.codigo for c in sit.complementos}
        assert codigos == {1, 2, 3, 4, 5}

    def test_obter_por_codigo_2(self):
        sit = obter_situacao_por_codigo(2)
        assert sit is not None
        assert sit.nome == "Acordo"

    def test_acordo_esta_em_listar_pares_validos(self):
        pares = set(listar_pares_validos())
        pares_acordo = {p for p in pares if p[0] == "Acordo"}
        assert len(pares_acordo) == 5

    def test_tabela_markdown_inclui_acordo(self):
        tabela = gerar_tabela_markdown()
        assert "Acordo" in tabela
        assert "Acordo judicial parcelado CJ" in tabela
        assert "Acordo extrajudicial Parcelado CJ" in tabela
        assert "Alvará CJ" in tabela


class TestListarPares:
    def test_quantidade_de_pares(self):
        pares = listar_pares_validos()
        # 4 (Contato) + 5 (Acordo) + 5 (Contato c/ terceiros) + 4 (Dúvidas) + 4 (Recusa) = 22
        assert len(pares) == 22

    def test_todos_pares_validos_estao_na_lista(self):
        pares = set(listar_pares_validos())
        for par in PARES_VALIDOS:
            assert par in pares, f"Par ausente em listar_pares_validos(): {par}"

    def test_sem_duplicatas(self):
        pares = listar_pares_validos()
        assert len(pares) == len(set(pares))


class TestObtencaoDeObjetos:
    def test_obter_situacao_valida(self):
        sit = obter_situacao("Contato")
        assert sit is not None
        assert sit.codigo == 26

    def test_obter_situacao_invalida(self):
        assert obter_situacao("Inventada") is None

    def test_obter_situacao_por_codigo_6(self):
        sit = obter_situacao_por_codigo(6)
        assert sit is not None
        assert sit.nome == "Contato com terceiros"

    def test_obter_complemento_valido(self):
        comp = obter_complemento("Recusa acordo", "Alega pagamento")
        assert comp is not None
        assert comp.codigo == 1

    def test_obter_complemento_acordo_parcelado(self):
        comp = obter_complemento("Acordo", "Acordo judicial parcelado CJ")
        assert comp is not None
        assert comp.codigo == 5

    def test_obter_complemento_invalido(self):
        assert obter_complemento("Contato", "Não existe") is None


class TestTaxonomiaCompleta:
    def test_cinco_situacoes(self):
        """v2: agora são 5 situações (Contato, Acordo, Contato c/ terceiros, Dúvidas, Recusa)."""
        assert len(TAXONOMIA) == 5

    def test_codigos_situacoes(self):
        codigos = {s.codigo for s in TAXONOMIA}
        assert codigos == {26, 2, 6, 3, 9}

    def test_todos_complementos_tem_codigo_e_nome(self):
        for sit in TAXONOMIA:
            for comp in sit.complementos:
                assert comp.codigo > 0
                assert comp.nome.strip() != ""
                assert comp.quando_usar.strip() != ""

    def test_gerar_tabela_markdown_completa(self):
        tabela = gerar_tabela_markdown()
        for termo in ["Contato", "Acordo", "Proposta", "Recusa acordo",
                      "Dúvidas gerais", "Contato com terceiros",
                      "Acordo judicial parcelado CJ", "Alvará CJ"]:
            assert termo in tabela, f"Termo ausente na tabela markdown: '{termo}'"


class TestCasosDeBorda:
    def test_case_sensitive(self):
        assert not validar_par("contato", "proposta")
        assert validar_par("Contato", "Proposta")
        assert not validar_par("acordo", "acordo judicial parcelado cj")
        assert validar_par("Acordo", "Acordo judicial parcelado CJ")

    def test_nenhuma_situacao_aceita_complemento_arbitrario(self):
        for sit in TAXONOMIA:
            assert not validar_par(sit.nome, "XYZ qualquer coisa")
