from flask import Flask, jsonify
from models.user import User
from flask_cors import CORS
from config import configure
from middleware.access_control import require_identity
from werkzeug.exceptions import HTTPException
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
import os, datetime
import click

app = Flask(__name__)

configure(app)

CORS(app)
db.init_app(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)

app.before_request(require_identity)

@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, HTTPException):
        return jsonify({'error': error.description}), error.code
    db.session.rollback()
    app.logger.error('Falha interna ao processar requisição')
    return jsonify({'error': 'Erro interno'}), 500

@app.cli.command('bootstrap-admin')
def bootstrap_admin():
    if User.query.filter_by(role='admin').first():
        raise click.ClickException('Já existe um administrador')
    email = os.environ.get('TASK_ADMIN_EMAIL')
    password = os.environ.get('TASK_ADMIN_PASSWORD')
    name = os.environ.get('TASK_ADMIN_NAME')
    if not email or not password or len(password) < 4 or not name:
        raise click.ClickException('Informe TASK_ADMIN_EMAIL, TASK_ADMIN_PASSWORD e TASK_ADMIN_NAME')
    if User.query.filter_by(email=email).first():
        raise click.ClickException('Email já cadastrado')
    user = User(email=email, name=name, role='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo('Administrador criado')

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}

@app.cli.command('init-db')
def init_db():
    db.create_all()
    click.echo('Tabelas inicializadas')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='127.0.0.1', port=5000)
