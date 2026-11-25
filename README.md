# FarmaCore 💊

Sistema ERP simplificado para gestão de farmácias, desenvolvido como projeto da disciplina **Sistemas de Informação e Tecnologias (2026.2 — 1ª VA)**.

Construído em **Python** com **Streamlit**, banco de dados relacional **PostgreSQL (Supabase)**, autenticação via **Google OAuth 2.0 (OIDC)** com controle de acesso baseado em perfis (**RBAC**) e deploy contínuo no **Streamlit Community Cloud**.

---

## Funcionalidades e Módulos

- **🔐 Autenticação & Governança (RBAC):** Login corporativo via Google OAuth 2.0 com sincronização automática de usuários no banco, trilha de auditoria de acessos e três níveis de permissão (`ADMIN`, `FARMACEUTICO` e `CAIXA`), incluindo simulador de visão em tempo real na barra lateral para perfis administradores.
- **🏠 Início (Dashboard Executivo):** Visão geral em tempo real com faturamento mensal, ticket médio, contagem de itens abaixo do estoque mínimo, contas a pagar pendentes, gráfico de evolução diária de vendas e alertas de reposição.
- **📁 Cadastros:** Manutenção de produtos/medicamentos (código de barras, custo, preço de venda, estoque mínimo), categorias, fornecedores e clientes.
- **🛒 Compras:** Registro de entrada de mercadorias por fornecedor, atualização automática do saldo em estoque e geração de título a pagar no financeiro *(acesso restrito a `ADMIN` e `FARMACEUTICO`)*.
- **📦 Estoque:** Consulta de saldos atuais, alertas de nível crítico e histórico completo de movimentações (entradas, saídas, perdas e estornos).
- **💰 Vendas (PDV):** Frente de caixa com cálculo de subtotal/desconto, múltiplas formas de pagamento (`DINHEIRO`, `CARTAO`, `PIX`), baixa automática de estoque e lançamento de receita.
- **⚠️ Operacional (Perdas):** Registro de baixas por vencimento ou avaria com impacto direto no estoque e lançamento de despesa *(acesso restrito a `ADMIN` e `FARMACEUTICO`)*.
- **📊 Financeiro & Auditoria:** Controle centralizado de contas a pagar, contas a receber e despesas operacionais, com baixa de pagamentos, gestão de perfis de usuários e logs de auditoria *(acesso restrito a `ADMIN`)*.

---

## Estrutura do Projeto

```text
FarmaCore/
├── app.py                            # Ponto de entrada, identidade visual, RBAC e navegação
├── logo.png                          # Logotipo oficial exibido na tela de login e na sidebar
├── requirements.txt                  # Dependências Python do projeto (Streamlit, Authlib, psycopg)
├── core/
│   ├── auth.py                       # Autenticação Google OAuth, perfis de acesso e simulador de visão
│   ├── db.py                         # Pool de conexão e helpers de consulta SQL (psycopg)
│   ├── style.py                      # Estilização global (CSS) e tema visual
│   └── ui.py                         # Componentes visuais reutilizáveis e estados vazios
├── paginas/
│   ├── inicio.py                     # Dashboard executivo
│   ├── cadastros.py                  # Gestão de produtos, categorias, fornecedores e clientes
│   ├── compras.py                    # Entrada de compras
│   ├── estoque.py                    # Controle e histórico de estoque
│   ├── vendas.py                     # Ponto de venda (PDV)
│   ├── operacional.py                # Registro de perdas
│   └── financeiro.py                 # Fluxo financeiro, gestão de usuários e auditoria
├── db/
│   └── schema.sql                    # DDL completo do banco (tabelas, constraints e índices)
├── scripts/
│   └── seed.py                       # Script para popular o banco com dados iniciais de demonstração
├── docs/
│   └── mer.md                        # Modelo Entidade-Relacionamento (MER)
└── .streamlit/
    └── secrets.toml.example          # Modelo de configuração das credenciais (Supabase e Google OAuth)
