"""
Testes da taxonomia Siscobra.
Garante que todos os pares válidos são aceitos e inválidos são rejeitados.
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
    # Complemento de outra situação
    ("Contato", "Inquilino"),
    ("Contato com terceiros", "Proposta"),
    ("Dúvidas gerais", "Proposta"),
    ("Recusa acordo", "Proposta"),
    ("Recusa acordo", "Inquilino"),
    # Situação inexistente
    ("Não existe", "Proposta"),
    ("", "Proposta"),
    # Complemento inexistente
    ("Contato", ""),
    ("Contato", "Aplicativo da administração"),  # explicitamente não-aplicável
    ("Dúvidas gerais", "Solicitação de taxa abaixo de 29 dias"),  # não-aplicável
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


class TestListarPares:
    def test_quantidade_de_pares(self):
        pares = listar_pares_validos()
        # 4 + 5 + 4 + 4 = 17 pares
        assert len(pares) == 17

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

    def test_obter_situacao_por_codigo(self):
        sit = obter_situacao_por_codigo(6)
        assert sit is not None
        assert sit.nome == "Contato com terceiros"

    def test_obter_complemento_valido(self):
        comp = obter_complemento("Recusa acordo", "Alega pagamento")
        assert comp is not None
        assert comp.codigo == 1

    def test_obter_complemento_invalido(self):
        assert obter_complemento("Contato", "Não existe") is None


class TestTaxonomiaCompleta:
    def test_quatro_situacoes(self):
        assert len(TAXONOMIA) == 4

    def test_codigos_situacoes(self):
        codigos = {s.codigo for s in TAXONOMIA}
        assert codigos == {26, 6, 3, 9}

    def test_todos_complementos_tem_codigo_e_nome(self):
        for sit in TAXONOMIA:
            for comp in sit.complementos:
                assert comp.codigo > 0
                assert comp.nome.strip() != ""
                assert comp.quando_usar.strip() != ""

    def test_gerar_tabela_markdown_nao_vazia(self):
        tabela = gerar_tabela_markdown()
        assert "Contato" in tabela
        assert "Proposta" in tabela
        assert "Recusa acordo" in tabela
        assert "Dúvidas gerais" in tabela
        assert "Contato com terceiros" in tabela


class TestCasosDeBorda:
    def test_case_sensitive(self):
        """O sistema é case-sensitive — nomes devem ser exatos."""
        assert not validar_par("contato", "proposta")  # minúsculas não funcionam
        assert validar_par("Contato", "Proposta")      # correto

    def test_situacao_nenhum_complemento_fora_da_lista(self):
        """Nenhuma situação deve aceitar complemento arbitrário."""
        for sit in TAXONOMIA:
            assert not validar_par(sit.nome, "XYZ qualquer coisa")
