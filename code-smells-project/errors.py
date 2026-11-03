"""Erros de domínio e tradução segura no limite HTTP."""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status
        super().__init__(message)


def register_errors(app):
    @app.errorhandler(ApiError)
    def domain_error(error):
        return jsonify(erro=error.message, sucesso=False), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {400:"Dados inválidos",404:"Recurso não encontrado",405:"Método não permitido",
                    413:"Corpo da requisição muito grande",415:"Envie um objeto JSON"}
        status = 400 if error.code == 415 else error.code
        return jsonify(erro=messages.get(error.code, "Requisição inválida"), sucesso=False), status

    @app.errorhandler(Exception)
    def internal_error(error):
        # Não registrar SQL, parâmetros, corpos ou mensagens que possam ter segredos.
        app.logger.error("Falha interna (%s)", type(error).__name__)
        return jsonify(erro="Falha interna", sucesso=False), 500
