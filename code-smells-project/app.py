"""Entrada e composição da API; importar este módulo não abre o banco."""
from flask import Flask
from flask_cors import CORS
from config import load_config
from database import register_database
from errors import register_errors
from routes import register_routes
from security import register_security


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(load_config(config))
    register_database(app)
    register_errors(app)
    register_security(app)
    register_routes(app)
    if app.config["CORS_ORIGINS"]:
        CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
