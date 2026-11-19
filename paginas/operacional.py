from datetime import date
import json
import streamlit as st
from core.style import aplicar_estilo
from core import auth, db

aplicar_estilo()

usuario = auth.exigir_login()

st.title("⚠️ Controle de Perdas")

produtos = db.consultar(
    "SELECT id, nome, saldo_estoque, preco_custo FROM produto WHERE ativo = TRUE AND saldo_estoque > 0 ORDER BY nome"
)

with st.expander("➕ Registrar Nova Perda", expanded=True):
    if not produtos:
        st.info("Não há produtos com saldo em estoque.")
    else:
        with st.form("form_perda", clear_on_submit=True):
            prod_map = {f"{p['nome']} (Saldo: {p['saldo_estoque']})": p for p in produtos}
            c1, c2, c3 = st.columns([2, 1, 1])
            p_label = c1.selectbox("Produto *", list(prod_map.keys()))
            p_obj = prod_map[p_label]
            qtd = c2.number_input("Quantidade perdida *", min_value=1, max_value=int(p_obj["saldo_estoque"]), step=1)
            motivo = c3.selectbox("Motivo *", ["VENCIMENTO", "AVARIA"])
            obs = st.text_input("Observação (lote, justificativa, etc.)")

            if st.form_submit_button("Registrar Perda & Baixar Estoque", type="primary"):
                try:
                    custo = float(p_obj["preco_custo"])
                    valor_perda = round(int(qtd) * custo, 2)
                    with db.transacao() as conn:
                        perda_row = conn.execute(
                            """
                            INSERT INTO perda (produto_id, usuario_id, quantidade, motivo, custo_unitario, observacao)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            (p_obj["id"], usuario["id"], int(qtd), motivo, custo, obs.strip() or None),
                        ).fetchone()
                        perda_id = perda_row["id"]

                        conn.execute(
                            """
                            INSERT INTO movimentacao_estoque (produto_id, tipo, origem, origem_id, quantidade, usuario_id)
                            VALUES (%s, 'SAIDA', 'PERDA', %s, %s, %s)
                            """,
                            (p_obj["id"], perda_id, int(qtd), usuario["id"]),
                        )

                        if valor_perda > 0:
                            conn.execute(
                                """
                                INSERT INTO lancamento_financeiro
                                    (tipo, descricao, valor, data_vencimento, status, perda_id, usuario_id)
                                VALUES ('DESPESA', %s, %s, %s, 'LANCADO', %s, %s)
                                """,
                                (
                                    f"Perda #{perda_id} ({motivo}) - {p_obj['nome']}",
                                    valor_perda,
                                    date.today(),
                                    perda_id,
                                    usuario["id"],
                                ),
                            )

                        conn.execute(
                            """
                            INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id, detalhe)
                            VALUES (%s, 'CRIAR', 'perda', %s, %s::jsonb)
                            """,
                            (usuario["id"], perda_id, json.dumps({"motivo": motivo, "quantidade": int(qtd)})),
                        )

                    st.success(f"Perda #{perda_id} registrada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar perda: {e}")

perdas = db.consultar(
    """
    SELECT pe.id, pe.data_perda, p.nome AS produto, pe.quantidade,
           pe.motivo, pe.custo_unitario, pe.valor_total,
           COALESCE(pe.observacao, '-') AS observacao, u.nome AS usuario
      FROM perda pe
      JOIN produto p ON p.id = pe.produto_id
      JOIN usuario u ON u.id = pe.usuario_id
     ORDER BY pe.id DESC
     LIMIT 100
    """
)
st.subheader("Histórico de Perdas")
st.dataframe(perdas, use_container_width=True, hide_index=True)