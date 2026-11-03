"""Credenciais ficam no Model e nunca integram a representação pública."""
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db
from errors import ApiError


def required_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ApiError(f"{label} é obrigatório")
    return value


def find_user(user_id):
    return get_db().execute("SELECT * FROM usuarios WHERE id=?", (user_id,)).fetchone()


def list_users():
    return get_db().execute("SELECT * FROM usuarios ORDER BY id").fetchall()


def create_user(name, email, password, role="cliente"):
    for value, label in ((name,"Nome"),(email,"Email"),(password,"Senha")):
        required_text(value,label)
    db = get_db()
    with db:
        cursor = db.execute("INSERT INTO usuarios(nome,email,senha,tipo) VALUES(?,?,?,?)",
                            (name,email,generate_password_hash(password,method="scrypt"),role))
    return cursor.lastrowid


def authenticate(email, password):
    required_text(email,"Email")
    required_text(password,"Senha")
    # O legado admite emails duplicados: preservar a busca por credenciais,
    # sem descartar contas posteriores nem inventar unicidade nesta etapa.
    users = get_db().execute("SELECT * FROM usuarios WHERE email=? ORDER BY id", (email,)).fetchall()
    for user in users:
        try:
            valid = check_password_hash(user["senha"],password)
        except (ValueError,TypeError):
            valid = False
        if valid:
            return user
    return None
