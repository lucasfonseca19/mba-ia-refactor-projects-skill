from flask import request, jsonify, g, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature
from database import db
from models.user import User
from models.task import Task
from services.auth_tokens import matches_user
from utils.helpers import MAX_DATABASE_INTEGER


def require_identity():
    if request.method in {'POST', 'PUT'} and not isinstance(request.get_json(silent=True), dict):
        return jsonify({'error': 'Dados inválidos'}), 400
    if request.method == 'OPTIONS' or request.endpoint in {'health', 'index', 'users.login'}:
        return None
    if request.endpoint == 'users.create_user':
        role = request.get_json(silent=True).get('role', 'user')
        if role == 'user' or not request.headers.get('Authorization'):
            return None
    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer '):
        return jsonify({'error': 'Autenticação necessária'}), 401
    try:
        payload = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='task-auth').loads(authorization[7:], max_age=3600)
        user = db.session.get(User, payload['user_id'])
    except (BadSignature, KeyError, TypeError, ValueError):
        user = None
    if not user or not user.active or not matches_user(payload, user):
        return jsonify({'error': 'Credencial inválida'}), 401
    g.user = user
    endpoint = request.endpoint or ''
    method = 'GET' if request.method == 'HEAD' else request.method
    values = request.view_args or {}
    if any(isinstance(value, int) and value > MAX_DATABASE_INTEGER for value in values.values()):
        return jsonify({'error': 'Identificador inválido'}), 400
    if user.role == 'admin':
        return None
    allowed = False
    if endpoint in {'users.get_user', 'users.get_user_tasks'} and method == 'GET':
        allowed = user.role == 'manager' or values.get('user_id') == user.id
    elif endpoint == 'users.get_users' and method == 'GET':
        allowed = user.role == 'manager'
    elif endpoint == 'users.update_user' and method == 'PUT':
        data = request.get_json(silent=True)
        allowed = values.get('user_id') == user.id and not bool({'role', 'active'} & data.keys())
    elif endpoint == 'reports.summary_report' and method == 'GET':
        allowed = user.role == 'manager'
    elif endpoint == 'reports.user_report' and method == 'GET':
        allowed = user.role == 'manager' or values.get('user_id') == user.id
    elif endpoint == 'reports.get_categories' and method == 'GET':
        allowed = True
    elif endpoint in {'tasks.get_tasks', 'tasks.get_task', 'tasks.search_tasks', 'tasks.task_stats', 'tasks.create_task', 'tasks.update_task', 'tasks.delete_task'}:
        if user.role == 'manager':
            allowed = method == 'GET'
        elif user.role == 'user':
            allowed = method in {'GET', 'POST', 'PUT', 'DELETE'}
            task_id = values.get('task_id')
            if task_id is not None:
                task = db.session.get(Task, task_id)
                allowed = task is None or task.user_id == user.id
            if method in {'POST', 'PUT'}:
                data = request.get_json(silent=True)
                if 'user_id' in data and data['user_id'] != user.id:
                    allowed = False
                if method == 'POST' and 'user_id' not in data:
                    data['user_id'] = user.id
    if not allowed:
        return jsonify({'error': 'Acesso negado'}), 403
