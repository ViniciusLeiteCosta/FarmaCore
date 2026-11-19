"""Acesso ao PostgreSQL (Supabase) com pool de conexões."""
from contextlib import contextmanager

import streamlit as st
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


@st.cache_resource(show_spinner=False)
def _pool() -> ConnectionPool:
    return ConnectionPool(
        st.secrets["database"]["url"],
        min_size=0,
        max_size=5,
        timeout=30.0,
        max_idle=300,  # recicla conexões ociosas antes do Supabase derrubar
        kwargs={
            "row_factory": dict_row,
            "prepare_threshold": None,
            "connect_timeout": 15,
        },
        open=True,
    )


def consultar(sql: str, params=None) -> list[dict]:
    """SELECT: devolve lista de dicionários."""
    with _pool().connection() as conn:
        return conn.execute(sql, params).fetchall()


def consultar_um(sql: str, params=None) -> dict | None:
    linhas = consultar(sql, params)
    return linhas[0] if linhas else None


def executar(sql: str, params=None) -> list[dict]:
    """INSERT/UPDATE/DELETE com commit. Se houver RETURNING, devolve as linhas."""
    with _pool().connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall() if cur.description else []


@contextmanager
def transacao():
    """Várias operações atômicas (ex.: compra + itens + estoque + financeiro).

    with transacao() as conn:
        conn.execute(...)
        conn.execute(...)
    Commit ao sair; rollback automático se ocorrer exceção.
    """
    with _pool().connection() as conn:
        yield conn
