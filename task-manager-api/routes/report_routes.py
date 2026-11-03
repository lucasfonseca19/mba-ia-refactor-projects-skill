from flask import Blueprint, request, jsonify, g
from database import db
from services import report_service, category_service

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_service.summary_report()), 200

@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    report = report_service.user_report(user_id)
    if report is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(report), 200

@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(report_service.get_categories(g.user.id if g.user.role == 'user' else None)), 200

@report_bp.route('/categories', methods=['POST'])
def create_category():
    try:
        category = category_service.create_category(request.get_json(silent=True))
        return jsonify(category.to_dict()), 201
    except category_service.CategoryInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400

@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    category = category_service.find_category(cat_id)
    if not category:
        return jsonify({'error': 'Categoria não encontrada'}), 404
    try:
        category_service.update_category(category, request.get_json(silent=True))
        return jsonify(category.to_dict()), 200
    except category_service.CategoryInputError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400

@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    category = category_service.find_category(cat_id)
    if not category:
        return jsonify({'error': 'Categoria não encontrada'}), 404
    category_service.delete_category(category)
    return jsonify({'message': 'Categoria deletada'}), 200
