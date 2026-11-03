from flask import jsonify
from controllers.input import json_object
from errors import ApiError
from models import orders
from security import require_owner
from views import order


def create_order():
    data = json_object()
    uid = data.get("usuario_id")
    if type(uid) is not int or uid <= 0:
        raise ApiError("Usuário ID inválido")
    require_owner(uid)
    result = orders.create_order(uid,data.get("itens"))
    return jsonify(dados=result,sucesso=True,mensagem="Pedido criado com sucesso"),201


def list_orders():
    return jsonify(dados=[order(entry) for entry in orders.list_orders()],sucesso=True)


def user_orders(usuario_id):
    require_owner(usuario_id)
    return jsonify(dados=[order(entry) for entry in orders.list_orders(usuario_id)],sucesso=True)


def update_status(pedido_id):
    orders.update_status(pedido_id,json_object().get("status"))
    return jsonify(sucesso=True,mensagem="Status atualizado")
