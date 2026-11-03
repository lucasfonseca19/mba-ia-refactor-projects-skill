import os


def configure(app):
    secret = os.environ.get('TASK_SECRET_KEY')
    if not secret:
        raise RuntimeError('TASK_SECRET_KEY é obrigatória')
    app.config['SECRET_KEY'] = secret
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TASK_DATABASE_URI', 'sqlite:///tasks.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
