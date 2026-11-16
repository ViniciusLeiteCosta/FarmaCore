import streamlit as st

from core import db

st.title("🏠 Início")

try:
    r = db.consultar_um(
        """
        SELECT
          (SELECT count(*) FROM produto    WHERE ativo) AS produtos,
          (SELECT count(*) FROM fornecedor WHERE ativo) AS fornecedores,
          (SELECT count(*) FROM cliente    WHERE ativo) AS clientes,
          (SELECT count(*) FROM venda      WHERE status = 'CONFIRMADA') AS vendas,
          (SELECT count(*) FROM produto    WHERE ativo AND saldo_estoque <= estoque_minimo) AS abaixo_minimo
        """
    )
    c = st.columns(5)
    c[0].metric("Produtos", r["produtos"])
    c[1].metric("Fornecedores", r["fornecedores"])
    c[2].metric("Clientes", r["clientes"])
    c[3].metric("Vendas", r["vendas"])
    c[4].metric("Abaixo do mínimo", r["abaixo_minimo"])
    st.success("Conexão com o banco OK.")
except Exception as e:  # noqa: BLE001
    st.error(f"Não foi possível consultar o banco: {e}")
