from datetime import timedelta
from sqlalchemy import func, case
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.time_utils import utc_now

def summary_report():

    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    all_tasks = Task.query.all()
    overdue_count = 0
    overdue_list = []
    for t in all_tasks:
        if t.is_overdue():
            overdue_count += 1
            overdue_list.append({
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (utc_now() - t.due_date).days,
            })

    seven_days_ago = utc_now() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()

    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
    ).count()

    users = (db.session.query(User, func.count(Task.id),
                 func.coalesce(func.sum(case((Task.status == 'done', 1), else_=0)), 0))
             .outerjoin(Task, Task.user_id == User.id).group_by(User.id).all())
    user_stats = []
    for user, total, completed in users:
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total else 0,
        })

    report = {
        'generated_at': str(utc_now()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
        'overdue': {
            'count': overdue_count,
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return report

def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return None

    tasks = Task.query.filter_by(user_id=user_id).all()

    total = len(tasks)
    done = 0
    pending = 0
    in_progress = 0
    cancelled = 0
    overdue = 0
    high_priority = 0

    for t in tasks:
        if t.status == 'done':
            done = done + 1
        elif t.status == 'pending':
            pending = pending + 1
        elif t.status == 'in_progress':
            in_progress = in_progress + 1
        elif t.status == 'cancelled':
            cancelled = cancelled + 1

        if t.priority <= 2:
            high_priority = high_priority + 1

        if t.is_overdue():
            overdue += 1

    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
        }
    }

    return report

def get_categories(user_id=None):
    on_clause = Task.category_id == Category.id
    if user_id is not None:
        on_clause = on_clause & (Task.user_id == user_id)
    categories = db.session.query(Category, func.count(Task.id)).outerjoin(Task, on_clause).group_by(Category.id).all()
    result = []
    for c, task_count in categories:
        cat_data = c.to_dict()
        cat_data['task_count'] = task_count
        result.append(cat_data)
    return result
