"""
Service de Relatórios. A versão original buscava todas as tasks de cada usuário dentro de um
loop (N+1). Aqui, usamos agregação no banco em vez de iterar em Python quando possível.
"""
from datetime import timedelta
from utils.helpers import utcnow

from database import db
from models.task import Task
from models.user import User
from models.category import Category


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = dict(
        db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
    )
    priority_counts = dict(
        db.session.query(Task.priority, db.func.count(Task.id)).group_by(Task.priority).all()
    )

    all_tasks = Task.query.all()
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (utcnow() - t.due_date).days,
        }
        for t in all_tasks
        if t.is_overdue()
    ]

    seven_days_ago = utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done', Task.updated_at >= seven_days_ago
    ).count()

    users = User.query.all()
    task_counts_by_user = dict(
        db.session.query(Task.user_id, db.func.count(Task.id)).group_by(Task.user_id).all()
    )
    done_counts_by_user = dict(
        db.session.query(Task.user_id, db.func.count(Task.id))
        .filter(Task.status == 'done')
        .group_by(Task.user_id)
        .all()
    )
    user_stats = []
    for u in users:
        total = task_counts_by_user.get(u.id, 0)
        completed = done_counts_by_user.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
        })

    return {
        'generated_at': str(utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'done': status_counts.get('done', 0),
            'cancelled': status_counts.get('cancelled', 0),
        },
        'tasks_by_priority': {
            'critical': priority_counts.get(1, 0),
            'high': priority_counts.get(2, 0),
            'medium': priority_counts.get(3, 0),
            'low': priority_counts.get(4, 0),
            'minimal': priority_counts.get(5, 0),
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    overdue = 0
    high_priority = 0

    for t in tasks:
        counts[t.status] = counts.get(t.status, 0) + 1
        if t.priority <= 2:
            high_priority += 1
        if t.is_overdue():
            overdue += 1

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': counts['done'],
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'cancelled': counts['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((counts['done'] / total) * 100, 2) if total > 0 else 0,
        },
    }
