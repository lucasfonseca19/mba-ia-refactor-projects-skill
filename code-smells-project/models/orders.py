"""Pedido, itens e estoque formam uma única transação SQLite."""
from collections import defaultdict
import math
from database import get_db
from errors import ApiError
from models.products import SQLITE_MAX_INTEGER

ORDER_STATUSES = ("pendente","aprovado","enviado","entregue","cancelado")


def validate_items(items):
    if not isinstance(items,list) or not items:
        raise ApiError("Pedido deve ter pelo menos 1 item")
    demand = defaultdict(int)
    for item in items:
        if not isinstance(item,dict):
            raise ApiError("Item inválido")
        product_id, quantity = item.get("produto_id"),item.get("quantidade")
        if type(product_id) is not int or not 0 < product_id <= SQLITE_MAX_INTEGER:
            raise ApiError("Produto ID inválido")
        if type(quantity) is not int or not 0 < quantity <= SQLITE_MAX_INTEGER:
            raise ApiError("Quantidade deve ser um inteiro positivo")
        demand[product_id] += quantity
    return demand


def create_order(user_id,items):
    if type(user_id) is not int or not 0 < user_id <= SQLITE_MAX_INTEGER:
        raise ApiError("Usuário ID inválido")
    demand, db = validate_items(items),get_db()
    with db:
        # Serializa escritores antes da leitura/validação do estoque.
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT id FROM usuarios WHERE id=?",(user_id,)).fetchone() is None:
            raise ApiError("Usuário não encontrado",404)
        products = {}
        for product_id, quantity in demand.items():
            product = db.execute("SELECT * FROM produtos WHERE id=?",(product_id,)).fetchone()
            if product is None:
                raise ApiError(f"Produto {product_id} não encontrado")
            if product["estoque"] < quantity:
                raise ApiError("Estoque insuficiente para " + product["nome"])
            products[product_id] = product
        try:
            total = sum(products[item["produto_id"]]["preco"] * item["quantidade"] for item in items)
            valid_total = math.isfinite(total)
        except (OverflowError,TypeError,ValueError):
            valid_total = False
        if not valid_total:
            raise ApiError("Total do pedido fora do intervalo numérico")
        cursor = db.execute("INSERT INTO pedidos(usuario_id,status,total) VALUES(?,'pendente',?)",(user_id,total))
        order_id = cursor.lastrowid
        for item in items:
            db.execute("INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,?,?,?)",
                       (order_id,item["produto_id"],item["quantidade"],products[item["produto_id"]]["preco"]))
        for product_id, quantity in demand.items():
            changed = db.execute("UPDATE produtos SET estoque=estoque-? WHERE id=? AND estoque>=?",(quantity,product_id,quantity))
            if changed.rowcount != 1:
                raise ApiError("Estoque insuficiente")
    return {"pedido_id":order_id,"total":total}


def list_orders(user_id=None):
    db = get_db()
    condition, params = ("",()) if user_id is None else (" WHERE usuario_id=?",(user_id,))
    orders = db.execute("SELECT * FROM pedidos" + condition + " ORDER BY id",params).fetchall()
    where = "" if user_id is None else " WHERE p.usuario_id=?"
    items = db.execute("SELECT i.*,pr.nome AS produto_nome FROM itens_pedido i JOIN pedidos p ON p.id=i.pedido_id "
                       "LEFT JOIN produtos pr ON pr.id=i.produto_id" + where + " ORDER BY i.id",params).fetchall()
    by_order = defaultdict(list)
    for item in items:
        by_order[item["pedido_id"]].append(item)
    return [(order,by_order[order["id"]]) for order in orders]


def update_status(order_id,status):
    if status not in ORDER_STATUSES:
        raise ApiError("Status inválido")
    db = get_db()
    with db:
        if db.execute("UPDATE pedidos SET status=? WHERE id=?",(status,order_id)).rowcount != 1:
            raise ApiError("Pedido não encontrado",404)
