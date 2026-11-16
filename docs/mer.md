# MER - FarmaCore

Diagrama entidade-relacionamento (notação Mermaid). Para visualizar: cole o bloco em https://mermaid.live ou abra o arquivo no GitHub, que renderiza automaticamente.

```mermaid
erDiagram
    USUARIO ||--o{ COMPRA : registra
    USUARIO ||--o{ VENDA : registra
    USUARIO ||--o{ PERDA : registra
    USUARIO ||--o{ MOVIMENTACAO_ESTOQUE : executa
    USUARIO ||--o{ LANCAMENTO_FINANCEIRO : lanca
    USUARIO ||--o{ LOG_AUDITORIA : gera

    CATEGORIA ||--o{ PRODUTO : classifica
    FORNECEDOR ||--o{ COMPRA : fornece
    CLIENTE |o--o{ VENDA : realiza

    COMPRA ||--|{ ITEM_COMPRA : contem
    VENDA ||--|{ ITEM_VENDA : contem
    PRODUTO ||--o{ ITEM_COMPRA : comprado_em
    PRODUTO ||--o{ ITEM_VENDA : vendido_em
    PRODUTO ||--o{ PERDA : sofre
    PRODUTO ||--o{ MOVIMENTACAO_ESTOQUE : movimenta

    COMPRA ||--o| LANCAMENTO_FINANCEIRO : gera_conta_a_pagar
    VENDA ||--o| LANCAMENTO_FINANCEIRO : gera_conta_a_receber
    PERDA ||--o| LANCAMENTO_FINANCEIRO : gera_despesa

    USUARIO {
        bigint id PK
        varchar email UK
        varchar nome
        varchar perfil
        boolean ativo
        timestamptz criado_em
    }
    CATEGORIA {
        bigint id PK
        varchar nome UK
        boolean ativo
    }
    PRODUTO {
        bigint id PK
        varchar nome
        bigint categoria_id FK
        varchar codigo_barras UK
        numeric preco_custo
        numeric preco_venda
        int estoque_minimo
        int saldo_estoque
        boolean ativo
    }
    FORNECEDOR {
        bigint id PK
        varchar razao_social
        varchar cnpj UK
        varchar telefone
        varchar email
    }
    CLIENTE {
        bigint id PK
        varchar nome
        varchar cpf UK
        varchar telefone
        varchar email
    }
    COMPRA {
        bigint id PK
        bigint fornecedor_id FK
        bigint usuario_id FK
        date data_compra
        numeric valor_total
        varchar status
        timestamptz criado_em
    }
    ITEM_COMPRA {
        bigint id PK
        bigint compra_id FK
        bigint produto_id FK
        int quantidade
        numeric custo_unitario
    }
    VENDA {
        bigint id PK
        bigint cliente_id FK
        bigint usuario_id FK
        timestamptz data_venda
        numeric desconto
        numeric valor_total
        varchar forma_pagamento
        varchar status
    }
    ITEM_VENDA {
        bigint id PK
        bigint venda_id FK
        bigint produto_id FK
        int quantidade
        numeric preco_unitario
        numeric custo_unitario
    }
    PERDA {
        bigint id PK
        bigint produto_id FK
        bigint usuario_id FK
        int quantidade
        varchar motivo
        numeric custo_unitario
        numeric valor_total
        timestamptz data_perda
    }
    MOVIMENTACAO_ESTOQUE {
        bigint id PK
        bigint produto_id FK
        varchar tipo
        varchar origem
        bigint origem_id
        int quantidade
        bigint usuario_id FK
        timestamptz criado_em
    }
    LANCAMENTO_FINANCEIRO {
        bigint id PK
        varchar tipo
        numeric valor
        date data_vencimento
        timestamptz data_pagamento
        varchar status
        bigint compra_id FK
        bigint venda_id FK
        bigint perda_id FK
        bigint usuario_id FK
    }
    LOG_AUDITORIA {
        bigint id PK
        bigint usuario_id FK
        varchar acao
        varchar tabela
        bigint registro_id
        jsonb detalhe
        timestamptz criado_em
    }
```

## Como a integração aparece no modelo

| Operação | Tabelas afetadas |
|---|---|
| Confirmar compra | `compra` + `item_compra` → `movimentacao_estoque` (ENTRADA) → `produto.saldo_estoque` sobe → `lancamento_financeiro` (PAGAR) |
| Confirmar venda | `venda` + `item_venda` → `movimentacao_estoque` (SAIDA) → `produto.saldo_estoque` cai → `lancamento_financeiro` (RECEBER) |
| Registrar perda | `perda` → `movimentacao_estoque` (SAIDA) → `produto.saldo_estoque` cai → `lancamento_financeiro` (DESPESA) |
| Cancelar compra/venda | status vira CANCELADA, nova `movimentacao_estoque` de estorno e lançamento CANCELADO; nada é apagado |
