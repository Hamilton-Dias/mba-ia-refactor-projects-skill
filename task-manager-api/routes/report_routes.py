"""Camada de Routes de Relatórios/Categorias — apenas parse de request e delegação ao service."""
from flask import Blueprint, request, jsonify

from services import report_service, category_service

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_service.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    data = report_service.user_report(user_id)
    if data is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(data), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_service.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    category, error = category_service.create_category(data)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(category), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    category, error, status = category_service.update_category(cat_id, data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(category), status


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    if not category_service.delete_category(cat_id):
        return jsonify({'error': 'Categoria não encontrada'}), 404
    return jsonify({'message': 'Categoria deletada'}), 200
