"""Ferramentas privilegiadas, acessíveis somente pela política administrativa."""
from database import get_db
from errors import ApiError


def reset_database():
    db = get_db()
    with db:
        for table in ("itens_pedido","pedidos","produtos","usuarios"):
            db.execute(f"DELETE FROM {table}")


def execute_query(query):
    if not isinstance(query,str) or not query.strip():
        raise ApiError("Query não informada")
    db = get_db()
    with db:
        cursor = db.execute(query)
        if cursor.description is not None:
            return [dict(row) for row in cursor.fetchall()]
    return None


def health():
    db = get_db()
    return {table:db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("produtos","usuarios","pedidos")}
