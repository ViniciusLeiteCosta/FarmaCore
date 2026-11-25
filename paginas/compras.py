from datetime import date, timedelta
import json
import streamlit as st
from core.style import aplicar_estilo
from core import auth, db

aplicar_estilo()

usuario = auth.exigir_login()

st.title("🛒 Compras & Entrada de Mercadorias", anchor=False)

if "carrinho_compra" not in st.session_state:
    st.session_state.carrinho_compra = []

aba_nova, aba_hist = st.tabs(["➕ Registrar Compra", "📋 Histórico & Estorno"])

with aba_nova:
    fornecedores = db.consultar("SELECT id, razao_social FROM fornecedor WHERE ativo = TRUE ORDER BY razao_social")
    produtos = db.consultar("SELECT id, nome, preco_custo, saldo_estoque FROM produto WHERE ativo = TRUE ORDER BY nome")

    if not fornecedores or not produtos:
        st.info("Cadastre ao menos um fornecedor e um produto antes de registrar compras.")
    else:
        forn_map = {f["razao_social"]: f["id"] for f in fornecedores}
        prod_map = {f"{p['nome']} (Saldo: {p['saldo_estoque']})": p for p in produtos}

        c1, c2, c3 = st.columns([2, 1, 1])
        forn_sel = c1.selectbox("Fornecedor *", list(forn_map.keys()))
        data_compra = c2.date_input("Data da compra", value=date.today())
        vencimento = c3.date_input("Vencimento boleto", value=date.today() + timedelta(days=30))

        st.divider()
        st.subheader("Itens da Compra")

        ic1, ic2, ic3, ic4 = st.columns([3, 1, 1, 1])
        prod_label = ic1.selectbox("Produto", list(prod_map.keys()))
        prod_obj = prod_map[prod_label]
        qtd = ic2.number_input("Quantidade", min_value=1, step=1, value=1)
        custo = ic3.number_input(
            "Custo unit. (R$)",
            min_value=0.0,
            step=0.10,
            value=float(prod_obj["preco_custo"]),
            format="%.2f",
        )
        if ic4.button("Adicionar Item", use_container_width=True):
            st.session_state.carrinho_compra.append(
                {
                    "produto_id": prod_obj["id"],
                    "nome": prod_obj["nome"],
                    "quantidade": int(qtd),
                    "custo_unitario": float(custo),
                    "subtotal": round(int(qtd) * float(custo), 2),
                }
            )
            st.rerun()

        if st.session_state.carrinho_compra:
            st.dataframe(st.session_state.carrinho_compra, use_container_width=True, hide_index=True)
            total_compra = sum(i["subtotal"] for i in st.session_state.carrinho_compra)
            st.metric("Total da Compra", f"R$ {total_compra:,.2f}")

            b1, b2 = st.columns([1, 3])
            if b1.button("Limpar Itens", use_container_width=True):
                st.session_state.carrinho_compra = []
                st.rerun()

            if b2.button("Confirmar Compra & Dar Entrada no Estoque", type="primary", use_container_width=True):
                try:
                    with db.transacao() as conn:
                        compra_row = conn.execute(
                            """
                            INSERT INTO compra (fornecedor_id, usuario_id, data_compra, valor_total, status)
                            VALUES (%s, %s, %s, %s, 'CONFIRMADA')
                            RETURNING id
                            """,
                            (forn_map[forn_sel], usuario["id"], data_compra, total_compra),
                        ).fetchone()
                        compra_id = compra_row["id"]

                        for item in st.session_state.carrinho_compra:
                            conn.execute(
                                """
                                INSERT INTO item_compra (compra_id, produto_id, quantidade, custo_unitario)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (compra_id, item["produto_id"], item["quantidade"], item["custo_unitario"]),
                            )
                            conn.execute(
                                """
                                INSERT INTO movimentacao_estoque (produto_id, tipo, origem, origem_id, quantidade, usuario_id)
                                VALUES (%s, 'ENTRADA', 'COMPRA', %s, %s, %s)
                                """,
                                (item["produto_id"], compra_id, item["quantidade"], usuario["id"]),
                            )
                            conn.execute(
                                "UPDATE produto SET preco_custo = %s, atualizado_em = now() WHERE id = %s",
                                (item["custo_unitario"], item["produto_id"]),
                            )

                        if total_compra > 0:
                            conn.execute(
                                """
                                INSERT INTO lancamento_financeiro
                                    (tipo, descricao, valor, data_vencimento, status, compra_id, usuario_id)
                                VALUES ('PAGAR', %s, %s, %s, 'PENDENTE', %s, %s)
                                """,
                                (
                                    f"Compra #{compra_id} - {forn_sel}",
                                    total_compra,
                                    vencimento,
                                    compra_id,
                                    usuario["id"],
                                ),
                            )

                        conn.execute(
                            """
                            INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id, detalhe)
                            VALUES (%s, 'CRIAR', 'compra', %s, %s::jsonb)
                            """,
                            (usuario["id"], compra_id, json.dumps({"valor_total": total_compra})),
                        )

                    st.session_state.carrinho_compra = []
                    st.success(f"Compra #{compra_id} confirmada e estoque atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao confirmar compra: {e}")

with aba_hist:
    compras = db.consultar(
        """
        SELECT c.id, f.razao_social AS fornecedor, c.data_compra,
               c.valor_total, c.status, u.nome AS usuario
          FROM compra c
          JOIN fornecedor f ON f.id = c.fornecedor_id
          JOIN usuario u ON u.id = c.usuario_id
         ORDER BY c.id DESC
         LIMIT 50
        """
    )
    st.dataframe(compras, use_container_width=True, hide_index=True)

    confirmadas = [c for c in compras if c["status"] == "CONFIRMADA"]
    if confirmadas:
        with st.expander("Estornar Compra Confirmada"):
            comp_est_id = st.selectbox(
                "Selecione a compra para estornar",
                [c["id"] for c in confirmadas],
                format_func=lambda cid: f"Compra #{cid}",
            )
            if st.button("Confirmar Estorno da Compra", type="secondary"):
                try:
                    with db.transacao() as conn:
                        itens = conn.execute(
                            "SELECT produto_id, quantidade FROM item_compra WHERE compra_id = %s",
                            (comp_est_id,),
                        ).fetchall()
                        for it in itens:
                            conn.execute(
                                """
                                INSERT INTO movimentacao_estoque (produto_id, tipo, origem, origem_id, quantidade, usuario_id)
                                VALUES (%s, 'SAIDA', 'ESTORNO_COMPRA', %s, %s, %s)
                                """,
                                (it["produto_id"], comp_est_id, it["quantidade"], usuario["id"]),
                            )
                        conn.execute(
                            "UPDATE compra SET status = 'CANCELADA', cancelado_em = now() WHERE id = %s",
                            (comp_est_id,),
                        )
                        conn.execute(
                            "UPDATE lancamento_financeiro SET status = 'CANCELADO' WHERE compra_id = %s",
                            (comp_est_id,),
                        )
                        conn.execute(
                            """
                            INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id)
                            VALUES (%s, 'CANCELAR', 'compra', %s)
                            """,
                            (usuario["id"], comp_est_id),
                        )
                    st.success(f"Compra #{comp_est_id} estornada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Não foi possível estornar (verifique se já houve saída do estoque): {e}")