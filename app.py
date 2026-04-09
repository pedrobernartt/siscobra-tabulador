"""
Interface Streamlit — Auto-Tabulação Siscobra.
"""
import streamlit as st

from tabulador.categorias import listar_nomes_categorias, obter_categoria
from tabulador.config import carregar_config, salvar_operadores
from tabulador.db import atualizar_feedback, listar_historico, salvar_tabulacao
from tabulador.llm import tabular
from tabulador.parser import formatar_para_llm, parsear_conversa, tem_formato_kommo, tem_formato_whatsapp

st.set_page_config(
    page_title="Tabulador Siscobra",
    page_icon="📋",
    layout="wide",
)

_COR_CONFIANCA = {"alta": "🟢", "media": "🟡", "baixa": "🔴"}

# ── Navegação ─────────────────────────────────────────────────────────────────

aba_principal, aba_categorias, aba_historico, aba_config = st.tabs([
    "📋 Tabulação por Conversa",
    "📂 Tabulação por Categoria",
    "🕒 Histórico",
    "⚙️ Configurações",
])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

with aba_principal:
    st.title("Auto-Tabulação Siscobra")

    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        conversa_raw = st.text_area(
            "Cole a conversa ou resumo aqui",
            height=500,
            placeholder=(
                "Cole o conteúdo do WhatsApp, do Kommo ou um resumo da conversa.\n\n"
                "Exemplos aceitos:\n"
                "• Export do WhatsApp (com timestamps)\n"
                "• Mensagens copiadas do Kommo\n"
                "• Resumo gerado pelo Kommo"
            ),
        )
        botao_tabular = st.button("Tabular", type="primary", use_container_width=True)

    with col_output:
        if "resultado" not in st.session_state:
            st.session_state.resultado = None
        if "id_tabulacao" not in st.session_state:
            st.session_state.id_tabulacao = None
        if "descritivo_editado" not in st.session_state:
            st.session_state.descritivo_editado = ""

        if botao_tabular:
            if not conversa_raw.strip():
                st.error("Cole a conversa antes de tabular.")
            else:
                with st.spinner("Analisando..."):
                    try:
                        config = carregar_config()
                        modelo = config.get("modelo", "claude-sonnet-4-5")

                        mensagens = parsear_conversa(conversa_raw)
                        conversa_formatada = formatar_para_llm(mensagens) if mensagens else conversa_raw

                        resultado = tabular(conversa_formatada, modelo=modelo)

                        id_tab = salvar_tabulacao(
                            conversa_input=conversa_raw,
                            situacao=resultado.situacao_atual,
                            situacao_codigo=resultado.situacao_codigo,
                            complemento=resultado.complemento,
                            complemento_codigo=resultado.complemento_codigo,
                            descritivo=resultado.descritivo,
                            confianca=resultado.confianca,
                            observacoes=resultado.observacoes_para_operador,
                            modelo=resultado.modelo,
                            tokens_input=resultado.tokens_input,
                            tokens_output=resultado.tokens_output,
                            tokens_cache_write=resultado.tokens_cache_write,
                            tokens_cache_read=resultado.tokens_cache_read,
                            custo_usd=resultado.custo_usd,
                            tempo_segundos=resultado.tempo_segundos,
                        )

                        st.session_state.resultado = resultado
                        st.session_state.id_tabulacao = id_tab
                        st.session_state.descritivo_editado = resultado.descritivo

                    except Exception as e:
                        st.error(f"Erro ao tabular: {e}")

        resultado = st.session_state.resultado

        if resultado:
            icone = _COR_CONFIANCA.get(resultado.confianca, "⚪")
            st.caption(f"Confiança {icone}")

            if resultado.observacoes_para_operador:
                st.warning(resultado.observacoes_para_operador)

            st.divider()

            st.markdown("**Situação Atual**")
            st.code(resultado.situacao_atual, language="")

            st.markdown("**Complemento**")
            st.code(resultado.complemento, language="")

            st.markdown("**Descritivo**")
            descritivo_atual = st.text_area(
                "Descritivo",
                value=st.session_state.descritivo_editado,
                height=160,
                key="descritivo_campo",
                label_visibility="collapsed",
            )
            st.session_state.descritivo_editado = descritivo_atual

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Aprovar", use_container_width=True, type="primary"):
                    atualizar_feedback(st.session_state.id_tabulacao, status_operador="aprovado")
                    st.success("Salvo!")
            with col_b:
                if st.button("✏️ Salvar com edição", use_container_width=True):
                    editado = descritivo_atual != resultado.descritivo
                    atualizar_feedback(
                        st.session_state.id_tabulacao,
                        status_operador="editado" if editado else "aprovado",
                        descritivo_editado=descritivo_atual if editado else None,
                    )
                    st.success("Salvo!")

# ═══════════════════════════════════════════════════════════════════════════════
# ABA CATEGORIAS
# ═══════════════════════════════════════════════════════════════════════════════

with aba_categorias:
    st.title("Tabulação por Categoria")
    st.caption("Selecione a categoria da unidade para ver as opções de tabulação com exemplos.")

    cat_selecionada = st.selectbox(
        "Categoria da unidade",
        options=["— selecione —"] + listar_nomes_categorias(),
        index=0,
        key="cat_select",
    )

    if cat_selecionada != "— selecione —":
        categoria = obter_categoria(cat_selecionada)

        if categoria:
            st.caption(categoria.descricao)
            st.divider()

            if categoria.subcategorias:
                sub_selecionada = st.radio(
                    "Sub-cenário:",
                    options=[s.nome for s in categoria.subcategorias],
                    key="sub_select",
                    horizontal=True,
                )
                opcoes = next(
                    (s.opcoes for s in categoria.subcategorias if s.nome == sub_selecionada), []
                )
            else:
                opcoes = categoria.opcoes

            for i, opcao in enumerate(opcoes, start=1):
                with st.container(border=True):
                    col_sit, col_comp = st.columns(2)
                    with col_sit:
                        st.markdown("**Situação Atual**")
                        st.code(opcao.situacao, language="")
                    with col_comp:
                        st.markdown("**Complemento**")
                        st.code(opcao.complemento, language="")

                    st.caption(f"Quando usar: {opcao.quando_usar}")

                    st.markdown("**Descritivo** *(substitua os `[CAMPOS]` pelos dados reais)*")
                    st.text_area(
                        "template",
                        value=opcao.template,
                        height=120,
                        key=f"tpl_{i}",
                        label_visibility="collapsed",
                    )

                    with st.expander("Ver exemplo preenchido"):
                        st.info(opcao.exemplo)

# ═══════════════════════════════════════════════════════════════════════════════
# ABA HISTÓRICO
# ═══════════════════════════════════════════════════════════════════════════════

with aba_historico:
    st.title("Histórico")

    filtro = st.selectbox(
        "Filtrar",
        options=["Todos", "aprovado", "editado", "sem feedback"],
        index=0,
    )

    filtro_db = filtro if filtro not in ("Todos", "sem feedback") else None
    rows = listar_historico(limite=50, filtro_status=filtro_db)

    if filtro == "sem feedback":
        rows = [r for r in rows if r["status_operador"] is None]

    if not rows:
        st.info("Nenhuma tabulação encontrada.")
    else:
        st.caption(f"{len(rows)} registro(s)")
        for row in rows:
            icone = {"aprovado": "✅", "editado": "✏️"}.get(row["status_operador"] or "", "⏳")
            with st.expander(
                f"{icone}  {row['situacao']} / {row['complemento']} — {row['timestamp'][:16]}"
            ):
                st.markdown(f"**Situação:** {row['situacao']}")
                st.markdown(f"**Complemento:** {row['complemento']}")
                descr = row["descritivo_editado"] or row["descritivo"]
                st.markdown(f"**Descritivo:** {descr}")
                if row["observacoes"]:
                    st.warning(row["observacoes"])
                with st.expander("Ver conversa original"):
                    st.text(row["conversa_input"])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

with aba_config:
    st.title("Configurações")

    config_atual = carregar_config()

    # ── Modelo ────────────────────────────────────────────────────────────────
    st.subheader("Modelo de IA")
    modelo_opcoes = {
        "claude-sonnet-4-5": "Sonnet 4.5 — mais preciso (recomendado)",
        "claude-haiku-4-5-20251001": "Haiku 4.5 — mais rápido e econômico",
    }
    modelo_atual = config_atual.get("modelo", "claude-sonnet-4-5")
    modelo_novo = st.selectbox(
        "Modelo",
        options=list(modelo_opcoes.keys()),
        index=list(modelo_opcoes.keys()).index(modelo_atual),
        format_func=lambda m: modelo_opcoes[m],
        key="modelo_select",
    )

    # ── Operadores ────────────────────────────────────────────────────────────
    st.subheader("Operadores da Solug")
    st.caption(
        "Nomes exatamente como aparecem no Kommo (ex: LIZ, JANAINA, JOSI). "
        "Um por linha. Qualquer outro remetente será tratado como cliente."
    )
    operadores_atuais = config_atual.get("operadores", [])
    operadores_texto = st.text_area(
        "Operadores",
        value="\n".join(operadores_atuais),
        height=220,
        key="operadores_campo",
        label_visibility="collapsed",
    )

    if st.button("💾 Salvar configurações", type="primary"):
        novos_ops = [n.strip() for n in operadores_texto.splitlines() if n.strip()]
        config_atual["operadores"] = novos_ops
        config_atual["modelo"] = modelo_novo
        from tabulador.config import salvar_config
        salvar_config(config_atual)
        st.success("Configurações salvas!")
