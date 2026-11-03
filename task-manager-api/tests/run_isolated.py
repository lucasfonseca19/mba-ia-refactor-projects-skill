import importlib.util, os, pathlib, sys, unittest
base=pathlib.Path(__file__).resolve().parent.parent
allowed_roots = [pathlib.Path('/private/tmp').resolve(), pathlib.Path('/tmp').resolve()]
if not any(base.is_relative_to(root) for root in allowed_roots):
    raise RuntimeError('Execute somente numa cópia sob diretório temporário, dentro de barreira externa')
os.chdir(base)
(base / 'instance').mkdir(exist_ok=True)
os.environ['TASK_DATABASE_URI'] = 'sqlite:///:memory:'
os.environ['TASK_SECRET_KEY'] = 'isolated-test-secret-with-sufficient-length'
os.environ['TASK_ISOLATED_TESTS'] = '1'
sys.path.insert(0, str(base))
spec=importlib.util.find_spec('app')
if pathlib.Path(spec.origin).resolve() != base / 'app.py':
    raise RuntimeError('Origem da aplicação inesperada')
from app import app, db
with app.app_context():
    if app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite:///:memory:' or (db.engine.url.drivername != 'sqlite' or db.engine.url.database != ':memory:' or bool(db.engine.url.query)):
        raise RuntimeError('Os testes exigem SQLite exclusivamente em memória')
    if db.session.execute(db.text('PRAGMA database_list')).all()[0][2] != '':
        raise RuntimeError('Destino do banco não está em memória')
    print('Origem e banco em memória confirmados na cópia isolada', flush=True)
suite=unittest.defaultTestLoader.discover(str(base / 'tests'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
