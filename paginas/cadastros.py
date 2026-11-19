import json
import streamlit as st
from core import auth, db

usuario = auth.exigir_login()

st.title("🗂️ Cadastros")

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
                            st.success("Produto cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar produto: {e}")

    busca_prod = st.text_input("Buscar produto por nome ou código de barras", key="busca_prod")
    produtos = db.consultar(
        """
        SELECT p.id, p.nome, c.nome AS categoria, p.codigo_barras,
               p.preco_custo, p.preco_venda, p.estoque_minimo, p.saldo_estoque, p.ativo
          FROM produto p
          JOIN categoria c ON c.id = p.categoria_id
         WHERE (%s = '' OR p.nome ILIKE %s OR COALESCE(p.codigo_barras, '') ILIKE %s)
         ORDER BY p.nome
        """,
        (busca_prod, f"%{busca_prod}%", f"%{busca_prod}%"),
    )
    st.dataframe(produtos, use_container_width=True, hide_index=True)

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
                    st.success("Categoria adicionada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar categoria: {e}")

    cats = db.consultar("SELECT id, nome, ativo, criado_em FROM categoria ORDER BY nome")
    st.dataframe(cats, use_container_width=True, hide_index=True)

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
                        st.success("Fornecedor cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {e}")

    fornecedores = db.consultar(
        "SELECT id, razao_social, cnpj, telefone, email, ativo FROM fornecedor ORDER BY razao_social"
    )
    st.dataframe(fornecedores, use_container_width=True, hide_index=True)

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
                        st.success("Cliente cadastrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar cliente: {e}")

    clientes = db.consultar(
        "SELECT id, nome, cpf, telefone, email, ativo FROM cliente ORDER BY nome"
    )
    st.dataframe(clientes, use_container_width=True, hide_index=True)