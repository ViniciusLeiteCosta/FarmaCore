"""Login Google (OIDC nativo do Streamlit) + perfis de acesso."""
import json

import streamlit as st

from core import db

PERFIS = ("ADMIN", "FARMACEUTICO", "CAIXA")


def _sincronizar_usuario(email: str, nome: str) -> dict:
    """Cria o usuário no primeiro login e devolve o registro."""
    admins = [e.lower() for e in st.secrets.get("app", {}).get("admin_emails", [])]
    perfil_inicial = "ADMIN" if email.lower() in admins else "CAIXA"
    return db.executar(
        """
        INSERT INTO usuario (email, nome, perfil)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET nome = EXCLUDED.nome
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
    """Bloqueia o app até o usuário entrar. Devolve o usuário do banco."""
    if not st.user.is_logged_in:
        st.title("💊 FarmaCore")
        st.caption("ERP simplificado para farmácia")
        st.button("Entrar com Google", on_click=st.login, type="primary")
        st.stop()

    usuario = _sincronizar_usuario(st.user.email, st.user.get("name", ""))
    if not usuario["ativo"]:
        st.error("Seu usuário está inativo. Fale com o administrador.")
        st.button("Sair", on_click=st.logout)
        st.stop()

    _registrar_login(usuario)
    st.session_state["usuario"] = usuario
    return usuario


def usuario_atual() -> dict:
    return st.session_state["usuario"]


def exigir_perfil(*perfis: str) -> None:
    """Use no topo de uma página restrita: exigir_perfil('ADMIN', 'FARMACEUTICO')."""
    if usuario_atual()["perfil"] not in perfis:
        st.error("Você não tem permissão para acessar esta página.")
        st.stop()
