import base64
import html
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


def chrome_corporativo():
    st.markdown(
        """
        <style>
            /* Esconde apenas menus e rodapé padrão, sem bloquear o botão de expandir a sidebar */
            #MainMenu,
            footer,
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"],
            [data-testid="stHeaderActionElements"],
            .stAppDeployButton {
                display: none !important;
            }

            /* Mantém o header e a toolbar visíveis porém transparentes para preservar o controle da sidebar */
            header[data-testid="stHeader"],
            [data-testid="stToolbar"] {
                visibility: visible !important;
                display: flex !important;
                background: transparent !important;
                border-bottom: none !important;
            }

            /* Destaca o botão de expandir a barra lateral quando ela estiver fechada */
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="stExpandSidebarButton"] {
                visibility: visible !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background-color: #0f213a !important;
                color: #f8fafc !important;
                border-radius: 10px !important;
                border: 1px solid rgba(255, 255, 255, 0.16) !important;
                box-shadow: 0 4px 12px rgba(15, 33, 58, 0.25) !important;
                margin: 8px 0 0 8px !important;
                z-index: 99999 !important;
            }
            [data-testid="stSidebarCollapsedControl"] svg,
            [data-testid="stExpandSidebarButton"] svg,
            [data-testid="stSidebarCollapsedControl"] span,
            [data-testid="stExpandSidebarButton"] span {
                fill: #f8fafc !important;
                color: #f8fafc !important;
            }

            /* Estiliza o selectbox dentro da barra lateral escura */
            [data-testid="stSidebar"] [data-baseweb="select"] > div {
                background-color: rgba(255, 255, 255, 0.06) !important;
                border: 1px solid rgba(255, 255, 255, 0.14) !important;
                border-radius: 10px !important;
                color: #f8fafc !important;
            }
            [data-testid="stSidebar"] [data-baseweb="select"] span,
            [data-testid="stSidebar"] [data-baseweb="select"] svg {
                color: #f8fafc !important;
                fill: #f8fafc !important;
            }

            /* Estiliza o botão Sair da barra lateral para combinar com o tema */
            [data-testid="stSidebar"] .stButton > button {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: #f8fafc !important;
                border: 1px solid rgba(255, 255, 255, 0.14) !important;
                border-radius: 10px !important;
                font-weight: 500 !important;
                transition: all 0.18s ease !important;
            }
            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: rgba(239, 68, 68, 0.18) !important;
                border-color: rgba(248, 113, 113, 0.45) !important;
                color: #fca5a5 !important;
            }

            [data-testid="stApp"]::before {
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                height: 3px;
                width: 0%;
                background: linear-gradient(90deg, #0073e6 0%, #00d4ff 50%, #0073e6 100%);
                background-size: 200% 100%;
                box-shadow: 0 0 8px rgba(0, 212, 255, 0.75);
                z-index: 999999;
                pointer-events: none;
                opacity: 0;
                transition: width 0.25s ease-out, opacity 0.3s ease;
            }

            [data-testid="stApp"][data-test-script-state="running"]::before {
                opacity: 1;
                animation: farmLoadingProgress 1.6s cubic-bezier(0.22, 1, 0.36, 1) forwards,
                           farmLoadingShimmer 1.1s linear infinite;
            }

            [data-testid="stMainBlockContainer"] {
                transition: opacity 0.18s ease-in-out;
            }

            [data-testid="stMetric"] {
                transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
            }
            [data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                border-color: rgba(0, 115, 230, 0.45);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
            }

            @keyframes farmLoadingProgress {
                0%   { width: 8%; }
                40%  { width: 58%; }
                80%  { width: 84%; }
                100% { width: 93%; }
            }

            @keyframes farmLoadingShimmer {
                0%   { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            .fc-user-card {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                padding: 12px 14px;
                margin: 8px 0 12px 0;
            }
            .fc-user-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                margin-bottom: 4px;
            }
            .fc-user-name {
                font-size: 0.92rem;
                font-weight: 600;
                color: #f8fafc;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .fc-user-email {
                font-size: 0.76rem;
                color: rgba(248, 250, 252, 0.68);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .fc-badge {
                font-size: 0.66rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                padding: 2px 7px;
                border-radius: 999px;
                text-transform: uppercase;
                flex-shrink: 0;
            }
            .fc-badge-admin {
                background: rgba(0, 212, 255, 0.18);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.35);
            }
            .fc-badge-farmaceutico {
                background: rgba(16, 185, 129, 0.18);
                color: #34d399;
                border: 1px solid rgba(52, 211, 153, 0.35);
            }
            .fc-badge-caixa {
                background: rgba(245, 158, 11, 0.18);
                color: #fbbf24;
                border: 1px solid rgba(251, 191, 36, 0.35);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_cartao_usuario(usuario: dict):
    nome = html.escape(usuario.get("nome") or "Usuário")
    email = html.escape(usuario.get("email") or "")
    perfil = (usuario.get("perfil") or "CAIXA").upper()

    classe_badge = {
        "ADMIN": "fc-badge-admin",
        "FARMACEUTICO": "fc-badge-farmaceutico",
    }.get(perfil, "fc-badge-caixa")

    st.markdown(
        f"""
        <div class="fc-user-card">
            <div class="fc-user-header">
                <span class="fc-user-name" title="{nome}">{nome}</span>
                <span class="fc-badge {classe_badge}">{html.escape(perfil)}</span>
            </div>
            <div class="fc-user-email" title="{email}">{email}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="FarmaCore ERP",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_estilo()
chrome_corporativo()
usuario = auth.exigir_login()

logo_topo_sidebar("logo.png")

with st.sidebar:
    render_cartao_usuario(usuario)

    # Se o usuário logado no Google for ADMIN real, permite alternar a visão na apresentação
    if usuario.get("perfil_real") == "ADMIN":
        rotulos = {
            "ADMIN": "👑 Administrador (Total)",
            "FARMACEUTICO": "💊 Farmacêutico",
            "CAIXA": "🧾 Operador de Caixa",
        }
        atual = st.session_state.get("perfil_simulado", "ADMIN")
        escolhido = st.selectbox(
            "Simular visão de acesso",
            options=list(rotulos.keys()),
            index=list(rotulos.keys()).index(atual),
            format_func=lambda k: rotulos[k],
            help="Permite testar as restrições de tela e menu de cada cargo em tempo real.",
        )
        if escolhido != atual:
            st.session_state["perfil_simulado"] = escolhido
            st.rerun()

    st.button("Sair", on_click=st.logout, use_container_width=True)

perfil_ativo = usuario["perfil"]

paginas_operacao = [
    st.Page("paginas/cadastros.py", title="Cadastros", icon="📁"),
    st.Page("paginas/estoque.py", title="Estoque", icon="📦"),
    st.Page("paginas/vendas.py", title="Vendas", icon="💰"),
]

if perfil_ativo in ("ADMIN", "FARMACEUTICO"):
    paginas_operacao.insert(1, st.Page("paginas/compras.py", title="Compras", icon="🛒"))
    paginas_operacao.append(st.Page("paginas/operacional.py", title="Perdas", icon="⚠️"))

menu = {
    "Geral": [
        st.Page("paginas/inicio.py", title="Início", icon="🏠", default=True),
    ],
    "Operação": paginas_operacao,
}

if perfil_ativo == "ADMIN":
    menu["Gestão"] = [
        st.Page("paginas/financeiro.py", title="Financeiro & Auditoria", icon="📊"),
    ]

pg = st.navigation(menu)
pg.run()