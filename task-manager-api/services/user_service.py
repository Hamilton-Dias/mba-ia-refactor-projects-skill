"""Service de Usuário — cadastro, atualização e autenticação."""
import re

from database import db
from models.user import User
from models.task import Task

VALID_ROLES = ['user', 'admin', 'manager']
EMAIL_RE = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'


def list_users():
    users = User.query.all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = len(u.tasks)
        result.append(data)
    return result


def get_user_with_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return None
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(payload):
    name = payload.get('name')
    email = payload.get('email')
    password = payload.get('password')
    role = payload.get('role', 'user')

    if not name:
        return None, 'Nome é obrigatório'
    if not email:
        return None, 'Email é obrigatório'
    if not password:
        return None, 'Senha é obrigatória'
    if not re.match(EMAIL_RE, email):
        return None, 'Email inválido'
    if len(password) < 4:
        return None, 'Senha deve ter no mínimo 4 caracteres'
    if User.query.filter_by(email=email).first():
        return None, 'Email já cadastrado'
    if role not in VALID_ROLES:
        return None, 'Role inválido'

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    db.session.add(user)
    db.session.commit()
    return user.to_dict(), None


def update_user(user_id, payload):
    user = User.query.get(user_id)
    if not user:
        return None, 'Usuário não encontrado', 404

    if 'name' in payload:
        user.name = payload['name']

    if 'email' in payload:
        if not re.match(EMAIL_RE, payload['email']):
            return None, 'Email inválido', 400
        existing = User.query.filter_by(email=payload['email']).first()
        if existing and existing.id != user_id:
            return None, 'Email já cadastrado', 409
        user.email = payload['email']

    if 'password' in payload:
        if len(payload['password']) < 4:
            return None, 'Senha muito curta', 400
        user.set_password(payload['password'])

    if 'role' in payload:
        if payload['role'] not in VALID_ROLES:
            return None, 'Role inválido', 400
        user.role = payload['role']

    if 'active' in payload:
        user.active = payload['active']

    db.session.commit()
    return user.to_dict(), None, 200


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False

    # Remove as tasks relacionadas para não deixar registros órfãos.
    for task in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(task)

    db.session.delete(user)
    db.session.commit()
    return True


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None, 'Credenciais inválidas'
    if not user.active:
        return None, 'Usuário inativo'
    return user, None
