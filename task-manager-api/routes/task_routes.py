"""
Camada de Routes — apenas parse de request e delegação ao service. Nenhuma regra de negócio
ou acesso a dado deve existir aqui (ver services/task_service.py).
"""
from flask import Blueprint, request, jsonify

from services import task_service

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_service.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    data = task_service.get_task(task_id)
    if data is None:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(data), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    task, error = task_service.create_task(data)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(task), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    task, error, status = task_service.update_task(task_id, data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(task), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if not task_service.delete_task(task_id):
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    result = task_service.search_tasks(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_service.get_stats()), 200
