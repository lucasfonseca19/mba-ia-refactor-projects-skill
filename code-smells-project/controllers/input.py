"""Adaptação de entrada HTTP, separada das regras do domínio."""
import math
from flask import request
from errors import ApiError


def json_object():
    data = request.get_json()
    if not isinstance(data,dict):
        raise ApiError("Dados inválidos")
    return data


def optional_number(name):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (ValueError,OverflowError):
        raise ApiError("Filtro de preço inválido") from None
    if not math.isfinite(value):
        raise ApiError("Filtro de preço inválido")
    return value
