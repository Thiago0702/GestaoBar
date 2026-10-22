
import re
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = BASE_DIR / "instance" / "gestaobar.db"


def migrar():
    if not CAMINHO_BANCO.exists():
        raise FileNotFoundError(
            f"Banco não encontrado: {CAMINHO_BANCO}"
        )

    # Criar backup consistente do banco.
    nome_backup = (
        "gestaobar_backup_pre_pedidos_publicos_"
        + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        + ".db"
    )
    caminho_backup = CAMINHO_BANCO.parent / nome_backup

    origem = sqlite3.connect(CAMINHO_BANCO)
    backup = sqlite3.connect(caminho_backup)

    try:
        origem.backup(backup)
    finally:
        backup.close()
        origem.close()

    print(f"Backup criado: {caminho_backup}")

    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = OFF")

    try:
        conexao.execute("BEGIN IMMEDIATE")

        vendas_antes = conexao.execute(
            "SELECT * FROM vendas ORDER BY id"
        ).fetchall()

        itens_antes = conexao.execute(
            "SELECT * FROM itens_venda ORDER BY id"
        ).fetchall()

        colunas = conexao.execute(
            "PRAGMA table_info(vendas)"
        ).fetchall()

        usuario_id = next(
            (c for c in colunas if c[1] == "usuario_id"),
            None
        )

        if usuario_id is None:
            raise RuntimeError("Coluna usuario_id não encontrada.")

        if usuario_id[3] == 0:
            print("usuario_id já aceita NULL. Nenhuma alteração necessária.")
            conexao.rollback()
            return

        schema = conexao.execute("""
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'vendas'
        """).fetchone()

        if not schema or not schema[0]:
            raise RuntimeError("Estrutura da tabela vendas não encontrada.")

        # Capturar índices e gatilhos definidos pelo usuário.
        objetos = conexao.execute("""
            SELECT sql
            FROM sqlite_master
            WHERE tbl_name = 'vendas'
              AND type IN ('index', 'trigger')
              AND sql IS NOT NULL
        """).fetchall()

        sql_novo = re.sub(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?vendas[\"`\]]?",
            "CREATE TABLE vendas_nova",
            schema[0],
            count=1,
            flags=re.IGNORECASE
        )

        if sql_novo == schema[0]:
            raise RuntimeError("Não foi possível preparar a nova tabela.")

        sql_novo, alteracoes = re.subn(
            r"(\busuario_id\s+INTEGER)\s+NOT\s+NULL\b",
            r"\1",
            sql_novo,
            count=1,
            flags=re.IGNORECASE
        )

        if alteracoes != 1:
            raise RuntimeError(
                "Não foi possível identificar com segurança "
                "a restrição NOT NULL de usuario_id."
            )

        conexao.execute(sql_novo)

        nomes_colunas = [c[1] for c in colunas]
        lista_colunas = ", ".join(
            '"' + nome.replace('"', '""') + '"'
            for nome in nomes_colunas
        )

        conexao.execute(
            f"INSERT INTO vendas_nova ({lista_colunas}) "
            f"SELECT {lista_colunas} FROM vendas"
        )

        # Conferir todos os registros antes de substituir a tabela.
        vendas_copiadas = conexao.execute(
            "SELECT * FROM vendas_nova ORDER BY id"
        ).fetchall()

        if vendas_copiadas != vendas_antes:
            raise RuntimeError(
                "Os registros de vendas não foram copiados exatamente."
            )

        conexao.execute("DROP TABLE vendas")
        conexao.execute(
            "ALTER TABLE vendas_nova RENAME TO vendas"
        )

        # Restaurar eventuais índices e gatilhos.
        for (sql_objeto,) in objetos:
            conexao.execute(sql_objeto)

        vendas_depois = conexao.execute(
            "SELECT * FROM vendas ORDER BY id"
        ).fetchall()

        itens_depois = conexao.execute(
            "SELECT * FROM itens_venda ORDER BY id"
        ).fetchall()

        coluna_final = next(
            c for c in conexao.execute(
                "PRAGMA table_info(vendas)"
            ).fetchall()
            if c[1] == "usuario_id"
        )

        if vendas_depois != vendas_antes:
            raise RuntimeError("Os dados das vendas foram alterados.")

        if itens_depois != itens_antes:
            raise RuntimeError("Os itens de venda foram alterados.")

        if coluna_final[3] != 0:
            raise RuntimeError("usuario_id ainda está marcado como obrigatório.")

        erros_fk = conexao.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if erros_fk:
            raise RuntimeError(
                f"Falha nas chaves estrangeiras: {erros_fk}"
            )

        conexao.execute("PRAGMA user_version")
        conexao.commit()

        print("\nMIGRAÇÃO CONCLUÍDA!")
        print(f"Vendas preservadas: {len(vendas_depois)}")
        print(f"Itens preservados: {len(itens_depois)}")
        print("usuario_id aceita NULL: Sim")
        print("Verificação das chaves estrangeiras: OK")
        print(f"Backup mantido em: {caminho_backup}")

    except Exception:
        conexao.rollback()
        print("\nERRO: a migração foi revertida.")
        print("O backup foi mantido.")
        raise

    finally:
        conexao.close()


if __name__ == "__main__":
    migrar()
