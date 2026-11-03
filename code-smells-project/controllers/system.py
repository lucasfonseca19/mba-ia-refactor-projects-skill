from flask import current_app,jsonify
from controllers.input import json_object
from errors import ApiError
from models import admin,reports


def index():
    return jsonify(mensagem="Bem-vindo à API da Loja",versao="1.0.0",endpoints={
        "produtos":"/produtos","usuarios":"/usuarios","pedidos":"/pedidos","login":"/login",
        "relatorios":"/relatorios/vendas","health":"/health"})


def health():
    return jsonify(status="ok",database="connected",counts=admin.health(),versao="1.0.0")


def sales_report():
    return jsonify(dados=reports.sales_report(),sucesso=True)


def require_admin_tools():
    if not current_app.config["ADMIN_TOOLS_ENABLED"]:
        raise ApiError("Ferramentas administrativas desabilitadas",403)


def reset_database():
    require_admin_tools()
    admin.reset_database()
    return jsonify(mensagem="Banco de dados resetado",sucesso=True)


def execute_query():
    require_admin_tools()
    rows = admin.execute_query(json_object().get("sql"))
    if rows is not None:
        return jsonify(dados=rows,sucesso=True)
    return jsonify(mensagem="Query executada",sucesso=True)
