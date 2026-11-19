import json
import streamlit as st
from core import auth, db
from core.style import aplicar_estilo

aplicar_estilo()

usuario = auth.exigir_login()

st.title("📊 Gestão Financeira")

resumo = db.consultar_um(
    """
    SELECT
        COALESCE(SUM(valor) FILTER (WHERE tipo = 'RECEBER' AND status = 'PAGO'), 0) AS recebido,
        COALESCE(SUM(valor) FILTER (WHERE tipo = 'PAGAR'   AND status = 'PAGO'), 0) AS pago,
        COALESCE(SUM(valor) FILTER (WHERE tipo = 'PAGAR'   AND status = 'PENDENTE'), 0) AS a_pagar,
        COALESCE(SUM(valor) FILTER (WHERE tipo = 'DESPESA' AND status = 'LANCADO'), 0) AS perdas
      FROM lancamento_financeiro
    """
)

saldo_caixa = float(resumo["recebido"]) - float(resumo["pago"])

k1, k2, k3, k4 = st.columns(4)
k1.metric("Entradas (Recebido)", f"R$ {float(resumo['recebido']):,.2f}")
k2.metric("Saídas (Pago)", f"R$ {float(resumo['pago']):,.2f}")
k3.metric("Saldo em Caixa", f"R$ {saldo_caixa:,.2f}")
k4.metric("Contas a Pagar (Aberto)", f"R$ {float(resumo['a_pagar']):,.2f}")

st.divider()

c1, c2 = st.columns(2)
filtro_tipo = c1.selectbox("Tipo de lançamento", ["Todos", "RECEBER", "PAGAR", "DESPESA"])
filtro_status = c2.selectbox("Status", ["Todos", "PENDENTE", "PAGO", "LANCADO", "CANCELADO"])

lancamentos = db.consultar(
    """
    SELECT l.id, l.tipo, l.descricao, l.valor,
           l.data_vencimento, l.data_pagamento, l.status, u.nome AS usuario
      FROM lancamento_financeiro l
      JOIN usuario u ON u.id = l.usuario_id
     WHERE (%s = 'Todos' OR l.tipo = %s)
       AND (%s = 'Todos' OR l.status = %s)
     ORDER BY l.data_vencimento DESC, l.id DESC
     LIMIT 100
    """,
    (filtro_tipo, filtro_tipo, filtro_status, filtro_status),
)

st.dataframe(lancamentos, use_container_width=True, hide_index=True)

pendentes = [l for l in lancamentos if l["status"] == "PENDENTE"]
if pendentes:
    with st.expander("💸 Baixar / Pagar Título Pendente"):
        tit_id = st.selectbox(
            "Selecione o lançamento pendente",
            [p["id"] for p in pendentes],
            format_func=lambda lid: next(
                f"#{x['id']} - {x['descricao']} (R$ {float(x['valor']):.2f} | Venc: {x['data_vencimento']})"
                for x in pendentes
                if x["id"] == lid
            ),
        )
        if st.button("Confirmar Pagamento / Liquidação", type="primary"):
            try:
                db.executar(
                    """
                    UPDATE lancamento_financeiro
                       SET status = 'PAGO', data_pagamento = now()
                     WHERE id = %s
                    """,
                    (tit_id,),
                )
                db.executar(
                    """
                    INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id, detalhe)
                    VALUES (%s, 'EDITAR', 'lancamento_financeiro', %s, %s::jsonb)
                    """,
                    (usuario["id"], tit_id, json.dumps({"status": "PAGO"})),
                )
                st.success(f"Lançamento #{tit_id} liquidado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao liquidar título: {e}")