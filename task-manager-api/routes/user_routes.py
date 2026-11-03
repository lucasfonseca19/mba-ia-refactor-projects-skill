from flask import Blueprint, request, jsonify, g
from services.auth_tokens import issue_token
from database import db
from services import user_service
from services.user_service import UserInputError

user_bp = Blueprint('users', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_service.list_users()), 200

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = user_service.find_user(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user_service.user_with_tasks(user)), 200

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json(silent=True)
    if isinstance(data, dict) and data.get('role', 'user') != 'user' and (not getattr(g, 'user', None) or g.user.role != 'admin'):
        return jsonify({'error': 'Acesso negado'}), 403
    try:
        user = user_service.create_user(data)
        return jsonify(user.to_dict()), 201
    except UserInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = user_service.find_user(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    try:
        user = user_service.update_user(user, request.get_json(silent=True))
        return jsonify(user.to_dict()), 200
    except UserInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = user_service.find_user(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    user_service.delete_user(user)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200

@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    user = user_service.find_user(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user_service.user_tasks(user)), 200

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')

    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    try:
        user = user_service.authenticate(email, password)
    except UserInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user)
    }), 200
