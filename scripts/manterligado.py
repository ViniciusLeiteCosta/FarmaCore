"""Rotina automatizada para manter o banco Supabase ativo."""
import json
import os
import sys
import psycopg


def main() -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Erro: variável de ambiente DATABASE_URL não definida.", file=sys.stderr)
        sys.exit(1)

    with psycopg.connect(db_url, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            # 1. Consulta leve de leitura para registrar atividade no PostgreSQL
            cur.execute("SELECT NOW();")
            agora = cur.fetchone()[0]

            # 2. Registro opcional na tabela log_auditoria para evidência de execução
            cur.execute(
                """
                INSERT INTO log_auditoria (usuario_id, acao, tabela, detalhe)
                VALUES (NULL, 'KEEPALIVE', 'sistema', %s::jsonb)
                """,
                (json.dumps({"origem": "github_actions", "timestamp": str(agora)}),),
            )
        conn.commit()
        print(f"Keep-alive executado com sucesso em: {agora}")


if __name__ == "__main__":
    main()