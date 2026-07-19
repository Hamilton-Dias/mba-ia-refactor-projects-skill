"""Camada de Routes de Usuário — apenas parse de request e delegação ao service."""
from flask import Blueprint, request, jsonify

from services import user_service, task_service

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_service.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    data = user_service.get_user_with_tasks(user_id)
    if data is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(data), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    user, error = user_service.create_user(data)
    if error:
        status = 409 if error == 'Email já cadastrado' else 400
        return jsonify({'error': error}), status
    return jsonify(user), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    user, error, status = user_service.update_user(user_id, data)
    if error:
        return jsonify({'error': error}), status
    return jsonify(user), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not user_service.delete_user(user_id):
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    user = user_service.get_user_with_tasks(user_id)
    if user is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(task_service.get_user_tasks(user_id)), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user, error = user_service.authenticate(email, password)
    if error:
        status = 403 if error == 'Usuário inativo' else 401
        return jsonify({'error': error}), status

    # NOTA (ver relatório de auditoria): o token retornado é um mock, não um JWT real.
    # Implementar autenticação baseada em JWT de verdade está fora do escopo desta
    # refatoração de arquitetura MVC e é documentado como risco residual.
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': f'mock-token-{user.id}',
    }), 200
