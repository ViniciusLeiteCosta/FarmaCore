-- =====================================================================
-- FarmaCore - ERP simplificado de farmácia (1ª VA)
-- PostgreSQL (Supabase). Execute no SQL Editor do projeto.
-- Princípios: histórico imutável (estorno em vez de exclusão),
-- timestamps em todos os registros, integridade por constraints.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. AUTENTICAÇÃO E CONTROLE DE ACESSO
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id          BIGSERIAL PRIMARY KEY,
    email       VARCHAR(150) NOT NULL UNIQUE,          -- e-mail da conta Google
    nome        VARCHAR(120) NOT NULL,
    perfil      VARCHAR(20)  NOT NULL DEFAULT 'CAIXA'
                CHECK (perfil IN ('ADMIN', 'FARMACEUTICO', 'CAIXA')),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 2. CADASTROS
-- ---------------------------------------------------------------------
CREATE TABLE categoria (
    id          BIGSERIAL PRIMARY KEY,
    nome        VARCHAR(80) NOT NULL UNIQUE,
    ativo       BOOLEAN     NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE produto (
    id              BIGSERIAL PRIMARY KEY,
    nome            VARCHAR(150)  NOT NULL,
    categoria_id    BIGINT        NOT NULL REFERENCES categoria(id),
    codigo_barras   VARCHAR(20)   UNIQUE,
    preco_custo     NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (preco_custo >= 0),
    preco_venda     NUMERIC(12,2) NOT NULL CHECK (preco_venda >= 0),
    estoque_minimo  INTEGER       NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0),
    saldo_estoque   INTEGER       NOT NULL DEFAULT 0 CHECK (saldo_estoque >= 0),
    ativo           BOOLEAN       NOT NULL DEFAULT TRUE,
    criado_em       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE fornecedor (
    id            BIGSERIAL PRIMARY KEY,
    razao_social  VARCHAR(150) NOT NULL,
    cnpj          VARCHAR(18)  NOT NULL UNIQUE,
    telefone      VARCHAR(20),
    email         VARCHAR(150),
    ativo         BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE cliente (
    id          BIGSERIAL PRIMARY KEY,
    nome        VARCHAR(150) NOT NULL,
    cpf         VARCHAR(14)  UNIQUE,
    telefone    VARCHAR(20),
    email       VARCHAR(150),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 3. COMPRAS
-- ---------------------------------------------------------------------
CREATE TABLE compra (
    id             BIGSERIAL PRIMARY KEY,
    fornecedor_id  BIGINT        NOT NULL REFERENCES fornecedor(id),
    usuario_id     BIGINT        NOT NULL REFERENCES usuario(id),
    data_compra    DATE          NOT NULL DEFAULT CURRENT_DATE,
    valor_total    NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (valor_total >= 0),
    status         VARCHAR(15)   NOT NULL DEFAULT 'CONFIRMADA'
                   CHECK (status IN ('CONFIRMADA', 'CANCELADA')),
    criado_em      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    cancelado_em   TIMESTAMPTZ
);

CREATE TABLE item_compra (
    id              BIGSERIAL PRIMARY KEY,
    compra_id       BIGINT        NOT NULL REFERENCES compra(id),
    produto_id      BIGINT        NOT NULL REFERENCES produto(id),
    quantidade      INTEGER       NOT NULL CHECK (quantidade > 0),
    custo_unitario  NUMERIC(12,2) NOT NULL CHECK (custo_unitario >= 0)
);

-- ---------------------------------------------------------------------
-- 4. VENDAS
-- ---------------------------------------------------------------------
CREATE TABLE venda (
    id               BIGSERIAL PRIMARY KEY,
    cliente_id       BIGINT        REFERENCES cliente(id),   -- NULL = venda de balcão
    usuario_id       BIGINT        NOT NULL REFERENCES usuario(id),
    data_venda       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    desconto         NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (desconto >= 0),
    valor_total      NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (valor_total >= 0),
    forma_pagamento  VARCHAR(15)   NOT NULL
                     CHECK (forma_pagamento IN ('DINHEIRO', 'CARTAO', 'PIX')),
    status           VARCHAR(15)   NOT NULL DEFAULT 'CONFIRMADA'
                     CHECK (status IN ('CONFIRMADA', 'CANCELADA')),
    criado_em        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    cancelado_em     TIMESTAMPTZ
);

CREATE TABLE item_venda (
    id              BIGSERIAL PRIMARY KEY,
    venda_id        BIGINT        NOT NULL REFERENCES venda(id),
    produto_id      BIGINT        NOT NULL REFERENCES produto(id),
    quantidade      INTEGER       NOT NULL CHECK (quantidade > 0),
    preco_unitario  NUMERIC(12,2) NOT NULL CHECK (preco_unitario >= 0),
    custo_unitario  NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (custo_unitario >= 0)
        -- custo no momento da venda: permite calcular margem na 2ª VA
);

-- ---------------------------------------------------------------------
-- 5. OPERACIONAL (perdas por vencimento ou avaria)
-- ---------------------------------------------------------------------
CREATE TABLE perda (
    id              BIGSERIAL PRIMARY KEY,
    produto_id      BIGINT        NOT NULL REFERENCES produto(id),
    usuario_id      BIGINT        NOT NULL REFERENCES usuario(id),
    quantidade      INTEGER       NOT NULL CHECK (quantidade > 0),
    motivo          VARCHAR(15)   NOT NULL CHECK (motivo IN ('VENCIMENTO', 'AVARIA')),
    custo_unitario  NUMERIC(12,2) NOT NULL CHECK (custo_unitario >= 0),
    valor_total     NUMERIC(12,2) GENERATED ALWAYS AS (quantidade * custo_unitario) STORED,
    observacao      VARCHAR(255),
    data_perda      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    criado_em       TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 6. ESTOQUE (histórico imutável de movimentações)
-- ---------------------------------------------------------------------
CREATE TABLE movimentacao_estoque (
    id          BIGSERIAL PRIMARY KEY,
    produto_id  BIGINT      NOT NULL REFERENCES produto(id),
    tipo        VARCHAR(10) NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    origem      VARCHAR(20) NOT NULL
                CHECK (origem IN ('COMPRA', 'VENDA', 'PERDA',
                                  'ESTORNO_COMPRA', 'ESTORNO_VENDA')),
    origem_id   BIGINT      NOT NULL,          -- id da compra, venda ou perda
    quantidade  INTEGER     NOT NULL CHECK (quantidade > 0),
    usuario_id  BIGINT      NOT NULL REFERENCES usuario(id),
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 7. FINANCEIRO
-- PAGAR   -> gerado por compra
-- RECEBER -> gerado por venda
-- DESPESA -> gerado por perda (não é fluxo de caixa, é prejuízo contábil)
-- ---------------------------------------------------------------------
CREATE TABLE lancamento_financeiro (
    id               BIGSERIAL PRIMARY KEY,
    tipo             VARCHAR(10)   NOT NULL CHECK (tipo IN ('PAGAR', 'RECEBER', 'DESPESA')),
    descricao        VARCHAR(200)  NOT NULL,
    valor            NUMERIC(12,2) NOT NULL CHECK (valor > 0),
    data_vencimento  DATE          NOT NULL,
    data_pagamento   TIMESTAMPTZ,
    status           VARCHAR(15)   NOT NULL DEFAULT 'PENDENTE'
                     CHECK (status IN ('PENDENTE', 'PAGO', 'CANCELADO', 'LANCADO')),
    compra_id        BIGINT REFERENCES compra(id),
    venda_id         BIGINT REFERENCES venda(id),
    perda_id         BIGINT REFERENCES perda(id),
    usuario_id       BIGINT        NOT NULL REFERENCES usuario(id),
    criado_em        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    -- cada lançamento tem exatamente uma origem
    CONSTRAINT ck_lancamento_origem CHECK (
        (tipo = 'PAGAR'   AND compra_id IS NOT NULL AND venda_id IS NULL AND perda_id IS NULL) OR
        (tipo = 'RECEBER' AND venda_id  IS NOT NULL AND compra_id IS NULL AND perda_id IS NULL) OR
        (tipo = 'DESPESA' AND perda_id  IS NOT NULL AND compra_id IS NULL AND venda_id IS NULL)
    ),
    -- pago exige data de pagamento
    CONSTRAINT ck_lancamento_pago CHECK (status <> 'PAGO' OR data_pagamento IS NOT NULL)
);

-- ---------------------------------------------------------------------
-- 8. AUDITORIA
-- ---------------------------------------------------------------------
CREATE TABLE log_auditoria (
    id          BIGSERIAL PRIMARY KEY,
    usuario_id  BIGINT      REFERENCES usuario(id),
    acao        VARCHAR(30) NOT NULL,          -- ex.: LOGIN, CRIAR, EDITAR, CANCELAR
    tabela      VARCHAR(50),
    registro_id BIGINT,
    detalhe     JSONB,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- 9. REGRA DE NEGÓCIO NO BANCO: o saldo do produto é atualizado
--    automaticamente a cada movimentação. O CHECK (saldo_estoque >= 0)
--    impede vender mais do que existe em estoque.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_atualiza_saldo_estoque()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tipo = 'ENTRADA' THEN
        UPDATE produto
           SET saldo_estoque = saldo_estoque + NEW.quantidade,
               atualizado_em = now()
         WHERE id = NEW.produto_id;
    ELSE
        UPDATE produto
           SET saldo_estoque = saldo_estoque - NEW.quantidade,
               atualizado_em = now()
         WHERE id = NEW.produto_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movimentacao_atualiza_saldo
AFTER INSERT ON movimentacao_estoque
FOR EACH ROW EXECUTE FUNCTION fn_atualiza_saldo_estoque();

-- Histórico imutável: movimentações e auditoria não podem ser alteradas nem apagadas.
CREATE OR REPLACE FUNCTION fn_bloqueia_alteracao()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Registros de % são imutáveis. Use estorno.', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_movimentacao_imutavel
BEFORE UPDATE OR DELETE ON movimentacao_estoque
FOR EACH ROW EXECUTE FUNCTION fn_bloqueia_alteracao();

CREATE TRIGGER trg_auditoria_imutavel
BEFORE UPDATE OR DELETE ON log_auditoria
FOR EACH ROW EXECUTE FUNCTION fn_bloqueia_alteracao();

-- ---------------------------------------------------------------------
-- 10. ÍNDICES (consultas por período, produto e status)
-- ---------------------------------------------------------------------
CREATE INDEX idx_produto_categoria     ON produto(categoria_id);
CREATE INDEX idx_compra_fornecedor     ON compra(fornecedor_id);
CREATE INDEX idx_compra_data           ON compra(data_compra);
CREATE INDEX idx_item_compra_compra    ON item_compra(compra_id);
CREATE INDEX idx_item_compra_produto   ON item_compra(produto_id);
CREATE INDEX idx_venda_cliente         ON venda(cliente_id);
CREATE INDEX idx_venda_data            ON venda(data_venda);
CREATE INDEX idx_item_venda_venda      ON item_venda(venda_id);
CREATE INDEX idx_item_venda_produto    ON item_venda(produto_id);
CREATE INDEX idx_perda_produto         ON perda(produto_id);
CREATE INDEX idx_perda_data            ON perda(data_perda);
CREATE INDEX idx_mov_produto_data      ON movimentacao_estoque(produto_id, criado_em);
CREATE INDEX idx_mov_origem            ON movimentacao_estoque(origem, origem_id);
CREATE INDEX idx_lanc_tipo_status      ON lancamento_financeiro(tipo, status);
CREATE INDEX idx_lanc_vencimento       ON lancamento_financeiro(data_vencimento);
CREATE INDEX idx_auditoria_data        ON log_auditoria(criado_em);

-- ---------------------------------------------------------------------
-- 11. SEGURANÇA SUPABASE
-- Habilita RLS sem políticas: bloqueia o acesso pela API pública (anon).
-- O app Streamlit conecta direto no Postgres com a connection string,
-- que não é afetada pelo RLS.
-- ---------------------------------------------------------------------
ALTER TABLE usuario               ENABLE ROW LEVEL SECURITY;
ALTER TABLE categoria             ENABLE ROW LEVEL SECURITY;
ALTER TABLE produto               ENABLE ROW LEVEL SECURITY;
ALTER TABLE fornecedor            ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente               ENABLE ROW LEVEL SECURITY;
ALTER TABLE compra                ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_compra           ENABLE ROW LEVEL SECURITY;
ALTER TABLE venda                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_venda            ENABLE ROW LEVEL SECURITY;
ALTER TABLE perda                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimentacao_estoque  ENABLE ROW LEVEL SECURITY;
ALTER TABLE lancamento_financeiro ENABLE ROW LEVEL SECURITY;
ALTER TABLE log_auditoria         ENABLE ROW LEVEL SECURITY;
