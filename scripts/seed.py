import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import db


def popular_banco():
    print("1. Limpando registros operacionais antigos...")
    db.executar(
        """
        TRUNCATE TABLE
            log_auditoria,
            movimentacao_estoque,
            lancamento_financeiro,
            item_venda,
            venda,
            item_compra,
            compra,
            perda,
            produto,
            categoria,
            fornecedor,
            cliente
        RESTART IDENTITY CASCADE;
        """
    )

    usuario = db.executar("SELECT id FROM usuario LIMIT 1")
    usuario_id = usuario[0]["id"] if usuario else None

    print("2. Inserindo fornecedores...")
    fornecedores = [
        ("Distribuidora Farmacêutica Santa Cruz Ltda", "61.940.292/0001-03", "(11) 3100-4400", "pedidos@santacruzfarma.com.br"),
        ("Profarma Distribuidora de Produtos Farmacêuticos S.A.", "45.453.214/0001-51", "(21) 4009-3500", "comercial@profarma.com.br"),
        ("Panpharma Distribuidora de Medicamentos Ltda", "01.206.820/0001-04", "(11) 2133-8000", "vendas@panpharma.com.br"),
        ("Medley Indústria Farmacêutica Ltda", "50.929.710/0001-79", "(19) 2117-8222", "contato@medley.com.br"),
        ("EMS Sigma Pharma Ltda", "00.923.140/0001-31", "(19) 3887-9800", "atendimento@ems.com.br"),
    ]
    forn_ids = []
    for razao, cnpj, tel, email in fornecedores:
        res = db.executar(
            """
            INSERT INTO fornecedor (razao_social, cnpj, telefone, email, ativo)
            VALUES (%s, %s, %s, %s, TRUE) RETURNING id
            """,
            (razao, cnpj, tel, email),
        )
        forn_ids.append(res[0]["id"])

    print("3. Inserindo categorias...")
    categorias = [
        "Analgésicos e Antitérmicos",
        "Antibióticos",
        "Anti-inflamatórios",
        "Dermocosméticos",
        "Vitaminas e Suplementos",
        "Gripe e Resfriado",
    ]
    cat_map = {}
    for nome in categorias:
        res = db.executar(
            "INSERT INTO categoria (nome, ativo) VALUES (%s, TRUE) RETURNING id",
            (nome,),
        )
        cat_map[nome] = res[0]["id"]

    print("4. Inserindo produtos e medicamentos...")
    produtos = [
        ("Dipirona Sódica 500mg 20 comp", "Analgésicos e Antitérmicos", "7891058001018", 4.50, 12.90, 20, 45),
        ("Paracetamol 750mg 20 comp", "Analgésicos e Antitérmicos", "7896004701025", 5.20, 14.50, 15, 32),
        ("Ibuprofeno 600mg 20 comp", "Anti-inflamatórios", "7896181901031", 7.80, 19.90, 15, 28),
        ("Nimesulida 100mg 12 comp", "Anti-inflamatórios", "7896422501048", 6.10, 16.50, 12, 8),
        ("Amoxicilina 500mg 21 caps", "Antibióticos", "7896004705054", 14.90, 34.90, 10, 18),
        ("Azitromicina 500mg 5 comp", "Antibióticos", "7891058009069", 12.40, 29.90, 10, 4),
        ("Cefalexina 500mg 10 comp", "Antibióticos", "7896181902076", 11.20, 26.80, 10, 14),
        ("Protetor Solar Facial FPS 60 50g", "Dermocosméticos", "7899706101083", 36.00, 74.90, 10, 6),
        ("Hidratante Corporal Pele Seca 200ml", "Dermocosméticos", "7899706102097", 24.50, 52.00, 8, 15),
        ("Vitamina C 1g Efervescente 10 comp", "Vitaminas e Suplementos", "7891106901102", 8.90, 21.90, 15, 40),
        ("Complexo B 30 drágeas", "Vitaminas e Suplementos", "7896004709111", 9.50, 23.50, 12, 25),
        ("Vitamina D3 2000UI 30 caps", "Vitaminas e Suplementos", "7891058012120", 13.80, 32.90, 10, 19),
        ("Loratadina 10mg 12 comp", "Gripe e Resfriado", "7896422508139", 5.40, 15.90, 15, 30),
        ("Xarope Expectorante Adulto 120ml", "Gripe e Resfriado", "7896181914147", 11.00, 27.50, 10, 16),
        ("Descongestionante Nasal Spray 30ml", "Gripe e Resfriado", "7891058015152", 7.20, 18.90, 12, 22),
    ]
    prod_ids = []
    for nome, cat, ean, custo, venda, minimo, saldo in produtos:
        res = db.executar(
            """
            INSERT INTO produto (nome, categoria_id, codigo_barras, preco_custo, preco_venda, estoque_minimo, saldo_estoque, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE) RETURNING id
            """,
            (nome, cat_map[cat], ean, custo, venda, minimo, saldo),
        )
        prod_ids.append((res[0]["id"], nome, custo, venda))

    print("5. Inserindo clientes...")
    clientes = [
        ("Maria Fernanda Oliveira", "123.456.789-01", "(11) 98765-4321", "maria.oliveira@email.com"),
        ("Carlos Eduardo Santos", "234.567.890-12", "(11) 97654-3210", "carlos.santos@email.com"),
        ("Ana Paula Costa", "345.678.901-23", "(11) 96543-2109", "ana.costa@email.com"),
        ("Roberto Almeida Lima", "456.789.012-34", "(11) 95432-1098", "roberto.lima@email.com"),
        ("Juliana Mendes Rocha", "567.890.123-45", "(11) 94321-0987", "juliana.rocha@email.com"),
    ]
    cli_ids = []
    for nome, cpf, tel, email in clientes:
        res = db.executar(
            "INSERT INTO cliente (nome, cpf, telefone, email, ativo) VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
            (nome, cpf, tel, email),
        )
        cli_ids.append(res[0]["id"])

    print("6. Inserindo histórico recente de compras, vendas e financeiro...")
    c1 = db.executar(
        """
        INSERT INTO compra (fornecedor_id, usuario_id, data_compra, valor_total, status)
        VALUES (%s, %s, CURRENT_DATE - INTERVAL '10 days', 1250.00, 'CONFIRMADA') RETURNING id
        """,
        (forn_ids[0], usuario_id),
    )[0]["id"]
    db.executar(
        """
        INSERT INTO item_compra (compra_id, produto_id, quantidade, custo_unitario)
        VALUES (%s, %s, 50, 4.50)
        """,
        (c1, prod_ids[0][0]),
    )
    db.executar(
        """
        INSERT INTO lancamento_financeiro (tipo, descricao, valor, data_vencimento, data_pagamento, status, compra_id, usuario_id)
        VALUES ('PAGAR', 'Compra Distribuidora Santa Cruz #1', 1250.00, CURRENT_DATE - INTERVAL '2 days', NOW() - INTERVAL '2 days', 'PAGO', %s, %s)
        """,
        (c1, usuario_id),
    )

    c2 = db.executar(
        """
        INSERT INTO compra (fornecedor_id, usuario_id, data_compra, valor_total, status)
        VALUES (%s, %s, CURRENT_DATE - INTERVAL '3 days', 680.00, 'CONFIRMADA') RETURNING id
        """,
        (forn_ids[1], usuario_id),
    )[0]["id"]
    db.executar(
        """
        INSERT INTO item_compra (compra_id, produto_id, quantidade, custo_unitario)
        VALUES (%s, %s, 20, 14.90)
        """,
        (c2, prod_ids[4][0]),
    )
    db.executar(
        """
        INSERT INTO lancamento_financeiro (tipo, descricao, valor, data_vencimento, status, compra_id, usuario_id)
        VALUES ('PAGAR', 'Boleto Profarma Distribuidora #2', 680.00, CURRENT_DATE + INTERVAL '5 days', 'PENDENTE', %s, %s)
        """,
        (c2, usuario_id),
    )

    vendas_demo = [
        (6, cli_ids[0], "PIX", [(prod_ids[0], 3), (prod_ids[7], 1)]),
        (5, cli_ids[1], "CARTAO", [(prod_ids[4], 2), (prod_ids[9], 2)]),
        (4, cli_ids[2], "DINHEIRO", [(prod_ids[1], 4), (prod_ids[12], 2)]),
        (3, cli_ids[3], "PIX", [(prod_ids[8], 2), (prod_ids[11], 2)]),
        (2, cli_ids[4], "CARTAO", [(prod_ids[2], 3), (prod_ids[13], 2)]),
        (1, cli_ids[0], "PIX", [(prod_ids[0], 5), (prod_ids[10], 3)]),
        (0, cli_ids[2], "PIX", [(prod_ids[7], 2), (prod_ids[9], 3)]),
    ]
    for dias_atras, cli_id, pgto, itens in vendas_demo:
        total_venda = sum(p[3] * qtd for p, qtd in itens)
        v_id = db.executar(
            """
            INSERT INTO venda (cliente_id, usuario_id, data_venda, desconto, valor_total, forma_pagamento, status)
            VALUES (%s, %s, NOW() - (%s || ' days')::interval, 0, %s, %s, 'CONFIRMADA') RETURNING id
            """,
            (cli_id, usuario_id, dias_atras, total_venda, pgto),
        )[0]["id"]
        for prod, qtd in itens:
            db.executar(
                """
                INSERT INTO item_venda (venda_id, produto_id, quantidade, preco_unitario, custo_unitario)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (v_id, prod[0], qtd, prod[3], prod[2]),
            )
        db.executar(
            """
            INSERT INTO lancamento_financeiro (tipo, descricao, valor, data_vencimento, data_pagamento, status, venda_id, usuario_id)
            VALUES ('RECEBER', %s, %s, CURRENT_DATE - (%s || ' days')::interval, NOW() - (%s || ' days')::interval, 'PAGO', %s, %s)
            """,
            (f"Venda PDV #{v_id}", total_venda, dias_atras, dias_atras, v_id, usuario_id),
        )

    print("Concluído! Base populada com sucesso.")


if __name__ == "__main__":
    popular_banco()