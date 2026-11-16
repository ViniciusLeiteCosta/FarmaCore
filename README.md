# FarmaCore 💊

ERP simplificado para farmácia (Sistemas de Informação e Tecnologias, 2026.2, 1ª VA).
Python + Streamlit, PostgreSQL (Supabase), login Google, deploy no Streamlit Community Cloud.

## Estrutura

```
app.py              ponto de entrada (login + navegação)
core/db.py          conexão e helpers de banco
core/auth.py        login Google e perfis (ADMIN, FARMACEUTICO, CAIXA)
paginas/            uma página por módulo
db/schema.sql       script do banco (rodar no SQL Editor do Supabase)
docs/mer.md         diagrama entidade-relacionamento
.streamlit/secrets.toml.example   modelo das credenciais
```

## Rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # e preencha
streamlit run app.py
```
