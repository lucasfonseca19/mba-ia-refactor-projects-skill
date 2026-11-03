from flask import jsonify,session
from controllers.input import json_object
from errors import ApiError
from models import users
from security import establish_session,require_owner
from views import user


def list_users():
    return jsonify(dados=[user(row) for row in users.list_users()],sucesso=True)


def get_user(id):
    require_owner(id)
    row = users.find_user(id)
    if row is None:
        raise ApiError("Usuário não encontrado",404)
    return jsonify(dados=user(row),sucesso=True)


def create_user():
    data = json_object()
    uid = users.create_user(data.get("nome"),data.get("email"),data.get("senha"))
    return jsonify(dados={"id":uid},sucesso=True),201


def login():
    session.clear()
    data = json_object()
    row = users.authenticate(data.get("email"),data.get("senha"))
    if row is None:
        raise ApiError("Email ou senha inválidos",401)
    return jsonify(dados=user(row,login=True),sucesso=True,mensagem="Login OK",csrf_token=establish_session(row))
