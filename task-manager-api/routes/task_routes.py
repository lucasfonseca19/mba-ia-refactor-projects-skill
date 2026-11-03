from flask import Blueprint, request, jsonify, g
from database import db
from services import task_service
from services.task_service import TaskInputError


task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_service.list_tasks(g.user)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = task_service.find_task(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return jsonify(data), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    try:
        task = task_service.create_task(request.get_json(silent=True))
        return jsonify(task.to_dict()), 201
    except TaskInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = task_service.find_task(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    try:
        task = task_service.update_task(task, request.get_json(silent=True))
        return jsonify(task.to_dict()), 200
    except TaskInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), exc.status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = task_service.find_task(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    task_service.delete_task(task)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    try:
        return jsonify(task_service.search_tasks(g.user, request.args)), 200
    except TaskInputError as exc:
        return jsonify({'error': str(exc)}), exc.status


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_service.task_stats(g.user)), 200
