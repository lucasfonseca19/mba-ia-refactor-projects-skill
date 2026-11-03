"""Validade e persistência de produtos, sem dependência de request/response."""
import math
from database import get_db
from errors import ApiError

CATEGORIES = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
SQLITE_MAX_INTEGER = 2**63 - 1


def finite_number(value):
    if type(value) not in (int,float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def validate_product(data):
    for field, label in (("nome","Nome"),("preco","Preço"),("estoque","Estoque")):
        if field not in data:
            raise ApiError(f"{label} é obrigatório")
    name, price, stock = data["nome"], data["preco"], data["estoque"]
    category, description = data.get("categoria", "geral"), data.get("descricao", "")
    if not isinstance(name, str) or not 2 <= len(name) <= 200:
        raise ApiError("Nome deve ter entre 2 e 200 caracteres")
    if not finite_number(price) or price < 0:
        raise ApiError("Preço deve ser um número finito não negativo")
    if type(stock) is not int or not 0 <= stock <= SQLITE_MAX_INTEGER:
        raise ApiError("Estoque deve ser um inteiro não negativo")
    if category not in CATEGORIES:
        raise ApiError("Categoria inválida")
    if not isinstance(description, str):
        raise ApiError("Descrição inválida")
    # A coluna é REAL; não enviar um int Python fora do intervalo de binding.
    return name, description, float(price), stock, category


def list_products(term="", category=None, minimum=None, maximum=None):
    clauses, values = ["1=1"], []
    if term:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        values.extend((f"%{term}%", f"%{term}%"))
    if category:
        clauses.append("categoria = ?")
        values.append(category)
    for operator, value in ((">=",minimum),("<=",maximum)):
        if value is not None:
            clauses.append(f"preco {operator} ?")
            values.append(value)
    return get_db().execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses) + " ORDER BY id", values).fetchall()


def find_product(product_id):
    product = get_db().execute("SELECT * FROM produtos WHERE id=?", (product_id,)).fetchone()
    if product is None:
        raise ApiError("Produto não encontrado",404)
    return product


def create_product(data):
    values, db = validate_product(data), get_db()
    with db:
        cursor = db.execute("INSERT INTO produtos(nome,descricao,preco,estoque,categoria) VALUES(?,?,?,?,?)", values)
    return cursor.lastrowid


def update_product(product_id, data):
    find_product(product_id)
    values, db = validate_product(data), get_db()
    with db:
        db.execute("UPDATE produtos SET nome=?,descricao=?,preco=?,estoque=?,categoria=? WHERE id=?", (*values,product_id))


def delete_product(product_id):
    db = get_db()
    with db:
        if db.execute("DELETE FROM produtos WHERE id=?", (product_id,)).rowcount != 1:
            raise ApiError("Produto não encontrado",404)
