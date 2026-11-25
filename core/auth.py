"""Login Google (OIDC nativo do Streamlit) + perfis de acesso e simulação de visão."""
import base64
import json
import os

import streamlit as st

from core import db
from core.ui import estado_vazio

PERFIS = ("ADMIN", "FARMACEUTICO", "CAIXA")

def _render_tela_login() -> None:
    """Renderiza uma tela de autenticação corporativa SaaS com Google OAuth unificado."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"],
            [data-testid="stSidebarCollapsedControl"],
            header[data-testid="stHeader"] {
                display: none !important;
            }

            /* Fundo corporativo profundo com brilho radial sutil */
            [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at 20% 20%, rgba(0, 115, 230, 0.18) 0%, transparent 45%),
                    radial-gradient(circle at 80% 80%, rgba(0, 212, 255, 0.12) 0%, transparent 45%),
                    linear-gradient(135deg, #070f1d 0%, #0d1b33 50%, #091324 100%) !important;
            }

            [data-testid="stMainBlockContainer"] {
                max-width: 460px !important;
                padding-top: 6vh !important;
                padding-bottom: 4vh !important;
            }

            /* Cartão principal unificado */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(15, 29, 54, 0.82) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border: 1px solid rgba(148, 163, 184, 0.18) !important;
                border-radius: 20px !important;
                padding: 36px 32px 28px 32px !important;
                box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45),
                            inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
            }

            .fc-login-header {
                text-align: center;
                margin-bottom: 24px;
            }
            .fc-login-pill {
                display: inline-block;
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #38bdf8;
                background: rgba(56, 189, 248, 0.12);
                border: 1px solid rgba(56, 189, 248, 0.28);
                padding: 4px 12px;
                border-radius: 999px;
                margin-bottom: 16px;
            }
            .fc-login-title {
                color: #f8fafc;
                font-size: 1.55rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                margin: 12px 0 8px 0;
            }
            .fc-login-sub {
                color: #94a3b8;
                font-size: 0.92rem;
                line-height: 1.5;
                margin: 0;
            }

            /* Botão estilo oficial Sign in with Google dentro do cartão */
            div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
                background-color: #ffffff !important;
                color: #1e293b !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 12px !important;
                height: 48px !important;
                font-size: 0.96rem !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18) !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {
                background-color: #f8fafc !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 8px 20px rgba(0, 212, 255, 0.22) !important;
                border-color: #38bdf8 !important;
            }

            /* Ícone G oficial do Google antes do texto do botão */
            div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button p::before {
                content: "";
                display: inline-block;
                width: 18px;
                height: 18px;
                margin-right: 10px;
                vertical-align: -3px;
                background-size: contain;
                background-repeat: no-repeat;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath fill='%23EA4335' d='M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z'/%3E%3Cpath fill='%234285F4' d='M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z'/%3E%3Cpath fill='%23FBBC05' d='M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z'/%3E%3Cpath fill='%2334A853' d='M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z'/%3E%3C/svg%3E");
            }

            .fc-login-divider {
                height: 1px;
                background: rgba(148, 163, 184, 0.16);
                margin: 24px 0 18px 0;
            }
            .fc-login-features {
                display: flex;
                justify-content: space-between;
                gap: 8px;
                font-size: 0.75rem;
                color: #94a3b8;
                text-align: center;
            }
            .fc-login-features span {
                flex: 1;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 8px;
                padding: 7px 6px;
            }
            .fc-login-footer {
                text-align: center;
                color: #64748b;
                font-size: 0.76rem;
                margin-top: 18px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    logo_html = '<div style="font-size: 3rem;">💊</div>'
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        logo_html = (
            f'<img src="data:image/png;base64,{img_b64}" '
            f'style="max-height: 76px; margin: 4px auto 6px auto; display: block;" alt="FarmaCore">'
        )

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="fc-login-header">
                {logo_html}
                <div class="fc-login-title">Bem-vindo ao FarmaCore</div>
                <p class="fc-login-sub">
                    Sistema Integrado de Gestão Farmacêutica.<br>
                    Autentique-se com sua conta Google institucional.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.button(
            "Continuar com o Google",
            on_click=st.login,
            use_container_width=True,
        )

        st.markdown(
            """
            <div class="fc-login-divider"></div>
            <div class="fc-login-features">
                <span>🔒 OAuth 2.0</span>
                <span>🛡️ Perfis RBAC</span>
                <span>📋 Auditoria</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="fc-login-footer">FarmaCore ERP · Acesso monitorado</div>',
        unsafe_allow_html=True,
    )

def _sincronizar_usuario(email: str, nome: str) -> dict:
    """Cria ou atualiza o usuário no login Google e garante promoção se estiver em admin_emails."""
    admins = [e.lower() for e in st.secrets.get("app", {}).get("admin_emails", [])]
    eh_admin_config = email.lower() in admins
    perfil_inicial = "ADMIN" if eh_admin_config else "CAIXA"

    if eh_admin_config:
        return db.executar(
            """
            INSERT INTO usuario (email, nome, perfil)
            VALUES (%s, %s, 'ADMIN')
            ON CONFLICT (email) DO UPDATE
               SET nome = EXCLUDED.nome,
                   perfil = 'ADMIN'
            RETURNING id, email, nome, perfil, ativo
            """,
            (email.lower(), nome or email),
        )[0]

    return db.executar(
        """
        INSERT INTO usuario (email, nome, perfil)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE
           SET nome = EXCLUDED.nome
        RETURNING id, email, nome, perfil, ativo
        """,
        (email.lower(), nome or email, perfil_inicial),
    )[0]


def _registrar_login(usuario: dict) -> None:
    if st.session_state.get("login_registrado"):
        return
    db.executar(
        "INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id, detalhe) "
        "VALUES (%s, 'LOGIN', 'usuario', %s, %s::jsonb)",
        (usuario["id"], usuario["id"], json.dumps({"email": usuario["email"]})),
    )
    st.session_state["login_registrado"] = True


def exigir_login() -> dict:
    """Bloqueia o app até o usuário autenticar via Google OAuth. Devolve o usuário com o perfil ativo."""
    logado_google = getattr(st.user, "is_logged_in", False)

    if not logado_google:
        _render_tela_login()
        st.stop()

    usuario = _sincronizar_usuario(st.user.email, st.user.get("name", ""))
    if not usuario["ativo"]:
        st.error("Seu usuário está inativo. Fale com o administrador.")
        st.button("Sair", on_click=st.logout)
        st.stop()

    _registrar_login(usuario)

    # Guarda o perfil real do banco e aplica a simulação de visão se o ADMIN ativou na sidebar
    usuario["perfil_real"] = usuario["perfil"]
    if usuario["perfil_real"] == "ADMIN":
        visao = st.session_state.get("perfil_simulado", "ADMIN")
        if visao in PERFIS:
            usuario["perfil"] = visao

    st.session_state["usuario"] = usuario
    return usuario


def usuario_atual() -> dict:
    return st.session_state["usuario"]


def exigir_perfil(*perfis: str) -> dict:
    """Use no topo de uma página restrita: usuario = auth.exigir_perfil('ADMIN', 'FARMACEUTICO')."""
    u = usuario_atual()
    if u["perfil"] not in perfis:
        st.title("🔒 Acesso Restrito", anchor=False)
        estado_vazio(
            "Permissão insuficiente para este módulo",
            f"O perfil ativo ({u['perfil']}) não possui autorização para acessar esta área. "
            f"Perfis permitidos: {', '.join(perfis)}.",
            icone="🛡️",
        )
        st.stop()
    return u