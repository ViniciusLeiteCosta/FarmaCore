from datetime import date
import json
import streamlit as st
from core import auth, db

usuario = auth.exigir_login()

st.title("💰 Vendas & Frente de Caixa (PDV)")

if "carrinho_venda" not in st.session_state:
    st.session_state.carrinho_venda = []

aba_pdv, aba_hist = st.tabs(["🛒 Nova Venda", "📋 Histórico & Estorno"])

with aba_pdv:
    produtos = db.consultar(
        """
        SELECT id, nome, codigo_barras, preco_venda, preco_custo, saldo_estoque
          FROM produto
         WHERE ativo = TRUE AND saldo_estoque > 0
         ORDER BY nome
        """
    )
    clientes = db.consultar("SELECT id, nome, cpf FROM cliente WHERE ativo = TRUE ORDER BY nome")

    if not produtos:
        st.warning("Nenhum produto com saldo disponível em estoque. Registre uma compra primeiro.")
    else:
        col_esq, col_dir = st.columns([3, 2], gap="large")

        with col_esq:
            st.subheader("Adicionar Produto")
            prod_opcoes = {
                f"{p['nome']} — R$ {float(p['preco_venda']):.2f} (Disp: {p['saldo_estoque']})": p
                for p in produtos
            }
            p_label = st.selectbox("Produto (com saldo)", list(prod_opcoes.keys()))
            p_sel = prod_opcoes[p_label]

            c_qtd, c_btn = st.columns([1, 2])
            qtd_venda = c_qtd.number_input(
                "Qtd",
                min_value=1,
                max_value=int(p_sel["saldo_estoque"]),
                step=1,
                value=1,
            )
            if c_btn.button("Adicionar ao Carrinho", type="secondary", use_container_width=True):
                existente = next(
                    (i for i in st.session_state.carrinho_venda if i["produto_id"] == p_sel["id"]),
                    None,
                )
                nova_qtd = (existente["quantidade"] if existente else 0) + int(qtd_venda)
                if nova_qtd > int(p_sel["saldo_estoque"]):
                    st.error(f"Saldo insuficiente! Máximo disponível: {p_sel['saldo_estoque']}.")
                else:
                    if existente:
                        existente["quantidade"] = nova_qtd
                        existente["subtotal"] = round(nova_qtd * existente["preco_unitario"], 2)
                    else:
                        st.session_state.carrinho_venda.append(
                            {
                                "produto_id": p_sel["id"],
                                "nome": p_sel["nome"],
                                "quantidade": int(qtd_venda),
                                "preco_unitario": float(p_sel["preco_venda"]),
                                "custo_unitario": float(p_sel["preco_custo"]),
                                "subtotal": round(int(qtd_venda) * float(p_sel["preco_venda"]), 2),
                            }
                        )
                    st.rerun()

            if st.session_state.carrinho_venda:
                st.divider()
                st.subheader("Itens da Venda")
                st.dataframe(
                    [
                        {
                            "Produto": i["nome"],
                            "Qtd": i["quantidade"],
                            "Unit. (R$)": i["preco_unitario"],
                            "Subtotal (R$)": i["subtotal"],
                        }
                        for i in st.session_state.carrinho_venda
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                if st.button("Esvaziar Carrinho"):
                    st.session_state.carrinho_venda = []
                    st.rerun()

        with col_dir:
            st.subheader("Fechamento")
            cli_map = {"Venda de Balcão (Sem cadastro)": None}
            for c in clientes:
                doc = f" ({c['cpf']})" if c["cpf"] else ""
                cli_map[f"{c['nome']}{doc}"] = c["id"]

            cli_sel = st.selectbox("Cliente", list(cli_map.keys()))
            forma_pgto = st.selectbox("Forma de Pagamento", ["PIX", "CARTAO", "DINHEIRO"])

            subtotal_geral = sum(i["subtotal"] for i in st.session_state.carrinho_venda)
            desconto = st.number_input(
                "Desconto (R$)",
                min_value=0.0,
                max_value=float(subtotal_geral),
                step=0.50,
                format="%.2f",
            )
            total_final = round(max(subtotal_geral - desconto, 0.0), 2)

            st.metric("Total a Pagar", f"R$ {total_final:,.2f}")

            if st.button(
                "Finalizar Venda",
                type="primary",
                use_container_width=True,
                disabled=not bool(st.session_state.carrinho_venda),
            ):
                try:
                    with db.transacao() as conn:
                        venda_row = conn.execute(
                            """
                            INSERT INTO venda (cliente_id, usuario_id, desconto, valor_total, forma_pagamento, status)
                            VALUES (%s, %s, %s, %s, %s, 'CONFIRMADA')
                            RETURNING id
                            """,
                            (cli_map[cli_sel], usuario["id"], desconto, total_final, forma_pgto),
                        ).fetchone()
                        venda_id = venda_row["id"]

                        for item in st.session_state.carrinho_venda:
                            conn.execute(
                                """
                                INSERT INTO item_venda (venda_id, produto_id, quantidade, preco_unitario, custo_unitario)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    venda_id,
                                    item["produto_id"],
                                    item["quantidade"],
                                    item["preco_unitario"],
                                    item["custo_unitario"],
                                ),
                            )
                            conn.execute(
                                """
                                INSERT INTO movimentacao_estoque (produto_id, tipo, origem, origem_id, quantidade, usuario_id)
                                VALUES (%s, 'SAIDA', 'VENDA', %s, %s, %s)
                                """,
                                (item["produto_id"], venda_id, item["quantidade"], usuario["id"]),
                            )

                        if total_final > 0:
                            conn.execute(
                                """
                                INSERT INTO lancamento_financeiro
                                    (tipo, descricao, valor, data_vencimento, data_pagamento, status, venda_id, usuario_id)
                                VALUES ('RECEBER', %s, %s, %s, now(), 'PAGO', %s, %s)
                                """,
                                (
                                    f"Venda #{venda_id} ({forma_pgto})",
                                    total_final,
                                    date.today(),
                                    venda_id,
                                    usuario["id"],
                                ),
                            )

                        conn.execute(
                            """
                            INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id, detalhe)
                            VALUES (%s, 'CRIAR', 'venda', %s, %s::jsonb)
                            """,
                            (
                                usuario["id"],
                                venda_id,
                                json.dumps({"valor_total": total_final, "forma_pagamento": forma_pgto}),
                            ),
                        )

                    st.session_state.carrinho_venda = []
                    st.success(f"Venda #{venda_id} registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao finalizar venda: {e}")

with aba_hist:
    vendas = db.consultar(
        """
        SELECT v.id, v.data_venda, COALESCE(c.nome, 'Balcão') AS cliente,
               v.forma_pagamento, v.desconto, v.valor_total, v.status, u.nome AS operador
          FROM venda v
          LEFT JOIN cliente c ON c.id = v.cliente_id
          JOIN usuario u ON u.id = v.usuario_id
         ORDER BY v.id DESC
         LIMIT 50
        """
    )
    st.dataframe(vendas, use_container_width=True, hide_index=True)

    confirmadas = [v for v in vendas if v["status"] == "CONFIRMADA"]
    if confirmadas:
        with st.expander("Estornar Venda"):
            venda_est_id = st.selectbox(
                "Selecione a venda para estornar",
                [v["id"] for v in confirmadas],
                format_func=lambda vid: f"Venda #{vid}",
            )
            if st.button("Confirmar Estorno da Venda", type="secondary"):
                try:
                    with db.transacao() as conn:
                        itens = conn.execute(
                            "SELECT produto_id, quantidade FROM item_venda WHERE venda_id = %s",
                            (venda_est_id,),
                        ).fetchall()
                        for it in itens:
                            conn.execute(
                                """
                                INSERT INTO movimentacao_estoque (produto_id, tipo, origem, origem_id, quantidade, usuario_id)
                                VALUES (%s, 'ENTRADA', 'ESTORNO_VENDA', %s, %s, %s)
                                """,
                                (it["produto_id"], venda_est_id, it["quantidade"], usuario["id"]),
                            )
                        conn.execute(
                            "UPDATE venda SET status = 'CANCELADA', cancelado_em = now() WHERE id = %s",
                            (venda_est_id,),
                        )
                        conn.execute(
                            "UPDATE lancamento_financeiro SET status = 'CANCELADO' WHERE venda_id = %s",
                            (venda_est_id,),
                        )
                        conn.execute(
                            """
                            INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id)
                            VALUES (%s, 'CANCELAR', 'venda', %s)
                            """,
                            (usuario["id"], venda_est_id),
                        )
                    st.success(f"Venda #{venda_est_id} estornada e itens devolvidos ao estoque!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao estornar venda: {e}")