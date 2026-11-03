"""Conexão por requisição; esquema e migração somente por comandos explícitos."""
import getpass
import sqlite3
import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, descricao TEXT,
    preco REAL, estoque INTEGER, categoria TEXT, ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT, senha TEXT,
    tipo TEXT DEFAULT 'cliente', criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER,
    status TEXT DEFAULT 'pendente', total REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER,
    produto_id INTEGER, quantidade INTEGER, preco_unitario REAL
);
CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"], timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().executescript(SCHEMA)


def migrate_plaintext_passwords():
    """Converter base declaradamente em texto puro, sem inferir por prefixo.

    Um marcador transacional evita converter hashes em senhas numa repetição.
    Execute antes de aceitar cadastros com hash nessa base legada.
    """
    db = get_db()
    with db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
        if db.execute("SELECT 1 FROM schema_migrations WHERE name=?", ("plaintext-passwords-v1",)).fetchone():
            return 0
        users = db.execute("SELECT id,senha FROM usuarios").fetchall()
        for user in users:
            if not isinstance(user["senha"], str) or not user["senha"]:
                raise ValueError("Credencial legada inválida; migração revertida")
            db.execute("UPDATE usuarios SET senha=? WHERE id=?", (generate_password_hash(user["senha"], method="scrypt"), user["id"]))
        db.execute("INSERT INTO schema_migrations(name) VALUES(?)", ("plaintext-passwords-v1",))
    return len(users)


def register_database(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_command():
        """Criar tabelas sem apagar dados nem semear usuários."""
        init_db()
        click.echo("Esquema inicializado, sem dados de exemplo.")

    @app.cli.command("migrate-passwords")
    @click.option("--from-plaintext", is_flag=True, required=True, help="Confirma o formato legado de toda a base.")
    def migrate_command(from_plaintext):
        """Converter uma base legada após backup e verificação em cópia."""
        count = migrate_plaintext_passwords()
        click.echo(f"Credenciais migradas: {count}")

    @app.cli.command("create-admin")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    def create_admin(nome, email):
        """Criar admin explicitamente; senha não passa por argumento ou log."""
        from models.users import create_user
        password = getpass.getpass("Senha: ")
        if password != getpass.getpass("Confirme a senha: "):
            raise click.ClickException("Senhas diferentes")
        create_user(nome, email, password, role="admin")
        click.echo("Administrador criado.")
