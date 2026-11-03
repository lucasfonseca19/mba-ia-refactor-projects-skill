from datetime import datetime
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.time_utils import utc_now

from utils.helpers import VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, DEFAULT_PRIORITY, MAX_DATABASE_INTEGER


class TaskInputError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _apply(task, data, create=False):
    if not isinstance(data, dict) or not data:
        raise TaskInputError('Dados inválidos')
    if create and not data.get('title'):
        raise TaskInputError('Título é obrigatório')
    if 'title' in data:
        title = data['title']
        if not isinstance(title, str) or len(title) < MIN_TITLE_LENGTH:
            raise TaskInputError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise TaskInputError('Título muito longo')
        task.title = title
    status = data.get('status', 'pending' if create else task.status)
    if not isinstance(status, str) or status not in VALID_STATUSES:
        raise TaskInputError('Status inválido')
    task.status = status
    priority = data.get('priority', DEFAULT_PRIORITY if create else task.priority)
    if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 5:
        raise TaskInputError('Prioridade deve ser entre 1 e 5')
    task.priority = priority
    if 'description' in data or create:
        description = data.get('description', '')
        if description is not None and not isinstance(description, str):
            raise TaskInputError('Descrição inválida')
        task.description = description
    for key, model, label in [('user_id', User, 'Usuário'), ('category_id', Category, 'Categoria')]:
        if key in data:
            value = data[key]
            if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
                raise TaskInputError(f'{label} inválido')
            if value is not None and not 0 < value <= MAX_DATABASE_INTEGER:
                raise TaskInputError(f'{label} inválido')
            if value is not None and not db.session.get(model, value):
                raise TaskInputError(f'{label} não encontrado', 404)
            setattr(task, key, value)
    if 'due_date' in data:
        if data['due_date'] is not None and not isinstance(data['due_date'], str):
            raise TaskInputError('Formato de data inválido. Use YYYY-MM-DD')
        try:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d') if data['due_date'] else None
        except (ValueError, TypeError):
            raise TaskInputError('Formato de data inválido. Use YYYY-MM-DD') from None
    if 'tags' in data:
        tags = data['tags']
        if isinstance(tags, list):
            if not all(isinstance(tag, str) for tag in tags):
                raise TaskInputError('Tags inválidas')
            task.tags = ','.join(tags)
        elif tags is None or isinstance(tags, str):
            task.tags = tags
        else:
            raise TaskInputError('Tags inválidas')
    if not create:
        task.updated_at = utc_now()
    return task


def create_task(data):
    task = _apply(Task(), data, create=True)
    db.session.add(task)
    db.session.commit()
    return task


def update_task(task, data):
    _apply(task, data)
    db.session.commit()
    return task


def visible_tasks(viewer):
    query = Task.query
    return query if viewer.role in {'admin', 'manager'} else query.filter_by(user_id=viewer.id)


def list_tasks(viewer):
    from sqlalchemy.orm import joinedload
    tasks = visible_tasks(viewer).options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for task in tasks:
        data = task.to_dict()
        data.update(overdue=task.is_overdue(), user_name=task.user.name if task.user else None,
                    category_name=task.category.name if task.category else None)
        result.append(data)
    return result


def find_task(task_id):
    return db.session.get(Task, task_id)


def delete_task(task):
    db.session.delete(task)
    db.session.commit()


def search_tasks(viewer, filters):
    tasks = visible_tasks(viewer)
    if filters.get('q'):
        value = f"%{filters['q']}%"
        tasks = tasks.filter(db.or_(Task.title.like(value), Task.description.like(value)))
    if filters.get('status'):
        tasks = tasks.filter(Task.status == filters['status'])
    for key in ('priority', 'user_id'):
        value = filters.get(key)
        if value:
            if not value.isascii() or not value.isdecimal():
                raise TaskInputError('Prioridade inválida' if key == 'priority' else 'Usuário inválido')
            digits = value.lstrip('0') or '0'
            if len(digits) > 19 or int(digits) > MAX_DATABASE_INTEGER:
                raise TaskInputError('Prioridade inválida' if key == 'priority' else 'Usuário inválido')
            tasks = tasks.filter(getattr(Task, key) == int(digits))
    return [task.to_dict() for task in tasks.all()]


def task_stats(viewer):
    tasks = visible_tasks(viewer).all()
    total = len(tasks)
    counts = {status: sum(task.status == status for task in tasks) for status in VALID_STATUSES}
    return {
        'total': total,
        **counts,
        'overdue': sum(task.is_overdue() for task in tasks),
        'completion_rate': round(counts['done'] / total * 100, 2) if total else 0,
    }
