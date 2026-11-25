import base64
import os
import streamlit as st
from core import auth
from core.style import aplicar_estilo


def logo_topo_sidebar(caminho: str = "logo.png"):
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
                [data-testid="stSidebarNav"]::before {{
                    content: "";
                    display: block;
                    height: 85px;
                    margin: 10px 18px 14px 18px;
                    background-image: url("data:image/png;base64,{img_b64}");
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center center;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )


st.set_page_config(
    page_title="FarmaCore ERP",
    page_icon="💊",
    layout="wide",
)

aplicar_estilo()
usuario = auth.exigir_login()

# Injeta a logo no topo absoluto do menu lateral
logo_topo_sidebar("logo.png")

with st.sidebar:
    st.markdown("---")
    st.subheader(usuario.get("nome", "Desenvolvedor"))
    st.caption(f"{usuario['email']} · {usuario['perfil']}")
    if getattr(st.user, "is_logged_in", False):
        st.button("Sair", on_click=st.logout, use_container_width=True)

# Navegação nativa agrupada (mantém todas as suas páginas intactas)
pg = st.navigation(
    {
        "Geral": [
            st.Page("paginas/inicio.py", title="Início", icon="🏠", default=True),
        ],
        "Operação": [
            st.Page("paginas/cadastros.py", title="Cadastros", icon="📁"),
            st.Page("paginas/compras.py", title="Compras", icon="🛒"),
            st.Page("paginas/estoque.py", title="Estoque", icon="📦"),
            st.Page("paginas/vendas.py", title="Vendas", icon="💰"),
            st.Page("paginas/operacional.py", title="Perdas", icon="⚠️"),
        ],
        "Gestão": [
            st.Page("paginas/financeiro.py", title="Financeiro", icon="📊"),
        ],
    }
)

pg.run()