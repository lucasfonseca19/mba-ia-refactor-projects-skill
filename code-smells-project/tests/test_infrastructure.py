"""Verificações de configuração, recursos e migração com SQLite real."""
from pathlib import Path
from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from database import get_db, init_db, migrate_plaintext_passwords
from models.orders import list_orders
from werkzeug.security import check_password_hash


class InfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="infra-009-")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name)/"test.db")
        self.app = create_app({"TESTING":True,"DATABASE_PATH":self.path,"SECRET_KEY":"synthetic-009"})

    def test_factory_and_import_do_not_initialize_database(self):
        self.assertFalse(Path(self.path).exists())
        with self.app.app_context():
            init_db()
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],0)

    def test_config_requires_database_and_secret_and_defaults_to_safe_flags(self):
        with patch.dict(os.environ,{},clear=True):
            for config in ({},{"DATABASE_PATH":self.path},{"SECRET_KEY":"synthetic"}):
                with self.assertRaises(RuntimeError):
                    create_app(config)
            app = create_app({"DATABASE_PATH":self.path,"SECRET_KEY":"synthetic"})
            self.assertFalse(app.debug)
            self.assertFalse(app.config["ADMIN_TOOLS_ENABLED"])
            self.assertTrue(app.config["SESSION_COOKIE_SECURE"])
            self.assertTrue(app.config["SESSION_COOKIE_HTTPONLY"])
            self.assertEqual(app.config["SESSION_COOKIE_SAMESITE"],"Lax")

    def test_connection_is_closed_on_context_exit_in_success_and_failure(self):
        connections=[]
        for fails in (False,True):
            try:
                with self.app.app_context():
                    db=get_db()
                    connections.append(db)
                    db.execute("CREATE TABLE IF NOT EXISTS scratch(id INTEGER)")
                    db.execute("INSERT INTO scratch VALUES(1)")
                    if fails:
                        raise RuntimeError("synthetic")
            except RuntimeError:
                pass
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")
        self.assertIsNot(connections[0],connections[1])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM scratch").fetchone()[0],0)

    def test_order_queries_do_not_grow_with_orders_or_items(self):
        with self.app.app_context():
            init_db()
            db=get_db()
            counts=[]
            for count in (0,1,10):
                with db:
                    db.execute("DELETE FROM itens_pedido")
                    db.execute("DELETE FROM pedidos")
                    for number in range(count):
                        db.execute("INSERT INTO pedidos(id,usuario_id,total) VALUES(?,2,100)",(number+1,))
                        db.executemany("INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(?,1,1,20)",[(number+1,)]*5)
                for user_id in (None,2):
                    statements=[]
                    db.set_trace_callback(statements.append)
                    orders=list_orders(user_id)
                    db.set_trace_callback(None)
                    self.assertEqual(len(orders),count)
                    self.assertEqual(sum(len(items) for _,items in orders),count*5)
                    counts.append(sum(sql.lstrip().upper().startswith("SELECT") for sql in statements))
            self.assertEqual(counts,[2]*6)

    def test_plaintext_migration_preserves_login_is_idempotent_and_handles_hashlike_password(self):
        with self.app.app_context():
            init_db()
            db=get_db()
            with db:
                db.executemany("INSERT INTO usuarios(nome,email,senha) VALUES(?,?,?)",[
                    ("Pessoa","one@example.test","synthetic-password"),
                    ("Pessoa","two@example.test","scrypt:not-a-hash"),
                ])
            self.assertEqual(migrate_plaintext_passwords(),2)
            first=[row[0] for row in db.execute("SELECT senha FROM usuarios ORDER BY id")]
            self.assertTrue(check_password_hash(first[0],"synthetic-password"))
            self.assertTrue(check_password_hash(first[1],"scrypt:not-a-hash"))
            self.assertEqual(migrate_plaintext_passwords(),0)
            self.assertEqual([row[0] for row in db.execute("SELECT senha FROM usuarios ORDER BY id")],first)

    def test_invalid_legacy_record_rolls_back_all_password_updates(self):
        with self.app.app_context():
            init_db()
            db=get_db()
            with db:
                db.executemany("INSERT INTO usuarios(nome,email,senha) VALUES(?,?,?)",[
                    ("Pessoa","one@example.test","synthetic-password"),("Pessoa","two@example.test",None)])
            with self.assertRaises(ValueError):
                migrate_plaintext_passwords()
            self.assertEqual(db.execute("SELECT senha FROM usuarios WHERE id=1").fetchone()[0],"synthetic-password")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0],0)

    def test_cli_init_and_migration_require_explicit_operator_intent(self):
        runner=self.app.test_cli_runner()
        self.assertEqual(runner.invoke(args=["init-db"]).exit_code,0)
        self.assertNotEqual(runner.invoke(args=["migrate-passwords"]).exit_code,0)
        self.assertEqual(runner.invoke(args=["migrate-passwords","--from-plaintext"]).exit_code,0)

    def test_rules_can_run_without_http_or_database(self):
        from models.products import validate_product
        from models.orders import validate_items
        self.assertEqual(validate_product({"nome":"Produto","preco":0,"estoque":0}), ("Produto","",0,0,"geral"))
        self.assertEqual(validate_items([{"produto_id":1,"quantidade":2}]*2),{1:4})

    def test_cli_create_admin_stores_hash_and_can_authenticate(self):
        runner=self.app.test_cli_runner()
        self.assertEqual(runner.invoke(args=["init-db"]).exit_code,0)
        with patch("database.getpass.getpass",return_value="synthetic-password"):
            result=runner.invoke(args=["create-admin","--nome","Admin Teste","--email","cli@example.test"])
        self.assertEqual(result.exit_code,0,result.output)
        response=self.app.test_client().post("/login",json={"email":"cli@example.test","senha":"synthetic-password"})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json["dados"]["tipo"],"admin")
        with closing(sqlite3.connect(self.path)) as db:
            self.assertTrue(check_password_hash(db.execute("SELECT senha FROM usuarios").fetchone()[0],"synthetic-password"))
