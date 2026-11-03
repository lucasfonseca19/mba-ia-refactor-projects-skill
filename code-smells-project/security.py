"""Identidade assinada, autorização atualizada no banco e token CSRF por sessão."""
from functools import wraps
import secrets
from flask import current_app, g, request, session
from errors import ApiError
from models.users import find_user


def register_security(app):
    @app.before_request
    def check_origin():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("Origin")
            allowed = [request.host_url.rstrip("/"), *current_app.config["CORS_ORIGINS"]]
            if origin and origin not in allowed:
                raise ApiError("Origem não permitida", 403)

    @app.after_request
    def private_responses(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


def login_required(admin=False):
    def decorate(handler):
        @wraps(handler)
        def guarded(*args, **kwargs):
            uid = session.get("user_id")
            user = find_user(uid) if type(uid) is int else None
            if user is None:
                session.clear()
                raise ApiError("Autenticação necessária", 401)
            g.actor = user
            if admin and user["tipo"] != "admin":
                raise ApiError("Permissão insuficiente", 403)
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                token, expected = request.headers.get("X-CSRF-Token", ""), session.get("csrf_token", "")
                if not token or not expected or not secrets.compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
                    raise ApiError("Token CSRF inválido", 403)
            return handler(*args, **kwargs)
        return guarded
    return decorate


def require_owner(user_id):
    if g.actor["tipo"] != "admin" and g.actor["id"] != user_id:
        raise ApiError("Permissão insuficiente", 403)


def establish_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["csrf_token"] = secrets.token_urlsafe(32)
    session.permanent = True
    return session["csrf_token"]
