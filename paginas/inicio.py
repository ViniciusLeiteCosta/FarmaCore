import pandas as pd
import streamlit as st
from core import auth, db
from core.style import aplicar_estilo
from core.ui import estado_vazio

aplicar_estilo()
usuario = auth.exigir_login()

st.title("🏠 Início", anchor=False)
st.caption("Visão executiva de faturamento, saúde de estoque e compromissos financeiros")

try:
    res_faturamento = db.executar(
        """
        SELECT
            COALESCE(SUM(valor_total), 0) AS total_mes,
            COALESCE(AVG(valor_total), 0) AS ticket_medio,
            COUNT(*) AS qtd_vendas
        FROM venda
        WHERE status = 'CONFIRMADA'
          AND DATE_TRUNC('month', data_venda) = DATE_TRUNC('month', CURRENT_DATE)
        """
    )[0]
    faturamento_mes = float(res_faturamento["total_mes"])
    ticket_medio = float(res_faturamento["ticket_medio"])
    qtd_vendas = int(res_faturamento["qtd_vendas"])
except Exception:
    faturamento_mes, ticket_medio, qtd_vendas = 0.0, 0.0, 0

try:
    abaixo_minimo = int(
        db.executar(
            "SELECT COUNT(*) AS total FROM produto WHERE ativo = TRUE AND saldo_estoque <= estoque_minimo"
        )[0]["total"]
    )
except Exception:
    abaixo_minimo = 0

try:
    res_contas = db.executar(
        """
        SELECT COALESCE(SUM(valor), 0) AS valor_pendente, COUNT(*) AS qtd_pendente
        FROM lancamento_financeiro
        WHERE tipo = 'PAGAR' AND status = 'PENDENTE'
        """
    )[0]
    contas_pendentes = float(res_contas["valor_pendente"])
    qtd_contas = int(res_contas["qtd_pendente"])
except Exception:
    contas_pendentes, qtd_contas = 0.0, 0


def _brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Faturamento (Mês)", _brl(faturamento_mes), f"{qtd_vendas} venda(s) no mês")
with col2:
    st.metric("Ticket Médio", _brl(ticket_medio), "Média por atendimento")
with col3:
    st.metric(
        "Abaixo do Mínimo",
        f"{abaixo_minimo}",
        "Necessita reposição" if abaixo_minimo > 0 else "Estoque saudável",
        delta_color="inverse" if abaixo_minimo > 0 else "normal",
    )
with col4:
    st.metric(
        "Contas a Pagar",
        _brl(contas_pendentes),
        f"{qtd_contas} título(s) pendente(s)",
        delta_color="inverse" if qtd_contas > 0 else "normal",
    )

st.divider()

col_grafico, col_alertas = st.columns([1.4, 1], gap="large")

with col_grafico:
    st.subheader("📈 Evolução de Vendas", anchor=False)
    try:
        historico_vendas = db.executar(
            """
            SELECT TO_CHAR(data_venda::date, 'DD/MM') AS dia, SUM(valor_total)::float AS faturamento
            FROM venda
            WHERE status = 'CONFIRMADA'
            GROUP BY data_venda::date
            ORDER BY data_venda::date
            LIMIT 15
            """
        )
    except Exception:
        historico_vendas = []

    if historico_vendas:
        df_vendas = pd.DataFrame(historico_vendas).set_index("dia")
        st.area_chart(df_vendas, color=["#0073e6"])
    else:
        estado_vazio(
            "Sem histórico de vendas ainda",
            "Registre vendas no PDV para acompanhar o gráfico de evolução diária.",
            icone="📈",
        )

with col_alertas:
    st.subheader("🚨 Alertas de Reposição", anchor=False)
    try:
        itens_alerta = db.executar(
            """
            SELECT nome, saldo_estoque, estoque_minimo
            FROM produto
            WHERE ativo = TRUE AND saldo_estoque <= estoque_minimo
            ORDER BY (estoque_minimo - saldo_estoque) DESC, nome
            LIMIT 6
            """
        )
    except Exception:
        itens_alerta = []

    if itens_alerta:
        df_alertas = pd.DataFrame(itens_alerta)
        max_ref = max(int(df_alertas["estoque_minimo"].max()), 1)
        st.dataframe(
            df_alertas,
            hide_index=True,
            use_container_width=True,
            column_config={
                "nome": st.column_config.TextColumn("Produto"),
                "saldo_estoque": st.column_config.ProgressColumn(
                    "Saldo Atual",
                    format="%d un",
                    min_value=0,
                    max_value=max_ref,
                ),
                "estoque_minimo": st.column_config.NumberColumn("Mínimo", format="%d un"),
            },
        )
    else:
        estado_vazio(
            "Níveis de estoque regulares",
            "Nenhum medicamento está abaixo ou no limite do estoque mínimo.",
            icone="✅",
        )