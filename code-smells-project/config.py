"""Configuração operacional explícita, sem credenciais de exemplo."""
import os
from datetime import timedelta


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    if value.lower() not in ("true", "false", "1", "0"):
        raise RuntimeError(f"Configuração inválida: {name}")
    return value.lower() in ("true", "1")


def load_config(overrides=None):
    config = {
        "DATABASE_PATH": os.environ.get("DATABASE_PATH"),
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "DEBUG": env_bool("DEBUG"),
        "ADMIN_TOOLS_ENABLED": env_bool("ADMIN_TOOLS_ENABLED"),
        "SESSION_COOKIE_SECURE": env_bool("SESSION_COOKIE_SECURE", True),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "CORS_ORIGINS": [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()],
        "MAX_CONTENT_LENGTH": 1024 * 1024,
    }
    config.update(overrides or {})
    for key in ("DATABASE_PATH", "SECRET_KEY"):
        if not isinstance(config[key], str) or not config[key].strip():
            raise RuntimeError(f"Configuração obrigatória ausente: {key}")
    if "*" in config["CORS_ORIGINS"]:
        raise RuntimeError("CORS_ORIGINS deve conter origens explícitas")
    return config
