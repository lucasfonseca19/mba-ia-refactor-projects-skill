const { test } = require('node:test');
const assert = require('node:assert/strict');
const {setup,checkout,TOKEN,PASSWORD} = require('./helpers');

test('checkout aprovado preserva resposta e grava todas as etapas',async t=>{
 const c=await setup(t); const r=await c.request('POST','/api/checkout',checkout());
 assert.equal(r.status,200); assert.equal(r.data.msg,'Sucesso'); assert.equal(typeof r.data.enrollment_id,'number');
 assert.deepEqual(await c.snapshot(),{users:3,enrollments:2,payments:2,audit_logs:1});
 const row=await c.database.read(db=>db.get('SELECT amount,status FROM payments WHERE enrollment_id=?',[r.data.enrollment_id]));
 assert.deepEqual(row,{amount:497,status:'PAID'});
});
test('pagamento recusado não cria usuário nem registros parciais',async t=>{
 const c=await setup(t); const before=await c.snapshot();
 assert.equal((await c.request('POST','/api/checkout',checkout({card:'5000000000000000'}))).status,400);
 assert.deepEqual(await c.snapshot(),before);
});
test('email existente exige senha correta',async t=>{
 const c=await setup(t); const before=await c.snapshot();
 assert.equal((await c.request('POST','/api/checkout',checkout({eml:'student@example.test',pwd:'wrong-password'}))).status,401);
 assert.deepEqual(await c.snapshot(),before);
 assert.equal((await c.request('POST','/api/checkout',checkout({eml:'student@example.test'}))).status,200);
 assert.equal((await c.snapshot()).users,2);
});
for(const [label,body] of [['sem senha',checkout({pwd:undefined})],['senha numérica',checkout({pwd:42})],['cartão numérico',checkout({card:4000})],['email objeto',checkout({eml:{}})],['nome vazio',checkout({usr:'   '})],['ID inválido',checkout({c_id:'2x'})],['ID não positivo',checkout({c_id:0})],['corpo nulo',null]]) {
 test(`entrada inválida: ${label} não grava`,async t=>{
  const c=await setup(t); const before=await c.snapshot();
  assert.equal((await c.request('POST','/api/checkout',body)).status,400);
  assert.deepEqual(await c.snapshot(),before);
 });
}
for(const id of [3,999]) test(`curso ${id} indisponível mantém banco`,async t=>{
 const c=await setup(t); const before=await c.snapshot();
 assert.equal((await c.request('POST','/api/checkout',checkout({c_id:id}))).status,404); assert.deepEqual(await c.snapshot(),before);
});
test('logs e respostas não contêm cartão, senha nem token',async t=>{
 const c=await setup(t); const body=checkout(); const r=await c.request('POST','/api/checkout',body);
 assert.equal(r.status,200); const output=c.logs.join('\n')+JSON.stringify(r);
 for(const secret of [body.card,body.pwd,TOKEN]) assert.equal(output.includes(secret),false);
});
for(const table of ['users','enrollments','payments','audit_logs']) test(`falha em ${table} desfaz checkout inteiro`,async t=>{
 const c=await setup(t); const before=await c.snapshot();
 await c.database.read(db=>db.exec(`CREATE TRIGGER reject_write BEFORE INSERT ON ${table} BEGIN SELECT RAISE(ABORT,'synthetic injected failure'); END;`));
 const r=await c.request('POST','/api/checkout',checkout()); assert.equal(r.status,500); assert.deepEqual(await c.snapshot(),before);
 assert.equal(JSON.stringify(r).includes('synthetic injected failure'),false);
 await c.database.read(db=>db.exec('DROP TRIGGER reject_write'));
 assert.equal((await c.request('POST','/api/checkout',checkout())).status,200);
});
test('relatório e exclusão rejeitam credenciais ausentes ou inválidas',async t=>{
 const c=await setup(t); const before=await c.snapshot();
 for(const token of [undefined,'invalid-token']) {
  assert.equal((await c.request('GET','/api/admin/financial-report',undefined,token)).status,401);
  assert.equal((await c.request('DELETE','/api/users/2',undefined,token)).status,401);
 }
 assert.deepEqual(await c.snapshot(),before);
});
test('relatório autorizado preserva receitas, alunos e cursos vazios',async t=>{
 const c=await setup(t); await c.request('POST','/api/checkout',checkout());
 const r=await c.request('GET','/api/admin/financial-report',undefined,TOKEN); assert.equal(r.status,200);
 const report=r.data.sort((a,b)=>a.course.localeCompare(b.course));
 assert.deepEqual(report,[{course:'Clean Architecture',revenue:997,students:[{student:'Aluno Teste',paid:997}]},{course:'Docker',revenue:497,students:[{student:'Novo Aluno',paid:497}]},{course:'Inativo',revenue:0,students:[]},{course:'Vazio',revenue:0,students:[]}]);
});
test('exclusão autorizada sem vínculos remove usuário',async t=>{
 const c=await setup(t); assert.equal((await c.request('DELETE','/api/users/2',undefined,TOKEN)).status,200);
 assert.equal(await c.database.read(db=>db.get('SELECT id FROM users WHERE id=2')),undefined);
});
test('exclusão vinculada recebe 409 e preserva histórico',async t=>{
 const c=await setup(t); const before=await c.snapshot(); assert.equal((await c.request('DELETE','/api/users/1',undefined,TOKEN)).status,409); assert.deepEqual(await c.snapshot(),before);
});
for(const [id,status] of [['999',404],['no',400],['0',400],['1.5',400]]) test(`exclusão ${id} retorna ${status}`,async t=>{
 const c=await setup(t); const before=await c.snapshot(); assert.equal((await c.request('DELETE',`/api/users/${id}`,undefined,TOKEN)).status,status); assert.deepEqual(await c.snapshot(),before);
});
test('checkouts concorrentes não misturam rollback e commit',async t=>{
 const c=await setup(t);
 await c.database.read(db=>db.exec("CREATE TRIGGER reject_course BEFORE INSERT ON payments WHEN NEW.amount=997 BEGIN SELECT RAISE(ABORT,'synthetic'); END;"));
 const results=await Promise.all([c.request('POST','/api/checkout',checkout({eml:'fail@example.test',c_id:1})),c.request('POST','/api/checkout',checkout({eml:'ok@example.test'}))]);
 assert.deepEqual(results.map(r=>r.status),[500,200]); assert.deepEqual(await c.snapshot(),{users:3,enrollments:2,payments:2,audit_logs:1});
 assert.equal(await c.database.read(db=>db.get("SELECT id FROM users WHERE email='fail@example.test'")),undefined);
});
test('mesmo email concorrente cria um usuário e verifica senha',async t=>{
 const c=await setup(t); const results=await Promise.all([c.request('POST','/api/checkout',checkout()),c.request('POST','/api/checkout',checkout({pwd:'another-password'}))]);
 assert.deepEqual(results.map(r=>r.status).sort(),[200,401]); assert.deepEqual(await c.snapshot(),{users:3,enrollments:2,payments:2,audit_logs:1});
});
test('erro de consulta não vira 404 ou relatório parcial',async t=>{
 const c=await setup(t); await c.database.read(db=>db.exec('ALTER TABLE courses RENAME TO courses_unavailable'));
 for(const r of [await c.request('POST','/api/checkout',checkout()),await c.request('GET','/api/admin/financial-report',undefined,TOKEN)]) {
  assert.equal(r.status,500); assert.equal(JSON.stringify(r).includes('SQLITE'),false);
 }
});
test('número de consultas do relatório não cresce por matrícula',async t=>{
 const c=await setup(t); let before=c.database.queryCount;
 await c.request('GET','/api/admin/financial-report',undefined,TOKEN); const small=c.database.queryCount-before;
 await c.database.read(async db=>{ for(let i=0;i<12;i++) {const e=await db.run('INSERT INTO enrollments(user_id,course_id) VALUES(1,2)'); await db.run("INSERT INTO payments(enrollment_id,amount,status) VALUES(?,497,'PAID')",[e.lastID]);}});
 before=c.database.queryCount; const r=await c.request('GET','/api/admin/financial-report',undefined,TOKEN);
 assert.equal(c.database.queryCount-before,small); assert.equal(r.data.find(x=>x.course==='Docker').revenue,5964);
});
test('aplicações não compartilham banco ou cache',async t=>{
 const a=await setup(t),b=await setup(t); await a.request('POST','/api/checkout',checkout());
 assert.deepEqual(await b.snapshot(),{users:2,enrollments:1,payments:1,audit_logs:0});
});

test('ID com codificação inválida recebe 400 sanitizado',async t=>{
 const c=await setup(t);const before=await c.snapshot();
 const r=await c.request('DELETE','/api/users/%E0%A4%A',undefined,TOKEN);
 assert.equal(r.status,400);assert.equal(JSON.stringify(r).includes('%E0'),false);assert.deepEqual(await c.snapshot(),before);
});
