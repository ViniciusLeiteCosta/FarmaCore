import json
import pandas as pd
import streamlit as st
from core import auth, db
from core.style import aplicar_estilo
from core.ui import estado_vazio, notificar

aplicar_estilo()
usuario = auth.exigir_login()

if "toast_cadastros" in st.session_state:
    notificar(st.session_state.pop("toast_cadastros"), tipo="sucesso")

st.title("🗂️ Cadastros", anchor=False)
st.caption("Gestão de catálogo de produtos, categorias, fornecedores e base de clientes")

aba_prod, aba_cat, aba_forn, aba_cli = st.tabs(
    ["💊 Produtos", "🏷️ Categorias", "🚚 Fornecedores", "👤 Clientes"]
)

# ---------------------------------------------------------------------
# ABA 1: PRODUTOS
# ---------------------------------------------------------------------
with aba_prod:
    categorias = db.consultar(
        "SELECT id, nome FROM categoria WHERE ativo = TRUE ORDER BY nome"
    )

    with st.expander("➕ Novo Produto", expanded=not bool(categorias)):
        if not categorias:
            st.warning("Cadastre ao menos uma categoria na aba 'Categorias' antes de criar produtos.")
        else:
            with st.form("form_novo_produto", clear_on_submit=True):
                c1, c2 = st.columns([2, 1])
                nome = c1.text_input("Nome do produto *")
                cat_map = {c["nome"]: c["id"] for c in categorias}
                cat_nome = c2.selectbox("Categoria *", list(cat_map.keys()))

                c3, c4, c5, c6 = st.columns(4)
                ean = c3.text_input("Código de barras (EAN)")
                preco_custo = c4.number_input("Preço de custo (R$)", min_value=0.0, step=0.10, format="%.2f")
                preco_venda = c5.number_input("Preço de venda (R$) *", min_value=0.01, step=0.10, format="%.2f")
                estoque_min = c6.number_input("Estoque mínimo", min_value=0, step=1, value=5)

                if st.form_submit_button("Salvar Produto", type="primary"):
                    if not nome.strip():
                        st.error("Informe o nome do produto.")
                    else:
                        try:
                            novo = db.executar(
                                """
                                INSERT INTO produto (nome, categoria_id, codigo_barras, preco_custo, preco_venda, estoque_minimo)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING id
                                """,
                                (
                                    nome.strip(),
                                    cat_map[cat_nome],
                                    ean.strip() or None,
                                    preco_custo,
                                    preco_venda,
                                    estoque_min,
                                ),
                            )[0]
                            db.executar(
                                """
                                INSERT INTO log_auditoria (usuario_id, acao, tabela, registro_id, detalhe)
                                VALUES (%s, 'CRIAR', 'produto', %s, %s::jsonb)
                                """,
                                (usuario["id"], novo["id"], json.dumps({"nome": nome.strip()})),
                            )
                            st.session_state["toast_cadastros"] = f"Produto '{nome.strip()}' cadastrado com sucesso!"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar produto: {e}")

    busca_prod = st.text_input("Buscar produto por nome ou código de barras", key="busca_prod")
    produtos = db.consultar(
        """
        SELECT p.id, p.nome, c.nome AS categoria, COALESCE(p.codigo_barras, '-') AS codigo_barras,
               p.preco_custo, p.preco_venda, p.estoque_minimo, p.saldo_estoque, p.ativo
          FROM produto p
          JOIN categoria c ON c.id = p.categoria_id
         WHERE (%s = '' OR p.nome ILIKE %s OR COALESCE(p.codigo_barras, '') ILIKE %s)
         ORDER BY p.nome
        """,
        (busca_prod, f"%{busca_prod}%", f"%{busca_prod}%"),
    )

    if not produtos:
        estado_vazio(
            "Nenhum produto encontrado",
            "Cadastre um novo item acima ou limpe o campo de busca.",
            icone="💊",
        )
    else:
        df_prod = pd.DataFrame(produtos)
        df_prod["status_fmt"] = df_prod["ativo"].map({True: "🟢 Ativo", False: "🔴 Inativo"})
        st.dataframe(
            df_prod[["id", "nome", "categoria", "codigo_barras", "preco_custo", "preco_venda", "estoque_minimo", "saldo_estoque", "status_fmt"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID #", format="%d"),
                "nome": st.column_config.TextColumn("Produto"),
                "categoria": st.column_config.TextColumn("Categoria"),
                "codigo_barras": st.column_config.TextColumn("EAN"),
                "preco_custo": st.column_config.NumberColumn("Custo", format="R$ %.2f"),
                "preco_venda": st.column_config.NumberColumn("Venda", format="R$ %.2f"),
                "estoque_minimo": st.column_config.NumberColumn("Mínimo", format="%d un"),
                "saldo_estoque": st.column_config.NumberColumn("Saldo", format="%d un"),
                "status_fmt": st.column_config.TextColumn("Status"),
            },
        )

# ---------------------------------------------------------------------
# ABA 2: CATEGORIAS
# ---------------------------------------------------------------------
with aba_cat:
    with st.form("form_nova_categoria", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        nome_cat = col1.text_input("Nome da categoria (ex.: Genéricos, Referência, Perfumaria)")
        if col2.form_submit_button("Adicionar", type="primary", use_container_width=True):
            if nome_cat.strip():
                try:
                    db.executar("INSERT INTO categoria (nome) VALUES (%s)", (nome_cat.strip(),))
                    st.session_state["toast_cadastros"] = f"Categoria '{nome_cat.strip()}' adicionada!"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar categoria: {e}")

    cats = db.consultar("SELECT id, nome, ativo, criado_em FROM categoria ORDER BY nome")
    if not cats:
        estado_vazio("Nenhuma categoria cadastrada", "Adicione a primeira categoria no formulário acima.", icone="🏷️")
    else:
        df_cats = pd.DataFrame(cats)
        df_cats["status_fmt"] = df_cats["ativo"].map({True: "🟢 Ativa", False: "🔴 Inativa"})
        st.dataframe(
            df_cats[["id", "nome", "status_fmt", "criado_em"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID #", format="%d"),
                "nome": st.column_config.TextColumn("Categoria"),
                "status_fmt": st.column_config.TextColumn("Status"),
                "criado_em": st.column_config.DatetimeColumn("Criada em", format="DD/MM/YYYY HH:mm"),
            },
        )

# ---------------------------------------------------------------------
# ABA 3: FORNECEDORES
# ---------------------------------------------------------------------
with aba_forn:
    with st.expander("➕ Novo Fornecedor"):
        with st.form("form_novo_fornecedor", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            razao = c1.text_input("Razão Social *")
            cnpj = c2.text_input("CNPJ *")
            c3, c4 = st.columns(2)
            tel_f = c3.text_input("Telefone")
            email_f = c4.text_input("E-mail")

            if st.form_submit_button("Salvar Fornecedor", type="primary"):
                if not razao.strip() or not cnpj.strip():
                    st.error("Razão social e CNPJ são obrigatórios.")
                else:
                    try:
                        db.executar(
                            """
                            INSERT INTO fornecedor (razao_social, cnpj, telefone, email)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (razao.strip(), cnpj.strip(), tel_f.strip() or None, email_f.strip() or None),
                        )
                        st.session_state["toast_cadastros"] = f"Fornecedor '{razao.strip()}' cadastrado!"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {e}")

    fornecedores = db.consultar(
        "SELECT id, razao_social, cnpj, COALESCE(telefone, '-') AS telefone, COALESCE(email, '-') AS email, ativo FROM fornecedor ORDER BY razao_social"
    )
    if not fornecedores:
        estado_vazio("Nenhum fornecedor cadastrado", "Clique em '+ Novo Fornecedor' para registrar o primeiro parceiro.", icone="🚚")
    else:
        df_forn = pd.DataFrame(fornecedores)
        df_forn["status_fmt"] = df_forn["ativo"].map({True: "🟢 Ativo", False: "🔴 Inativo"})
        st.dataframe(
            df_forn[["id", "razao_social", "cnpj", "telefone", "email", "status_fmt"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID #", format="%d"),
                "razao_social": st.column_config.TextColumn("Razão Social"),
                "cnpj": st.column_config.TextColumn("CNPJ"),
                "telefone": st.column_config.TextColumn("Telefone"),
                "email": st.column_config.TextColumn("E-mail"),
                "status_fmt": st.column_config.TextColumn("Status"),
            },
        )

# ---------------------------------------------------------------------
# ABA 4: CLIENTES
# ---------------------------------------------------------------------
with aba_cli:
    with st.expander("➕ Novo Cliente"):
        with st.form("form_novo_cliente", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            nome_cli = c1.text_input("Nome completo *")
            cpf_cli = c2.text_input("CPF")
            c3, c4 = st.columns(2)
            tel_cli = c3.text_input("Telefone")
            email_cli = c4.text_input("E-mail")

            if st.form_submit_button("Salvar Cliente", type="primary"):
                if not nome_cli.strip():
                    st.error("Informe o nome do cliente.")
                else:
                    try:
                        db.executar(
                            """
                            INSERT INTO cliente (nome, cpf, telefone, email)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                nome_cli.strip(),
                                cpf_cli.strip() or None,
                                tel_cli.strip() or None,
                                email_cli.strip() or None,
                            ),
                        )
                        st.session_state["toast_cadastros"] = f"Cliente '{nome_cli.strip()}' cadastrado!"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {e}")

    clientes = db.consultar(
        "SELECT id, nome, COALESCE(cpf, '-') AS cpf, COALESCE(telefone, '-') AS telefone, COALESCE(email, '-') AS email, ativo FROM cliente ORDER BY nome"
    )
    if not clientes:
        estado_vazio("Nenhum cliente cadastrado", "Clique em '+ Novo Cliente' para iniciar sua base.", icone="👤")
    else:
        df_cli = pd.DataFrame(clientes)
        df_cli["status_fmt"] = df_cli["ativo"].map({True: "🟢 Ativo", False: "🔴 Inativo"})
        st.dataframe(
            df_cli[["id", "nome", "cpf", "telefone", "email", "status_fmt"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID #", format="%d"),
                "nome": st.column_config.TextColumn("Nome"),
                "cpf": st.column_config.TextColumn("CPF"),
                "telefone": st.column_config.TextColumn("Telefone"),
                "email": st.column_config.TextColumn("E-mail"),
                "status_fmt": st.column_config.TextColumn("Status"),
            },
        )