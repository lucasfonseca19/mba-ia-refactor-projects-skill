from flask import jsonify,request
from controllers.input import json_object,optional_number
from models import products
from views import product


def list_products():
    return jsonify(dados=[product(row) for row in products.list_products()],sucesso=True)


def search_products():
    rows = products.list_products(request.args.get("q",""),request.args.get("categoria"),
                                  optional_number("preco_min"),optional_number("preco_max"))
    return jsonify(dados=[product(row) for row in rows],total=len(rows),sucesso=True)


def get_product(id):
    return jsonify(dados=product(products.find_product(id)),sucesso=True)


def create_product():
    product_id = products.create_product(json_object())
    return jsonify(dados={"id":product_id},sucesso=True,mensagem="Produto criado"),201


def update_product(id):
    products.update_product(id,json_object())
    return jsonify(sucesso=True,mensagem="Produto atualizado")


def delete_product(id):
    products.delete_product(id)
    return jsonify(sucesso=True,mensagem="Produto deletado")
