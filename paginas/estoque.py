import pandas as pd
import streamlit as st
from core import auth, db
from core.style import aplicar_estilo
from core.ui import estado_vazio

aplicar_estilo()
usuario = auth.exigir_login()

st.title("📦 Controle de Estoque", anchor=False)
st.caption("Posição atual de inventário, valoração a custo, alertas de reposição e trilha de movimentações")

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
    m1.metric("Unidades em Estoque", f"{total_itens:,}".replace(",", "."), f"{len(saldos)} SKU(s) listado(s)")
    m2.metric(
        "Valor em Estoque (Custo)",
        f"R$ {valor_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "Capital imobilizado",
    )
    m3.metric(
        "Produtos em Alerta",
        criticos,
        "Abaixo ou no mínimo" if criticos > 0 else "Níveis regulares",
        delta_color="inverse" if criticos > 0 else "normal",
    )

    st.divider()

    if not saldos:
        estado_vazio(
            "Nenhum produto encontrado para o filtro aplicado",
            "Tente limpar a busca ou desmarcar a opção de alerta crítico.",
            icone="🔎",
        )
    else:
        df_saldos = pd.DataFrame(saldos)
        df_saldos["nivel_pct"] = df_saldos.apply(
            lambda r: min(100, int((r["saldo_estoque"] / max(r["estoque_minimo"] * 2, 1)) * 100)),
            axis=1,
        )

        st.dataframe(
            df_saldos[
                [
                    "id",
                    "produto",
                    "categoria",
                    "ean",
                    "saldo_estoque",
                    "estoque_minimo",
                    "nivel_pct",
                    "preco_custo",
                    "preco_venda",
                    "valor_custo_total",
                    "situacao",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID #", format="%d"),
                "produto": st.column_config.TextColumn("Produto"),
                "categoria": st.column_config.TextColumn("Categoria"),
                "ean": st.column_config.TextColumn("EAN"),
                "saldo_estoque": st.column_config.NumberColumn("Saldo", format="%d un"),
                "estoque_minimo": st.column_config.NumberColumn("Mínimo", format="%d un"),
                "nivel_pct": st.column_config.ProgressColumn(
                    "Nível",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
                "preco_custo": st.column_config.NumberColumn("Custo Unit.", format="R$ %.2f"),
                "preco_venda": st.column_config.NumberColumn("Venda Unit.", format="R$ %.2f"),
                "valor_custo_total": st.column_config.NumberColumn("Total Custo", format="R$ %.2f"),
                "situacao": st.column_config.TextColumn("Situação"),
            },
        )

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

    if not movs:
        estado_vazio(
            "Nenhuma movimentação registrada",
            "As entradas e saídas de compras, vendas e perdas aparecerão aqui.",
            icone="🔄",
        )
    else:
        df_movs = pd.DataFrame(movs)
        df_movs["tipo_fmt"] = df_movs["tipo"].map(
            {"ENTRADA": "⬆️ ENTRADA", "SAIDA": "⬇️ SAÍDA"}
        ).fillna(df_movs["tipo"])

        st.dataframe(
            df_movs[["id", "data_hora", "produto", "tipo_fmt", "origem", "doc_id", "quantidade", "responsavel"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("Mov #", format="%d"),
                "data_hora": st.column_config.DatetimeColumn("Data/Hora", format="DD/MM/YYYY HH:mm"),
                "produto": st.column_config.TextColumn("Produto"),
                "tipo_fmt": st.column_config.TextColumn("Tipo"),
                "origem": st.column_config.TextColumn("Origem"),
                "doc_id": st.column_config.NumberColumn("Doc #", format="%d"),
                "quantidade": st.column_config.NumberColumn("Qtd", format="%d un"),
                "responsavel": st.column_config.TextColumn("Responsável"),
            },
        )