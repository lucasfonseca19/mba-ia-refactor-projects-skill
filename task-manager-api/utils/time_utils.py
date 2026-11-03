from datetime import datetime, timezone


def utc_now():
    """UTC sem fuso no limite de persistência SQLite legado."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
