"""Valida 19 operações por HTTP real, em subprocesso/banco descartáveis.

Uso: .venv/bin/python -B tools/validate_http.py [--source /copia/original --legacy]
Não importe fontes não confiáveis. O diretório indicado deve ser a API auditada.
"""
import argparse
from contextlib import closing
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import secrets
import select
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


def serve(source,legacy,database):
    sys.path.insert(0,str(source))
    import app as application
    from werkzeug.serving import make_server
    from werkzeug.security import generate_password_hash
    if legacy:
        import database as storage
        storage.db_path=database
        storage.get_db()
        app=application.app
    else:
        app=application.create_app({"DATABASE_PATH":database,"SECRET_KEY":secrets.token_urlsafe(32),
                                    "ADMIN_TOOLS_ENABLED":True,"SESSION_COOKIE_SECURE":False})
        from database import init_db
        with app.app_context():
            init_db()
    app.config["DEBUG"]=False
    with closing(sqlite3.connect(database)) as db, db:
        for table in ("itens_pedido","pedidos","produtos","usuarios"):
            db.execute(f"DELETE FROM {table}")
        password="synthetic-password" if legacy else generate_password_hash("synthetic-password")
        db.executemany("INSERT INTO usuarios(id,nome,email,senha,tipo) VALUES(?,?,?,?,?)",[
            (1,"Administrador Teste","admin@example.test",password,"admin"),
            (2,"Cliente Teste","client@example.test",password,"cliente")])
        db.execute("INSERT INTO produtos(id,nome,descricao,preco,estoque,categoria) VALUES(1,'Produto Teste','Descrição',20,10,'geral')")
    server=make_server("127.0.0.1",0,app,threaded=True)
    print(server.server_port,flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def validate(source,legacy):
    with tempfile.TemporaryDirectory(prefix="http-009-") as temp:
        dbpath=str(Path(temp)/"test.db")
        command=[sys.executable,"-B",str(Path(__file__).resolve()),"--serve-source",str(source),"--database",dbpath]
        if legacy:
            command.append("--legacy")
        with open(Path(temp)/"server.log","w+") as log:
            process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=log,text=True)
            try:
                # O servidor anuncia a porta após bind e preparação das fixtures.
                ready,_,_=select.select([process.stdout],[],[],15)
                if not ready:
                    raise RuntimeError("Boot não anunciou prontidão em 15 segundos")
                port=process.stdout.readline().strip()
                if not port.isdigit():
                    raise RuntimeError("Boot falhou; consulte o ambiente/dependências da fonte")
                base=f"http://127.0.0.1:{port}"
                client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
                records=[]
                csrf={}
                def request(method,path,body=None,expected=200,record=True):
                    headers={**csrf}
                    payload=None if body is None else json.dumps(body).encode()
                    if payload is not None:
                        headers["Content-Type"]="application/json"
                    req=urllib.request.Request(base+path,data=payload,headers=headers,method=method)
                    try:
                        response=client.open(req,timeout=10)
                    except urllib.error.HTTPError as error:
                        response=error
                    with response:
                        status=response.code
                        data=json.load(response)
                    if status!=expected:
                        raise AssertionError(f"{method} {path}: esperado{expected}, recebido{status}")
                    if record:
                        records.append({"method":method,"path":path,"status":status})
                    return data
                def sql(query,params=()):
                    with closing(sqlite3.connect(dbpath)) as db, db:
                        return db.execute(query,params).fetchall()
                request("GET","/")
                health=request("GET","/health")
                assert ("secret_key" in health)==legacy
                assert len(request("GET","/produtos")["dados"])==1
                assert request("GET","/produtos/busca?q=Produto&categoria=geral&preco_min=10&preco_max=30")["total"]==1
                assert request("GET","/produtos/1")["dados"]["preco"]==20
                if not legacy:
                    request("GET","/usuarios",expected=401,record=False)
                login=request("POST","/login",{"email":"admin@example.test","senha":"synthetic-password"})
                csrf={"X-CSRF-Token":login.get("csrf_token","")}
                product={"nome":"Novo Produto","preco":30,"estoque":7,"categoria":"geral"}
                pid=request("POST","/produtos",product,201)["dados"]["id"]
                product["preco"]=35
                request("PUT",f"/produtos/{pid}",product)
                assert sql("SELECT preco FROM produtos WHERE id=?",(pid,))==[(35.0,)]
                request("DELETE",f"/produtos/{pid}")
                assert sql("SELECT id FROM produtos WHERE id=?",(pid,))==[]
                users=request("GET","/usuarios")["dados"]
                assert len(users)==2 and (("senha" in users[0])==legacy)
                assert request("GET","/usuarios/2")["dados"]["id"]==2
                uid=request("POST","/usuarios",{"nome":"Nova Pessoa","email":"new@example.test","senha":"new-password"},201)["dados"]["id"]
                assert sql("SELECT nome FROM usuarios WHERE id=?",(uid,))==[("Nova Pessoa",)]
                order=request("POST","/pedidos",{"usuario_id":2,"itens":[{"produto_id":1,"quantidade":2}]},201)["dados"]
                assert order["total"]==40
                assert sql("SELECT estoque FROM produtos WHERE id=1")==[(8,)]
                assert sql("SELECT quantidade,preco_unitario FROM itens_pedido WHERE pedido_id=?",(order["pedido_id"],))==[(2,20.0)]
                assert len(request("GET","/pedidos")["dados"])==1
                assert request("GET","/pedidos/usuario/2")["dados"][0]["itens"][0]["produto_nome"]=="Produto Teste"
                request("PUT",f"/pedidos/{order['pedido_id']}/status",{"status":"aprovado"})
                assert sql("SELECT status FROM pedidos WHERE id=?",(order["pedido_id"],))==[("aprovado",)]
                report=request("GET","/relatorios/vendas")["dados"]
                assert (report["total_pedidos"],report["faturamento_bruto"],report["pedidos_aprovados"])==(1,40,1)
                assert request("POST","/admin/query",{"sql":"SELECT COUNT(*) AS total FROM pedidos"})["dados"]==[{"total":1}]
                request("POST","/admin/reset-db",{})
                for table in ("produtos","usuarios","pedidos","itens_pedido"):
                    assert sql(f"SELECT COUNT(*) FROM {table}")==[(0,)]
                assert len(records)==19
                return {"mode":"before" if legacy else "after","boot":"ok","endpoints":records,
                        "persistence":"verified via independent SQLite connections",
                        "health_secret_exposed":legacy,"user_password_exposed":legacy,
                        "server_shutdown":"terminated and reaped in finally","database":"temporary, removed on exit"}
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                process.stdout.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--legacy",action="store_true")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--serve-source",type=Path,help=argparse.SUPPRESS)
    parser.add_argument("--database",help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.serve_source:
        serve(args.serve_source.resolve(),args.legacy,args.database)
    else:
        result=validate(args.source.resolve(),args.legacy)
        text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            args.output.write_text(text)
        print(text)
