import streamlit as st
from core import auth, db
from core.style import aplicar_estilo

aplicar_estilo()

usuario = auth.exigir_login()

st.title("📦 Controle de Estoque", anchor=False)

aba_saldo, aba_mov = st.tabs(["📊 Posição Atual", "🔄 Histórico de Movimentações"])

with aba_saldo:
    c1, c2, c3 = st.columns([2, 1, 1])
    busca = c1.text_input("Buscar produto ou código de barras")
    categorias = db.consultar("SELECT id, nome FROM categoria WHERE ativo = TRUE ORDER BY nome")
    cat_opcoes = ["Todas"] + [c["nome"] for c in categorias]
    cat_sel = c2.selectbox("Categoria", cat_opcoes)
    apenas_critico = c3.checkbox("Apenas abaixo do mínimo", value=False)

    saldos = db.consultar(
        """
        SELECT p.id, p.nome AS produto, c.nome AS categoria,
               COALESCE(p.codigo_barras, '-') AS ean,
               p.saldo_estoque, p.estoque_minimo,
               p.preco_custo, p.preco_venda,
               ROUND(p.saldo_estoque * p.preco_custo, 2) AS valor_custo_total,
               CASE
                   WHEN p.saldo_estoque = 0 THEN '🔴 Zerado'
                   WHEN p.saldo_estoque <= p.estoque_minimo THEN '🟡 Baixo'
                   ELSE '🟢 Normal'
               END AS situacao
          FROM produto p
          JOIN categoria c ON c.id = p.categoria_id
         WHERE p.ativo = TRUE
           AND (%s = '' OR p.nome ILIKE %s OR COALESCE(p.codigo_barras, '') ILIKE %s)
           AND (%s = 'Todas' OR c.nome = %s)
           AND (NOT %s OR p.saldo_estoque <= p.estoque_minimo)
         ORDER BY (p.saldo_estoque <= p.estoque_minimo) DESC, p.nome
        """,
        (busca, f"%{busca}%", f"%{busca}%", cat_sel, cat_sel, apenas_critico),
    )

    total_itens = sum(r["saldo_estoque"] for r in saldos)
    valor_estoque = sum(float(r["valor_custo_total"]) for r in saldos)
    criticos = sum(1 for r in saldos if r["saldo_estoque"] <= r["estoque_minimo"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Unidades em Estoque", total_itens)
    m2.metric("Valor em Estoque (Custo)", f"R$ {valor_estoque:,.2f}")
    m3.metric("Produtos em Alerta", criticos)

    st.dataframe(saldos, use_container_width=True, hide_index=True)

with aba_mov:
    f1, f2 = st.columns([2, 1])
    filtro_prod = f1.text_input("Filtrar movimentação por produto")
    filtro_origem = f2.selectbox(
        "Origem",
        ["Todas", "COMPRA", "VENDA", "PERDA", "ESTORNO_COMPRA", "ESTORNO_VENDA"],
    )

    movs = db.consultar(
        """
        SELECT m.id, m.criado_em AS data_hora, p.nome AS produto,
               m.tipo, m.origem, m.origem_id AS doc_id,
               m.quantidade, u.nome AS responsavel
          FROM movimentacao_estoque m
          JOIN produto p ON p.id = m.produto_id
          JOIN usuario u ON u.id = m.usuario_id
         WHERE (%s = '' OR p.nome ILIKE %s)
           AND (%s = 'Todas' OR m.origem = %s)
         ORDER BY m.id DESC
         LIMIT 100
        """,
        (filtro_prod, f"%{filtro_prod}%", filtro_origem, filtro_origem),
    )
    st.dataframe(movs, use_container_width=True, hide_index=True)