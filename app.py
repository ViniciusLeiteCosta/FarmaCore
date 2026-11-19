"""FarmaCore - ponto de entrada. Execute: streamlit run app.py"""
import streamlit as st

from core import auth

st.set_page_config(page_title="FarmaCore", page_icon="💊", layout="wide")

usuario = auth.exigir_login()

paginas = {
    "Geral": [
        st.Page("paginas/inicio.py", title="Início", icon="🏠", default=True),
    ],
    "Operação": [
        st.Page("paginas/cadastros.py", title="Cadastros", icon="🗂️"),
        st.Page("paginas/compras.py", title="Compras", icon="🛒"),
        st.Page("paginas/estoque.py", title="Estoque", icon="📦"),
        st.Page("paginas/vendas.py", title="Vendas", icon="💰"),
        st.Page("paginas/operacional.py", title="Perdas", icon="⚠️"),
    ],
    "Gestão": [
        st.Page("paginas/financeiro.py", title="Financeiro", icon="📊"),
    ],
}

with st.sidebar:
    st.markdown(f"**{usuario['nome']}**")
    st.caption(f"{usuario['email']} · {usuario['perfil']}")
    #st.button("Sair", on_click=st.logout, use_container_width=True)
    if st.user.is_logged_in:
        st.button("Sair", on_click=st.logout, use_container_width=True)
st.navigation(paginas).run()
