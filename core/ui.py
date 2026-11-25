from typing import Any, Callable
import streamlit as st


def notificar(mensagem: str, tipo: str = "sucesso") -> None:
    """Exibe uma notificação flutuante discreta (toast) sem deslocar o layout."""
    icones = {
        "sucesso": "✅",
        "aviso": "⚠️",
        "erro": "❌",
        "info": "ℹ️",
    }
    st.toast(mensagem, icon=icones.get(tipo, "✅"))


def estado_vazio(titulo: str, subtitulo: str = "", icone: str = "📭") -> None:
    """Renderiza um bloco centralizado limpo quando não há registros para exibir."""
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: 36px 20px;
            margin: 12px 0;
            border: 1px dashed rgba(148, 163, 184, 0.35);
            border-radius: 12px;
            background: rgba(148, 163, 184, 0.04);
        ">
            <div style="font-size: 2rem; margin-bottom: 8px;">{icone}</div>
            <div style="font-weight: 600; font-size: 1rem; margin-bottom: 4px;">{titulo}</div>
            <div style="font-size: 0.85rem; opacity: 0.72;">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Confirmar Operação")
def modal_confirmacao(
    titulo_acao: str,
    descricao: str,
    on_confirmar: Callable[..., Any],
    *args: Any,
    texto_confirmar: str = "Confirmar",
    **kwargs: Any,
) -> None:
    """Modal corporativo para ações críticas (cancelamento de venda, estorno, perda)."""
    st.markdown(f"**{titulo_acao}**")
    st.write(descricao)
    st.markdown("---")

    col_cancelar, col_confirmar = st.columns(2)
    with col_cancelar:
        if st.button("Voltar", use_container_width=True):
            st.rerun()
    with col_confirmar:
        if st.button(texto_confirmar, type="primary", use_container_width=True):
            on_confirmar(*args, **kwargs)
            st.rerun()