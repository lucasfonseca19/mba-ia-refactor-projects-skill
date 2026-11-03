import re
from database import db
from models.user import User

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH


class UserInputError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _apply(user, data, create=False):
    if not isinstance(data, dict) or not data:
        raise UserInputError('Dados inválidos')
    if create and not data.get('name'):
        raise UserInputError('Nome é obrigatório')
    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name']:
            raise UserInputError('Nome é obrigatório')
        user.name = data['name']
    if create and not data.get('email'):
        raise UserInputError('Email é obrigatório')
    if 'email' in data:
        email = data['email']
        if not isinstance(email, str) or not EMAIL_PATTERN.fullmatch(email):
            raise UserInputError('Email inválido')
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            raise UserInputError('Email já cadastrado', 409)
        user.email = email
    if create and not data.get('password'):
        raise UserInputError('Senha é obrigatória')
    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise UserInputError('Senha deve ter no mínimo 4 caracteres')
        user.set_password(password)
    role = data.get('role', 'user' if create else user.role)
    if not isinstance(role, str) or role not in VALID_ROLES:
        raise UserInputError('Role inválido')
    user.role = role
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise UserInputError('Estado inválido')
        user.active = data['active']
    return user


def create_user(data):
    user = _apply(User(), data, create=True)
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user, data):
    _apply(user, data)
    db.session.commit()
    return user


def find_user(user_id):
    return db.session.get(User, user_id)


def list_users():
    from sqlalchemy import func
    from models.task import Task
    users = db.session.query(User, func.count(Task.id)).outerjoin(Task, Task.user_id == User.id).group_by(User.id).all()
    return [dict(user.to_dict(), task_count=count) for user, count in users]


def user_with_tasks(user):
    from models.task import Task
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user.id).all()]
    return data


def user_tasks(user):
    from models.task import Task
    result = []
    for task in Task.query.filter_by(user_id=user.id).all():
        data = {key: value for key, value in task.to_dict().items()
                if key in {'id', 'title', 'description', 'status', 'priority', 'created_at', 'due_date'}}
        data['overdue'] = task.is_overdue()
        result.append(data)
    return result


def delete_user(user):
    from models.task import Task
    for task in Task.query.filter_by(user_id=user.id).all():
        db.session.delete(task)
    db.session.delete(user)
    db.session.commit()


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UserInputError('Credenciais inválidas', 401)
    if not user.active:
        raise UserInputError('Usuário inativo', 403)
    db.session.commit()
    return user
