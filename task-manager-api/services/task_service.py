"""
Service de Task — concentra a lógica de negócio que antes estava espalhada e duplicada
dentro das rotas (cálculo de "overdue" reimplementado 3 vezes, validação inconsistente,
queries N+1 ao montar a listagem com nome de usuário/categoria).
"""
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import process_task_data, utcnow

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']


def _serialize_with_relations(task, users_by_id, categories_by_id):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()

    user = users_by_id.get(task.user_id) if task.user_id else None
    data['user_name'] = user.name if user else None

    category = categories_by_id.get(task.category_id) if task.category_id else None
    data['category_name'] = category.name if category else None

    return data


def _batch_lookup(model, ids):
    """Busca múltiplos registros em uma única query (evita N+1). Retorna dict {id: registro}."""
    ids = {i for i in ids if i is not None}
    if not ids:
        return {}
    rows = model.query.filter(model.id.in_(ids)).all()
    return {row.id: row for row in rows}


def list_tasks():
    tasks = Task.query.all()
    users_by_id = _batch_lookup(User, (t.user_id for t in tasks))
    categories_by_id = _batch_lookup(Category, (t.category_id for t in tasks))
    return [_serialize_with_relations(t, users_by_id, categories_by_id) for t in tasks]


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def create_task(payload):
    parsed, error = process_task_data(payload)
    if error:
        return None, error
    if 'title' not in parsed:
        return None, 'Título é obrigatório'

    if payload.get('user_id'):
        if not User.query.get(payload['user_id']):
            return None, 'Usuário não encontrado'
    if payload.get('category_id'):
        if not Category.query.get(payload['category_id']):
            return None, 'Categoria não encontrada'

    task = Task()
    task.title = parsed['title']
    task.description = parsed.get('description', '')
    task.status = parsed.get('status', 'pending')
    task.priority = parsed.get('priority', 3)
    task.user_id = payload.get('user_id')
    task.category_id = payload.get('category_id')
    task.due_date = parsed.get('due_date')
    task.tags = parsed.get('tags')

    db.session.add(task)
    db.session.commit()
    return task.to_dict(), None


def update_task(task_id, payload):
    task = Task.query.get(task_id)
    if not task:
        return None, 'Task não encontrada', 404

    parsed, error = process_task_data(payload)
    if error:
        return None, error, 400

    if 'user_id' in payload and payload['user_id']:
        if not User.query.get(payload['user_id']):
            return None, 'Usuário não encontrado', 404
    if 'category_id' in payload and payload['category_id']:
        if not Category.query.get(payload['category_id']):
            return None, 'Categoria não encontrada', 404

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in parsed:
            setattr(task, field, parsed[field])
    if 'user_id' in payload:
        task.user_id = payload['user_id']
    if 'category_id' in payload:
        task.category_id = payload['category_id']

    task.updated_at = utcnow()
    db.session.commit()
    return task.to_dict(), None, 200


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return False
    db.session.delete(task)
    db.session.commit()
    return True


def search_tasks(query, status, priority, user_id):
    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%'))
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return [t.to_dict() for t in tasks.all()]


def get_stats():
    total = Task.query.count()
    all_tasks = Task.query.all()
    overdue_count = sum(1 for t in all_tasks if t.is_overdue())

    return {
        'total': total,
        'pending': Task.query.filter_by(status='pending').count(),
        'in_progress': Task.query.filter_by(status='in_progress').count(),
        'done': Task.query.filter_by(status='done').count(),
        'cancelled': Task.query.filter_by(status='cancelled').count(),
        'overdue': overdue_count,
        'completion_rate': round((Task.query.filter_by(status='done').count() / total) * 100, 2) if total > 0 else 0,
    }


def get_user_tasks(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all()
    result = []
    for t in tasks:
        data = t.to_dict()
        data['overdue'] = t.is_overdue()
        result.append(data)
    return result
