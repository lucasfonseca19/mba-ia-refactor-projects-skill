"""Contratos e regressões com SQLite real e dados exclusivamente sintéticos."""
import concurrent.futures
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.environ.get("PROJECT_SOURCE", str(Path(__file__).resolve().parents[1])))
import app as application
from werkzeug.security import check_password_hash, generate_password_hash


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="api-009-")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "test.db")
        self.legacy = not hasattr(application, "create_app")
        if self.legacy:
            import database
            database.db_path = self.path
            database.db_connection = None
            database.get_db()
            self.addCleanup(lambda: database.db_connection.close())
            self.app = application.app
        else:
            self.app = application.create_app({
                "TESTING": True, "DATABASE_PATH": self.path,
                "SECRET_KEY": "synthetic-test-key-009", "ADMIN_TOOLS_ENABLED": True,
                "SESSION_COOKIE_SECURE": False,
            })
            with self.app.app_context():
                from database import init_db
                init_db()
        self.app.config["TESTING"] = True
        self.app.logger.disabled = True
        with closing(sqlite3.connect(self.path)) as db, db:
            for table in ("itens_pedido", "pedidos", "produtos", "usuarios"):
                db.execute(f"DELETE FROM {table}")
            password = "synthetic-password" if self.legacy else generate_password_hash("synthetic-password")
            db.executemany("INSERT INTO usuarios(id,nome,email,senha,tipo) VALUES(?,?,?,?,?)", [
                (1, "Administrador Teste", "admin@example.test", password, "admin"),
                (2, "Cliente Teste", "client@example.test", password, "cliente"),
                (3, "Outro Cliente", "other@example.test", password, "cliente"),
            ])
            db.executemany("INSERT INTO produtos(id,nome,descricao,preco,estoque,categoria) VALUES(?,?,?,?,?,?)", [
                (1, "Produto Teste", "Descrição", 20, 10, "geral"),
                (2, "Outro Produto", "Descrição", 50, 10, "livros"),
            ])
        self.client = self.app.test_client()
        self.headers = {}

    def sql(self, statement, parameters=()):
        with closing(sqlite3.connect(self.path)) as db, db:
            return db.execute(statement, parameters).fetchall()

    def login(self, email="admin@example.test", client=None):
        client = client or self.client
        response = client.post("/login", json={"email": email, "senha": "synthetic-password"})
        self.assertEqual(response.status_code, 200)
        headers = {"X-CSRF-Token": response.json.get("csrf_token", "")}
        if client is self.client:
            self.headers = headers
        return headers

    def order(self, items=None, user=2, client=None, headers=None):
        return (client or self.client).post("/pedidos", json={
            "usuario_id": user,
            "itens": items if items is not None else [{"produto_id": 1, "quantidade": 2}],
        }, headers=self.headers if headers is None else headers)

    def test_all_19_endpoints_preserve_successful_operations_and_persistence(self):
        self.login()
        product = {"nome": "Novo Produto", "preco": 30, "estoque": 7, "categoria": "geral"}
        responses = []
        def check(method, path, expected, body=None):
            response = self.client.open(path, method=method, json=body, headers=self.headers)
            self.assertEqual(response.status_code, expected, (method, path, response.json))
            responses.append((method, path))
            return response.json
        check("GET", "/", 200)
        check("GET", "/health", 200)
        self.assertEqual(len(check("GET", "/produtos", 200)["dados"]), 2)
        self.assertEqual(check("GET", "/produtos/busca?q=Outro&categoria=livros&preco_min=40&preco_max=60", 200)["total"], 1)
        self.assertEqual(check("GET", "/produtos/1", 200)["dados"]["preco"], 20)
        pid = check("POST", "/produtos", 201, product)["dados"]["id"]
        product["preco"] = 35
        check("PUT", f"/produtos/{pid}", 200, product)
        self.assertEqual(self.sql("SELECT preco FROM produtos WHERE id=?", (pid,)), [(35.0,)])
        check("DELETE", f"/produtos/{pid}", 200)
        self.assertEqual(self.sql("SELECT id FROM produtos WHERE id=?", (pid,)), [])
        self.assertEqual(len(check("GET", "/usuarios", 200)["dados"]), 3)
        self.assertEqual(check("GET", "/usuarios/2", 200)["dados"]["id"], 2)
        uid = check("POST", "/usuarios", 201, {"nome": "Nova Pessoa", "email": "new@example.test", "senha": "new-password"})["dados"]["id"]
        self.assertEqual(self.sql("SELECT nome FROM usuarios WHERE id=?", (uid,)), [("Nova Pessoa",)])
        # Login é contado separadamente porque já estabeleceu a sessão usada acima.
        responses.append(("POST", "/login"))
        order = check("POST", "/pedidos", 201, {"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 2}]})["dados"]
        self.assertEqual(order["total"], 40)
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(8,)])
        self.assertEqual(self.sql("SELECT quantidade,preco_unitario FROM itens_pedido WHERE pedido_id=?", (order["pedido_id"],)), [(2, 20.0)])
        self.assertEqual(len(check("GET", "/pedidos", 200)["dados"]), 1)
        self.assertEqual(check("GET", "/pedidos/usuario/2", 200)["dados"][0]["itens"][0]["produto_nome"], "Produto Teste")
        check("PUT", f"/pedidos/{order['pedido_id']}/status", 200, {"status": "aprovado"})
        self.assertEqual(self.sql("SELECT status FROM pedidos WHERE id=?", (order["pedido_id"],)), [("aprovado",)])
        report = check("GET", "/relatorios/vendas", 200)["dados"]
        self.assertEqual((report["total_pedidos"], report["faturamento_bruto"], report["pedidos_aprovados"]), (1, 40, 1))
        self.assertEqual(check("POST", "/admin/query", 200, {"sql": "SELECT COUNT(*) AS total FROM pedidos"})["dados"], [{"total": 1}])
        check("POST", "/admin/reset-db", 200, {})
        for table in ("produtos", "usuarios", "pedidos", "itens_pedido"):
            self.assertEqual(self.sql(f"SELECT COUNT(*) FROM {table}"), [(0,)])
        self.assertEqual(len(responses), 19)

    def test_no_secrets_in_public_health(self):
        body = self.client.get("/health").json
        self.assertEqual(body["status"], "ok")
        self.assertTrue({"secret_key", "debug", "db_path"}.isdisjoint(body))

    def test_user_responses_do_not_expose_password_or_hash(self):
        self.login()
        for path in ("/usuarios", "/usuarios/2"):
            body = self.client.get(path).json["dados"]
            for user in body if isinstance(body, list) else [body]:
                self.assertNotIn("senha", user)

    def test_registration_hashes_password_and_ignores_role_escalation(self):
        for email in ("new1@example.test", "new2@example.test"):
            response = self.client.post("/usuarios", json={"nome": "Nome Teste", "email": email, "senha": "same-password", "tipo": "admin"})
            self.assertEqual(response.status_code, 201)
        rows = self.sql("SELECT senha,tipo FROM usuarios WHERE email LIKE 'new%@example.test' ORDER BY id")
        self.assertTrue(all(check_password_hash(row[0], "same-password") for row in rows))
        self.assertNotEqual(rows[0][0], rows[1][0])
        self.assertEqual([row[1] for row in rows], ["cliente", "cliente"])

    def test_login_rejects_sql_injection_and_wrong_password(self):
        for email, password in [("' OR 1=1 --", "x"), ("admin@example.test", "wrong")]:
            response = self.client.post("/login", json={"email": email, "senha": password})
            self.assertEqual(response.status_code, 401)

    def test_product_apostrophe_and_search_injection_are_literal(self):
        self.login()
        response = self.client.post("/produtos", headers=self.headers, json={"nome": "Livro d'água", "preco": 10, "estoque": 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/produtos/busca", query_string={"q": "' OR 1=1 --"}).json["total"], 0)

    def test_sensitive_routes_require_identity(self):
        cases = [("GET", "/usuarios", None), ("GET", "/usuarios/2", None), ("GET", "/pedidos", None),
                 ("GET", "/pedidos/usuario/2", None), ("GET", "/relatorios/vendas", None),
                 ("POST", "/produtos", {}), ("PUT", "/produtos/1", {}), ("DELETE", "/produtos/1", None),
                 ("POST", "/pedidos", {}), ("PUT", "/pedidos/1/status", {}),
                 ("POST", "/admin/query", {"sql": "SELECT 1"}), ("POST", "/admin/reset-db", {})]
        for method, path, body in cases:
            with self.subTest(method=method, path=path):
                self.assertEqual(self.client.open(path, method=method, json=body).status_code, 401)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM produtos"), [(2,)])

    def test_customer_cannot_access_admin_or_other_users_resources(self):
        self.login("client@example.test")
        for method, path, body in [("GET", "/usuarios", None), ("GET", "/usuarios/3", None),
                ("GET", "/pedidos", None), ("GET", "/pedidos/usuario/3", None), ("GET", "/relatorios/vendas", None),
                ("POST", "/produtos", {}), ("PUT", "/produtos/1", {}), ("DELETE", "/produtos/1", None),
                ("PUT", "/pedidos/1/status", {}), ("POST", "/admin/query", {"sql": "SELECT 1"}), ("POST", "/admin/reset-db", {})]:
            with self.subTest(path=path):
                self.assertEqual(self.client.open(path, method=method, json=body, headers=self.headers).status_code, 403)
        self.assertEqual(self.client.get("/usuarios/2").status_code, 200)
        self.assertEqual(self.client.get("/pedidos/usuario/2").json["dados"], [])
        self.assertEqual(self.order(user=3).status_code, 403)
        self.assertEqual(self.order().status_code, 201)

    def test_csrf_required_for_authenticated_writes(self):
        self.login()
        for headers in ({}, {"X-CSRF-Token": "wrong"}):
            self.assertEqual(self.client.delete("/produtos/1", headers=headers).status_code, 403)
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(10,)])

    def test_failed_login_clears_previous_identity(self):
        self.login()
        self.client.post("/login", json={"email": "admin@example.test", "senha": "wrong"})
        self.assertEqual(self.client.get("/usuarios").status_code, 401)

    def test_update_uses_same_product_rules_as_create(self):
        self.login()
        for overrides in ({"nome": "x"}, {"nome": "x"*201}, {"categoria": "invalida"}, {"preco": -1}, {"estoque": -1}, {"preco": "20"}, {"estoque": 1.5}, {"preco": True}):
            data = {"nome": "Nome Válido", "preco": 20, "estoque": 10, "categoria": "geral", **overrides}
            for method, path in [("POST", "/produtos"), ("PUT", "/produtos/1")]:
                with self.subTest(method=method, overrides=overrides):
                    self.assertEqual(self.client.open(path, method=method, json=data, headers=self.headers).status_code, 400)
        self.assertEqual(self.sql("SELECT nome,preco,estoque FROM produtos WHERE id=1"), [("Produto Teste",20,10)])

    def test_product_valid_boundaries_and_required_fields(self):
        self.login()
        for name in ("ab", "a"*200):
            self.assertEqual(self.client.put("/produtos/1", headers=self.headers, json={"nome":name,"preco":0,"estoque":0}).status_code, 200)
        self.assertEqual(self.client.put("/produtos/1", headers=self.headers, json={"nome":"Nome"}).status_code, 400)

    def test_invalid_order_quantities_and_shapes_do_not_write(self):
        self.login()
        for items in ([{"produto_id":1,"quantidade":v}] for v in (0,-1,1.5,True,"2",None)):
            self.assertEqual(self.order(items).status_code, 400)
        for items in ([], [None], [{}], {"produto_id":1}, [{"produto_id":"1","quantidade":1}]):
            self.assertEqual(self.order(items).status_code, 400)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pedidos"), [(0,)])
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(10,)])

    def test_duplicate_lines_cannot_oversell_stock(self):
        self.login()
        self.assertEqual(self.order([{"produto_id":1,"quantidade":6}]*2).status_code, 400)
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(10,)])
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pedidos"), [(0,)])

    def test_duplicate_valid_lines_keep_line_items_and_correct_total(self):
        self.login()
        self.assertEqual(self.order([{"produto_id":1,"quantidade":2}]*2).json["dados"]["total"], 80)
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(6,)])
        self.assertEqual(self.sql("SELECT quantidade FROM itens_pedido ORDER BY id"), [(2,), (2,)])

    def test_missing_user_product_and_insufficient_stock_do_not_write(self):
        self.login()
        self.assertEqual(self.order(user=999).status_code, 404)
        self.assertEqual(self.order([{"produto_id":999,"quantidade":1}]).status_code, 400)
        self.assertEqual(self.order([{"produto_id":1,"quantidade":11}]).status_code, 400)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pedidos"), [(0,)])

    def test_failure_mid_order_rolls_back_before_later_commit(self):
        self.login()
        self.sql("CREATE TRIGGER fail_item BEFORE INSERT ON itens_pedido BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
        self.assertEqual(self.order().status_code, 500)
        self.assertEqual(self.client.post("/usuarios", json={"nome":"Outro", "email":"later@example.test", "senha":"test"}).status_code, 201)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pedidos"), [(0,)])
        self.assertEqual(self.sql("SELECT COUNT(*) FROM itens_pedido"), [(0,)])
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(10,)])

    def test_concurrent_orders_cannot_oversell(self):
        def purchase(_):
            client = self.app.test_client()
            headers = self.login("client@example.test", client)
            return self.order([{"produto_id":1,"quantidade":6}], client=client, headers=headers).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(sorted(executor.map(purchase, range(2))), [201,400])
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(4,)])
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pedidos"), [(1,)])

    def test_invalid_json_and_filters_have_safe_client_errors(self):
        self.login()
        for body in (None, [], "text", 1):
            self.assertEqual(self.client.post("/login", json=body).status_code, 400)
        self.assertEqual(self.client.post("/login", data="{", content_type="application/json").status_code, 400)
        for value in ("abc", "nan", "inf", "-inf"):
            response = self.client.get("/produtos/busca", query_string={"preco_min":value})
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("float", response.json["erro"])

    def test_missing_resources_and_invalid_status(self):
        self.login()
        for method, path, body in [("GET","/produtos/999",None),("PUT","/produtos/999",{}),("DELETE","/produtos/999",None),
                                   ("GET","/usuarios/999",None),("PUT","/pedidos/999/status",{"status":"aprovado"})]:
            self.assertEqual(self.client.open(path, method=method, json=body, headers=self.headers).status_code, 404)
        self.assertEqual(self.client.put("/pedidos/1/status", json={"status":"invalido"}, headers=self.headers).status_code, 400)

    def test_report_discount_boundaries_preserve_existing_strict_comparison(self):
        self.login()
        for amount, discount in [(0,0),(999,0),(1000,0),(1001,20.02),(4999,99.98),(5000,100),(5001,250.05),(9999,499.95),(10000,500),(10001,1000.1)]:
            self.sql("DELETE FROM pedidos")
            self.sql("INSERT INTO pedidos(usuario_id,total,status) VALUES(2,?,'pendente')", (amount,))
            report = self.client.get("/relatorios/vendas").json["dados"]
            self.assertEqual(report["desconto_aplicavel"], discount)

    def test_listing_keeps_empty_orders_and_deleted_product_name(self):
        self.login()
        self.sql("INSERT INTO pedidos(id,usuario_id,total) VALUES(1,2,0)")
        self.sql("INSERT INTO pedidos(id,usuario_id,total) VALUES(2,2,20)")
        self.sql("INSERT INTO itens_pedido(pedido_id,produto_id,quantidade,preco_unitario) VALUES(2,999,1,20)")
        orders = self.client.get("/pedidos").json["dados"]
        self.assertEqual(orders[0]["itens"], [])
        self.assertEqual(orders[1]["itens"][0]["produto_nome"], "Desconhecido")

    def test_admin_query_reads_and_writes_but_defaults_to_disabled(self):
        self.login()
        response = self.client.post("/admin/query", headers=self.headers, json={"sql":"UPDATE produtos SET estoque=9 WHERE id=1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"), [(9,)])
        self.assertEqual(self.client.post("/admin/query", json={"sql":""}, headers=self.headers).status_code, 400)
        self.app.config["ADMIN_TOOLS_ENABLED"] = False
        for path in ("/admin/query", "/admin/reset-db"):
            self.assertEqual(self.client.post(path, json={"sql":"SELECT 1"}, headers=self.headers).status_code, 403)

    def test_duplicate_emails_preserve_distinct_existing_credentials(self):
        ids=[]
        for password in ("first-password", "second-password"):
            created=self.client.post("/usuarios",json={"nome":"Pessoa", "email":"duplicate@example.test", "senha":password})
            self.assertEqual(created.status_code,201)
            ids.append(created.json["dados"]["id"])
        for password,uid in zip(("first-password","second-password"),ids):
            response=self.client.post("/login",json={"email":"duplicate@example.test","senha":password})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json["dados"]["id"],uid)

    def test_monetary_overflow_rejects_order_without_any_write(self):
        self.login()
        self.sql("UPDATE produtos SET preco=1e308 WHERE id=1")
        self.assertEqual(self.order().status_code,400)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM pedidos"),[(0,)])
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"),[(10,)])

    def test_invalid_legacy_report_totals_do_not_emit_nonfinite_json(self):
        self.login()
        self.sql("INSERT INTO pedidos(usuario_id,total) VALUES(2,?)",(float("inf"),))
        response=self.client.get("/relatorios/vendas")
        self.assertEqual(response.status_code,500)
        self.assertNotIn("Infinity",response.get_data(as_text=True))

    def test_huge_integer_inputs_and_nonascii_csrf_have_client_errors(self):
        self.login()
        for data in ({"preco":10**400},{"estoque":10**100}):
            response=self.client.post("/produtos",headers=self.headers,json={"nome":"Teste","preco":20,"estoque":10,**data})
            self.assertEqual(response.status_code,400)
        self.assertEqual(self.order([{"produto_id":10**100,"quantidade":1}]).status_code,400)
        self.assertEqual(self.order([{"produto_id":1,"quantidade":10**100}]).status_code,400)
        self.assertEqual(self.client.delete("/produtos/1",headers={"X-CSRF-Token":"inválido"}).status_code,403)

    def test_csrf_token_from_another_session_is_rejected(self):
        self.login()
        other=self.app.test_client()
        wrong_headers=self.login("client@example.test",other)
        self.assertEqual(self.client.delete("/produtos/1",headers=wrong_headers).status_code,403)
        self.assertEqual(self.sql("SELECT estoque FROM produtos WHERE id=1"),[(10,)])

    def test_role_changes_and_deleted_users_are_checked_against_database(self):
        self.login()
        self.sql("UPDATE usuarios SET tipo='cliente' WHERE id=1")
        self.assertEqual(self.client.get("/usuarios").status_code,403)
        self.sql("DELETE FROM usuarios WHERE id=1")
        self.assertEqual(self.client.get("/usuarios/1").status_code,401)

    def test_cross_origin_login_is_rejected_and_cors_is_explicit(self):
        response=self.client.post("/login",json={"email":"admin@example.test","senha":"synthetic-password"},headers={"Origin":"https://untrusted.example.test"})
        self.assertEqual(response.status_code,403)
        self.assertNotIn("Access-Control-Allow-Origin",response.headers)

    def test_tampered_cookie_does_not_authenticate(self):
        self.login()
        cookie=self.client.get_cookie("session")
        self.client.set_cookie("session",cookie.value+"tampered")
        self.assertEqual(self.client.get("/usuarios").status_code,401)

    def test_finite_large_integer_price_is_stored_as_real_in_post_and_put(self):
        self.login()
        body={"nome":"Produto Grande","preco":2**63,"estoque":1}
        response=self.client.post("/produtos",headers=self.headers,json=body)
        self.assertEqual(response.status_code,201)
        pid=response.json["dados"]["id"]
        self.assertEqual(self.client.put(f"/produtos/{pid}",headers=self.headers,json=body).status_code,200)
        self.assertEqual(self.sql("SELECT typeof(preco) FROM produtos WHERE id=?",(pid,)),[("real",)])


if __name__ == "__main__":
    unittest.main()
