
import streamlit as st


def aplicar_estilo():

    st.markdown("""
    <style>

    /* =====================================
       IDENTIDADE VISUAL GLOBAL
    ===================================== */

    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --sidebar: #102344;
        --sidebar-light: #1b3763;
        --background: #f3f6fc;
        --surface: #ffffff;
        --text: #172b4d;
        --muted: #64748b;
        --border: #e2e8f0;
    }

    /* Fundo principal */

    .stApp {
        background: var(--background);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* =====================================
       TÍTULOS
    ===================================== */

    h1 {
        color: #14294b !important;
        font-size: 2.2rem !important;
        font-weight: 750 !important;
        letter-spacing: -1px;
    }

    h2 {
        color: #1e3357 !important;
        font-weight: 700 !important;
    }

    h3 {
        color: #243b60 !important;
        font-weight: 650 !important;
    }

    p, label, span {
        color: inherit;
    }

    
/* ==========================================
   MENU LATERAL - COR FIXA
========================================== */

/* Fundo principal do menu */
[data-testid="stSidebar"] {
    background: #102344 !important;
    background-color: #102344 !important;
    border-right: 1px solid #203b63 !important;
}

/* Todos os containers internos */
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
[data-testid="stSidebar"] [data-testid="stSidebarContent"],
[data-testid="stSidebarContent"] {
    background: #102344 !important;
    background-color: #102344 !important;
}

/* Elementos de navegação */
[data-testid="stSidebar"] nav,
[data-testid="stSidebar"] section {
    background: transparent !important;
}

/* Textos */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] a {
    color: #E6EDF8 !important;
}

/* Hover */
[data-testid="stSidebar"] a:hover {
    background-color: #1D3C6B !important;
    color: #FFFFFF !important;
}

/* Ícones */
[data-testid="stSidebar"] svg {
    color: #E6EDF8 !important;
    fill: currentColor;
}


    /* =====================================
       CARDS E MÉTRICAS
    ===================================== */

    [data-testid="stMetric"] {
        background: white;
        padding: 22px;
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: 0 3px 12px rgba(15, 35, 70, 0.05);
        transition: all 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 7px 20px rgba(15, 35, 70, 0.09);
    }

    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #1746a2 !important;
        font-weight: 750;
    }

    /* =====================================
       BOTÕES
    ===================================== */

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 650;
        padding: 0.55rem 1.2rem;
        border: 1px solid #dbe4f0;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: var(--primary);
        color: var(--primary);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: var(--primary);
        color: white;
        border: none;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--primary-dark);
        color: white;
    }

    /* =====================================
       CAMPOS DE FORMULÁRIO
    ===================================== */

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"] {
        border-radius: 10px !important;
    }

    .stTextInput input:focus,
    .stNumberInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12);
    }

    [data-testid="stWidgetLabel"] {
        color: #334967;
        font-weight: 600;
    }

    /* =====================================
       ABAS
    ===================================== */

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 9px 9px 0 0;
        padding: 12px 20px;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }

    /* =====================================
       TABELAS
    ===================================== */

    [data-testid="stDataFrame"] {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 5px;
        box-shadow: 0 3px 12px rgba(15, 35, 70, 0.04);
        overflow: hidden;
    }

    /* =====================================
       EXPANDERS
    ===================================== */

    [data-testid="stExpander"] {
        background: white;
        border: 1px solid var(--border);
        border-radius: 13px;
        box-shadow: 0 2px 8px rgba(15, 35, 70, 0.04);
        margin-bottom: 12px;
    }

    [data-testid="stExpander"] summary {
        font-weight: 650;
    }

    /* =====================================
       FORMULÁRIOS
    ===================================== */

    [data-testid="stForm"] {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px;
    }

    /* =====================================
       ALERTAS
    ===================================== */

    [data-testid="stAlert"] {
        border-radius: 12px;
        border: none;
    }

    /* =====================================
       DIVISORES
    ===================================== */

    hr {
        border-color: #dce4f0 !important;
        margin-top: 22px;
        margin-bottom: 22px;
    }

    /* =====================================
       CHECKBOX
    ===================================== */

    [data-testid="stCheckbox"] {
        padding: 5px 0;
    }

    /* =====================================
       RESPONSIVIDADE
    ===================================== */

    @media (max-width: 768px) {

        .main .block-container {
            padding: 1rem;
        }

        h1 {
            font-size: 1.7rem !important;
        }

        [data-testid="stMetric"] {
            padding: 14px;
        }

    }

    </style>
    """, unsafe_allow_html=True)
