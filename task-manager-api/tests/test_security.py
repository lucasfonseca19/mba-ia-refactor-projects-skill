import hashlib
import json
import unittest
import os

if os.environ.get('TASK_ISOLATED_TESTS') != '1':
    raise RuntimeError('Execute os testes exclusivamente pelo executor em cópia isolada')

from app import app, db
from models.user import User
from models.task import Task

class SecurityTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        with app.app_context():
            if app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite:///:memory:' or (db.engine.url.drivername != 'sqlite' or db.engine.url.database != ':memory:' or bool(db.engine.url.query)):
                raise RuntimeError('Os testes exigem SQLite exclusivamente em memória')
            if db.session.execute(db.text('PRAGMA database_list')).all()[0][2] != '':
                raise RuntimeError('Destino do banco não está em memória')
            db.drop_all(); db.create_all()
            user = User(name='Example', email='user@example.invalid', role='user')
            user.password = hashlib.md5(b'test1234').hexdigest()
            admin = User(name='Admin', email='admin@example.invalid', role='admin'); admin.set_password('test1234')
            manager = User(name='Manager', email='manager@example.invalid', role='manager'); manager.set_password('test1234')
            other = User(name='Other', email='other@example.invalid', role='user'); other.set_password('test1234')
            db.session.add_all([user, admin, manager, other]); db.session.flush()
            db.session.add_all([Task(title='Tarefa própria', user_id=user.id), Task(title='Tarefa alheia', user_id=other.id)])
            db.session.commit(); self.user_id, self.other_id = user.id, other.id
        self.client = app.test_client()

    def test_protected_users_require_authentication(self):
        self.assertEqual(self.client.get('/users').status_code, 401)

    def test_legacy_login_migrates_hash_and_hides_password(self):
        response = self.client.post('/login', json={'email':'user@example.invalid','password':'test1234'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('password', response.get_json()['user'])
        with app.app_context():
            self.assertNotEqual(db.session.get(User, self.user_id).password, hashlib.md5(b'test1234').hexdigest())

    def test_registration_cannot_assign_admin_role(self):
        response = self.client.post('/users', json={'name':'New','email':'new@example.invalid','password':'test1234','role':'admin'})
        self.assertEqual(response.status_code, 403)

    def auth(self, email='user@example.invalid'):
        response = self.client.post('/login', json={'email': email, 'password': 'test1234'})
        return {'Authorization': 'Bearer ' + response.get_json()['token']}

    def test_user_cannot_access_other_user_or_elevate_role(self):
        headers = self.auth()
        self.assertEqual(self.client.get(f'/users/{self.other_id}', headers=headers).status_code, 403)
        self.assertEqual(self.client.put(f'/users/{self.user_id}', headers=headers, json={'role': 'admin'}).status_code, 403)
        self.assertEqual(self.client.delete(f'/users/{self.other_id}', headers=headers).status_code, 403)

    def test_user_task_list_and_search_are_scoped(self):
        headers = self.auth()
        for path in ('/tasks', '/tasks/search', '/tasks/stats'):
            response = self.client.get(path, headers=headers)
            self.assertEqual(response.status_code, 200)
            if path == '/tasks/stats': self.assertEqual(response.get_json()['total'], 1)
            else: self.assertEqual([t['title'] for t in response.get_json()], ['Tarefa própria'])

    def test_user_cannot_read_or_reassign_another_users_task(self):
        headers = self.auth()
        self.assertEqual(self.client.get('/tasks/2', headers=headers).status_code, 403)
        self.assertEqual(self.client.put('/tasks/1', headers=headers, json={'user_id': self.other_id}).status_code, 403)
        self.assertEqual(self.client.post('/tasks', headers=headers, json={'title':'Outra', 'user_id':self.other_id}).status_code, 403)

    def test_manager_can_read_but_not_write_administrative_data(self):
        headers = self.auth('manager@example.invalid')
        self.assertEqual(self.client.get('/users', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/reports/summary', headers=headers).status_code, 200)
        self.assertEqual(self.client.put(f'/users/{self.user_id}', headers=headers, json={'role':'admin'}).status_code, 403)
        self.assertEqual(self.client.post('/categories', headers=headers, json={'name':'teste'}).status_code, 403)

    def test_invalid_token_rejected_and_admin_can_access_users(self):
        self.assertEqual(self.client.get('/users', headers={'Authorization':'Bearer invalid'}).status_code, 401)
        self.assertEqual(self.client.get('/users', headers=self.auth('admin@example.invalid')).status_code, 200)

    def test_configuration_uses_environment(self):
        import os
        self.assertEqual(app.config['SECRET_KEY'], os.environ['TASK_SECRET_KEY'])
        self.assertEqual(app.config['SQLALCHEMY_DATABASE_URI'], os.environ['TASK_DATABASE_URI'])

    def test_invalid_task_priority_is_a_client_error(self):
        response = self.client.post('/tasks', headers=self.auth(), json={'title':'Tarefa válida','priority':'abc'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_search_filter_is_a_client_error(self):
        response = self.client.get('/tasks/search?priority=no', headers=self.auth())
        self.assertEqual(response.status_code, 400)

    def test_task_references_outside_database_integer_range_return_400_without_writes(self):
        headers = self.auth('admin@example.invalid')
        for method, path in [('POST', '/tasks'), ('PUT', '/tasks/1')]:
            for field in ('user_id', 'category_id'):
                for value in (2 ** 63, 10 ** 100):
                    with self.subTest(method=method, field=field, value=value):
                        response = self.client.open(path, method=method, headers=headers,
                            json={'title': 'Alteração inválida', field: value})
                        self.assertEqual(response.status_code, 400)
                        with app.app_context():
                            self.assertEqual(Task.query.count(), 2)
                            self.assertEqual(db.session.get(Task, 1).title, 'Tarefa própria')

    def test_search_filters_outside_database_integer_range_return_400(self):
        headers = self.auth('admin@example.invalid')
        for field in ('priority', 'user_id'):
            for value in (str(2 ** 63), '9' * 100, '9' * 5000):
                with self.subTest(field=field, digits=len(value)):
                    response = self.client.get('/tasks/search', headers=headers, query_string={field: value})
                    self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/tasks/search?q=Tarefa', headers=headers).status_code, 200)
        with app.app_context():
            self.assertEqual(Task.query.count(), 2)

    def test_resource_ids_outside_database_integer_range_return_400(self):
        headers = self.auth('admin@example.invalid')
        invalid_id = str(2 ** 63)
        for path in ('/tasks/', '/users/', '/categories/'):
            methods = ('PUT', 'DELETE') if path == '/categories/' else ('GET', 'PUT', 'DELETE')
            for method in methods:
                with self.subTest(path=path, method=method):
                    response = self.client.open(path + invalid_id, method=method, headers=headers,
                        json={'title': 'Tarefa válida', 'name': 'Exemplo'} if method == 'PUT' else None)
                    self.assertEqual(response.status_code, 400)
        for path in (f'/users/{invalid_id}/tasks', f'/reports/user/{invalid_id}'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=headers).status_code, 400)
        with app.app_context():
            self.assertEqual(Task.query.count(), 2)
            self.assertEqual(User.query.count(), 4)

    def test_database_integer_upper_bound_and_leading_zeros_remain_supported(self):
        headers = self.auth('admin@example.invalid')
        maximum = 9223372036854775807
        self.assertEqual(self.client.get(f'/tasks/{maximum}', headers=headers).status_code, 404)
        self.assertEqual(self.client.post('/tasks', headers=headers,
            json={'title': 'Tarefa válida', 'category_id': maximum}).status_code, 404)
        for field in ('priority', 'user_id'):
            response = self.client.get('/tasks/search', headers=headers, query_string={field: str(maximum)})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), [])
        response = self.client.get('/tasks/search?user_id=00000000000000000001', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([task['id'] for task in response.get_json()], [1])

    def test_invalid_priority_types_and_bounds_do_not_modify_tasks(self):
        headers = self.auth('admin@example.invalid')
        for priority in (0, 6, True, 2.5, '3', None, [], {}):
            for method, path in (('POST', '/tasks'), ('PUT', '/tasks/1')):
                with self.subTest(priority=priority, method=method):
                    response = self.client.open(path, method=method, headers=headers,
                        json={'title': 'Alteração inválida', 'priority': priority})
                    self.assertEqual(response.status_code, 400)
                    with app.app_context():
                        self.assertEqual(Task.query.count(), 2)
                        self.assertEqual(db.session.get(Task, 1).title, 'Tarefa própria')

    def test_write_body_containers_are_rejected_including_public_login(self):
        headers = self.auth('admin@example.invalid')
        endpoints = [('POST', path) for path in ('/login', '/users', '/tasks', '/categories')]
        endpoints += [('PUT', path) for path in ('/users/1', '/tasks/1', '/categories/1')]
        for payload in ([], ['invalid'], 'invalid', 1, True, None):
            for method, path in endpoints:
                with self.subTest(payload=payload, method=method, path=path):
                    response = self.client.open(path, method=method, headers=headers,
                        data=json.dumps(payload), content_type='application/json')
                    self.assertEqual(response.status_code, 400)
        with app.app_context():
            self.assertEqual(Task.query.count(), 2)
            self.assertEqual(User.query.count(), 4)

    def test_overdue_rule_avoids_deprecated_datetime(self):
        import warnings
        from datetime import datetime, timedelta
        with warnings.catch_warnings():
            warnings.simplefilter('error', DeprecationWarning)
            self.assertTrue(Task(title='Atrasada', status='pending', due_date=datetime.now() - timedelta(days=2)).is_overdue())

    def test_detail_avoids_legacy_query_get(self):
        import warnings
        from sqlalchemy.exc import LegacyAPIWarning
        headers = self.auth()
        with warnings.catch_warnings():
            warnings.simplefilter('error', LegacyAPIWarning)
            self.assertEqual(self.client.get('/tasks/1', headers=headers).status_code, 200)

    def test_category_and_user_lists_do_not_query_per_row(self):
        from models.category import Category
        from sqlalchemy import event
        with app.app_context():
            db.session.add_all([Category(name='A'), Category(name='B'), Category(name='C')]); db.session.commit()
            queries = []
            def count(conn, cursor, statement, parameters, context, executemany):
                if statement.lstrip().upper().startswith('SELECT'): queries.append(statement)
            event.listen(db.engine, 'before_cursor_execute', count)
            try:
                headers = self.auth('admin@example.invalid'); queries.clear()
                self.assertEqual(self.client.get('/categories', headers=headers).status_code, 200)
                self.assertLessEqual(len(queries), 3)
                queries.clear()
                self.assertEqual(self.client.get('/users', headers=headers).status_code, 200)
                self.assertLessEqual(len(queries), 3)
            finally:
                event.remove(db.engine, 'before_cursor_execute', count)

    def test_all_original_endpoints_and_persistence(self):
        headers = self.auth('admin@example.invalid')
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/health').status_code, 200)
        self.assertEqual(self.client.get('/users', headers=headers).status_code, 200)
        self.assertEqual(self.client.get(f'/users/{self.user_id}', headers=headers).status_code, 200)
        self.assertEqual(self.client.get(f'/users/{self.user_id}/tasks', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/tasks', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/tasks/1', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/tasks/search?q=Tarefa', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/tasks/stats', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/reports/summary', headers=headers).status_code, 200)
        self.assertEqual(self.client.get(f'/reports/user/{self.user_id}', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/categories', headers=headers).status_code, 200)
        created = self.client.post('/users', headers=headers, json={'name':'Nova','email':'new@example.invalid','password':'test1234','role':'user'})
        self.assertEqual(created.status_code, 201); uid=created.get_json()['id']
        self.assertNotIn('password', created.get_json())
        self.assertEqual(self.client.put(f'/users/{uid}', headers=headers, json={'name':'Alterada'}).status_code, 200)
        category = self.client.post('/categories', headers=headers, json={'name':'Nova'})
        self.assertEqual(category.status_code, 201); cid=category.get_json()['id']
        self.assertEqual(self.client.put(f'/categories/{cid}', headers=headers, json={'name':'Alterada'}).status_code, 200)
        task = self.client.post('/tasks', headers=headers, json={'title':'Nova tarefa','user_id':uid,'category_id':cid})
        self.assertEqual(task.status_code, 201); tid=task.get_json()['id']
        self.assertEqual(self.client.put(f'/tasks/{tid}', headers=headers, json={'title':'Tarefa alterada'}).status_code, 200)
        with app.app_context():
            self.assertEqual(db.session.get(Task, tid).title, 'Tarefa alterada')
        self.assertEqual(self.client.delete(f'/tasks/{tid}', headers=headers).status_code, 200)
        self.assertEqual(self.client.delete(f'/categories/{cid}', headers=headers).status_code, 200)
        self.assertEqual(self.client.delete(f'/users/{uid}', headers=headers).status_code, 200)
        with app.app_context():
            self.assertIsNone(db.session.get(Task, tid)); self.assertIsNone(db.session.get(User, uid))

    def test_task_domain_rejects_invalid_priority_without_http(self):
        from services.task_service import create_task
        with app.app_context():
            with self.assertRaises(ValueError):
                create_task({'title':'Tarefa válida','priority':'invalid'})
            self.assertEqual(Task.query.count(), 2)

    def test_bootstrap_admin_requires_credentials_and_never_replaces_existing_admin(self):
        from unittest.mock import patch
        with app.app_context():
            User.query.filter_by(role='admin').delete(); db.session.commit()
        runner = app.test_cli_runner()
        with patch.dict('os.environ', {'TASK_ADMIN_EMAIL':'bootstrap@example.invalid','TASK_ADMIN_PASSWORD':'safe-password-123','TASK_ADMIN_NAME':'Bootstrap'}):
            result = runner.invoke(args=['bootstrap-admin'])
            self.assertEqual(result.exit_code, 0)
            again = runner.invoke(args=['bootstrap-admin'])
            self.assertNotEqual(again.exit_code, 0)
        with app.app_context():
            self.assertEqual(User.query.filter_by(email='bootstrap@example.invalid').count(), 1)

    def test_category_invalid_body_is_a_client_error(self):
        headers = self.auth('admin@example.invalid')
        category = self.client.post('/categories', headers=headers, json={'name':'Exemplo'}).get_json()
        response = self.client.put(f"/categories/{category['id']}", headers=headers, json=['invalid'])
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_body_and_password_types_are_client_errors(self):
        headers = self.auth('admin@example.invalid')
        self.assertEqual(self.client.post('/login', json=['invalid']).status_code, 400)
        self.assertEqual(self.client.post('/users', json={'name':'x','email':'x@example.invalid','password':123}).status_code, 400)
        self.assertEqual(self.client.put(f'/users/{self.user_id}', headers=headers, json={'password':None}).status_code, 400)

    def test_smtp_credentials_are_not_hardcoded(self):
        from services.notification_service import NotificationService
        from unittest.mock import patch
        with patch.dict('os.environ', {}, clear=True):
            service = NotificationService()
            self.assertFalse(service.send_email('someone@example.invalid', 'Example', 'Example'))
            self.assertIsNone(service.email_password)

    def test_import_does_not_create_database(self):
        import os, pathlib, subprocess, sys, uuid
        base = pathlib.Path(__file__).resolve().parent.parent
        target = base / ('import-' + uuid.uuid4().hex + '.db')
        env = os.environ.copy()
        env['TASK_DATABASE_URI'] = 'sqlite:///' + str(target)
        result = subprocess.run([sys.executable, '-B', '-c', 'import app'], env=env, cwd=str(base), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())

    def test_unexpected_error_is_generic_and_rolls_back(self):
        from unittest.mock import patch
        headers = self.auth('admin@example.invalid')
        with patch('routes.task_routes.task_service.create_task', side_effect=RuntimeError('internal-marker')):
            response = self.client.post('/tasks', headers=headers, json={'title':'Tarefa válida'})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('internal-marker', response.get_data(as_text=True))

    def test_user_domain_rejects_invalid_email_without_http(self):
        from services.user_service import create_user
        with app.app_context():
            with self.assertRaises(ValueError):
                create_user({'name':'Example','email':'not-an-email','password':'test1234'})
            self.assertEqual(User.query.count(), 4)

    def test_head_respects_user_resource_permissions(self):
        headers = self.auth()
        self.assertEqual(self.client.head(f'/users/{self.other_id}', headers=headers).status_code, 403)
        self.assertEqual(self.client.head('/tasks/2', headers=headers).status_code, 403)
        self.assertEqual(self.client.head('/reports/summary', headers=headers).status_code, 403)

    def test_invalid_container_field_types_return_400(self):
        headers = self.auth('admin@example.invalid')
        self.assertEqual(self.client.post('/tasks', headers=headers, json={'title':'Tarefa válida','status':[]}).status_code, 400)
        self.assertEqual(self.client.post('/users', headers=headers, json={'name':'Example','email':'new@example.invalid','password':'test1234','role':[]}).status_code, 400)
        self.assertEqual(self.client.post('/categories', headers=headers, json={'name':[]}).status_code, 400)
        self.assertEqual(self.client.post('/categories', headers=headers, json={'name':'ok','color':[]}).status_code, 400)

    def test_public_registration_is_independent_of_bearer_header(self):
        headers = self.auth()
        response = self.client.post('/users', headers=headers, json={'name':'New','email':'public@example.invalid','password':'test1234'})
        self.assertEqual(response.status_code, 201)
        response = self.client.post('/users', headers={'Authorization':'Bearer invalid'}, json={'name':'New','email':'second@example.invalid','password':'test1234'})
        self.assertEqual(response.status_code, 201)

    def test_category_counts_are_scoped_for_regular_users(self):
        from models.category import Category
        with app.app_context():
            category = Category(name='Compartilhada'); db.session.add(category); db.session.flush()
            for task in Task.query.all(): task.category_id = category.id
            db.session.commit()
        regular = self.client.get('/categories', headers=self.auth()).get_json()
        admin = self.client.get('/categories', headers=self.auth('admin@example.invalid')).get_json()
        self.assertEqual(regular[0]['task_count'], 1)
        self.assertEqual(admin[0]['task_count'], 2)

    def test_invalid_task_fields_do_not_modify_data(self):
        headers = self.auth('admin@example.invalid')
        for field, value in [('description', []), ('due_date', []), ('due_date', False), ('user_id', 0), ('category_id', 0)]:
            response = self.client.put('/tasks/1', headers=headers, json={field:value})
            self.assertEqual(response.status_code, 400, (field, value))
        with app.app_context():
            self.assertIsNone(db.session.get(Task, 1).due_date)
            self.assertIsNone(db.session.get(Task, 1).category_id)
            self.assertEqual(db.session.get(Task, 1).user_id, self.user_id)
        self.assertEqual(self.client.get('/tasks/search?priority=²', headers=headers).status_code, 400)

    def test_test_setup_refuses_file_database_even_with_flag(self):
        import os, pathlib, sqlite3, subprocess, sys, uuid
        base = pathlib.Path(__file__).resolve().parent.parent
        target = base / ('sentinel-' + uuid.uuid4().hex + '.db')
        with sqlite3.connect(target) as connection:
            connection.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
            connection.execute("INSERT INTO users VALUES (1, 'preserved')")
        env = os.environ.copy()
        env['TASK_ISOLATED_TESTS'] = '1'
        env['TASK_DATABASE_URI'] = 'sqlite:///' + str(target)
        code = "import sys; sys.path.insert(0, 'tests'); from test_security import SecurityTests; SecurityTests().setUp()"
        result = subprocess.run([sys.executable, '-B', '-c', code], env=env, cwd=str(base), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        with sqlite3.connect(target) as connection:
            self.assertEqual(connection.execute('SELECT name FROM users WHERE id=1').fetchone(), ('preserved',))
        target.unlink()

    def test_category_nullable_description_can_be_cleared(self):
        headers = self.auth('admin@example.invalid')
        result = self.client.post('/categories', headers=headers, json={'name':'Exemplo','description':'Original'})
        self.assertEqual(result.status_code, 201)
        cid = result.get_json()['id']
        updated = self.client.put(f'/categories/{cid}', headers=headers, json={'description':None})
        self.assertEqual(updated.status_code, 200)
        self.assertIsNone(updated.get_json()['description'])

    def test_old_token_does_not_authenticate_recreated_account_with_same_id(self):
        headers = self.auth()
        with app.app_context():
            user = db.session.get(User, self.user_id)
            for task in Task.query.filter_by(user_id=user.id).all(): db.session.delete(task)
            db.session.delete(user); db.session.flush()
            replacement = User(id=self.user_id, name='Replacement', email='newowner@example.invalid', role='admin')
            replacement.set_password('test1234')
            db.session.add(replacement); db.session.commit()
        self.assertEqual(self.client.get('/users', headers=headers).status_code, 401)

    def test_password_change_revokes_existing_token(self):
        headers = self.auth()
        self.assertEqual(self.client.put(f'/users/{self.user_id}', headers=headers, json={'password':'new-password'}).status_code, 200)
        self.assertEqual(self.client.get(f'/users/{self.user_id}', headers=headers).status_code, 401)
