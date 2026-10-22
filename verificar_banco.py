
import sqlite3
from pathlib import Path

caminho = Path("instance") / "gestaobar.db"

if not caminho.exists():
    print("Banco de dados não encontrado:", caminho)
else:
    conexao = sqlite3.connect(caminho)

    print("Integridade:", conexao.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0])

    print("Vendas:", conexao.execute(
        "SELECT COUNT(*) FROM vendas"
    ).fetchone()[0])

    print("Itens:", conexao.execute(
        "SELECT COUNT(*) FROM itens_venda"
    ).fetchone()[0])

    print("Coluna usuario_id:", [
        (coluna[1], coluna[3])
        for coluna in conexao.execute(
            "PRAGMA table_info(vendas)"
        )
        if coluna[1] == "usuario_id"
    ])

    print("Índices e gatilhos:", conexao.execute("""
        SELECT type, name
        FROM sqlite_master
        WHERE tbl_name = 'vendas'
          AND type IN ('index', 'trigger')
          AND sql IS NOT NULL
    """).fetchall())

    conexao.close()
