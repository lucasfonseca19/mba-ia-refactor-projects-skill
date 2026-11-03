const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');
const { once } = require('node:events');
const ROOT = path.resolve(__dirname, '../..');
const TOKEN = 'synthetic-admin-token-for-issue010-tests';
const PASSWORD = 'Synthetic-password-for-tests';
const REVISION = '478f362d9de8969ec41905b9dd9c5077a478daf0';
function legacy(logs) {
  const read = file => execFileSync('git', ['show', `${REVISION}:ecommerce-api-legacy/src/${file}`], { cwd: ROOT, encoding: 'utf8' });
  const console = { log: (...args) => logs.push(args.join(' ')) };
  const utilities = { exports: {} };
  vm.runInNewContext(read('utils.js'), { module: utilities, Buffer, console });
  const mod = { exports: {} };
  vm.runInNewContext(read('AppManager.js'), { module: mod, console, require: name => name === './utils' ? utilities.exports : require(name) });
  const manager = new mod.exports();
  const raw = manager.db;
  let queries = 0;
  const session = Object.fromEntries(['run','get','all','exec'].map(method => [method, (sql, params = []) => new Promise((resolve, reject) => {
    queries++;
    const callback = function(error, value) { if (error) reject(error); else resolve(method === 'run' ? { lastID: this.lastID, changes: this.changes } : value); };
    if (method === 'exec') raw.exec(sql, callback); else raw[method](sql, params, callback);
  })]));
  const database = { read: fn => fn(session), close: () => new Promise((resolve,reject) => raw.close(e => e ? reject(e) : resolve())), get queryCount() { return queries; } };
  // Count queries made by the untouched legacy handlers as well.
  for (const method of ['run','get','all']) { const original = raw[method].bind(raw); raw[method] = (...args) => { queries++; return original(...args); }; }
  const express = require('express');
  const app = express(); app.use(express.json()); manager.setupRoutes(app);
  return { app, database, schema: read('AppManager.js').split('\n').filter(line => line.includes('CREATE TABLE')).map(line => JSON.parse(line.slice(line.indexOf('(')+1,line.lastIndexOf(')')))).join(';'), passwordHash: utilities.exports.badCrypto(PASSWORD) };
}
async function setup(t, { baseline = process.env.BASELINE === '1', seed = true, payment } = {}) {
  const logs = [];
  let context;
  if (baseline) {
    context = legacy(logs);
    await context.database.read(db => db.exec(context.schema));
  } else {
    const { createApplication } = require('../src/app');
    context = await createApplication({ config: { adminToken: TOKEN }, logger: event => logs.push(JSON.stringify(event)), ...(payment ? { payment } : {}) });
    const { hashPassword } = require('../src/security/passwords');
    context.passwordHash = await hashPassword(PASSWORD);
  }
  const { database, app } = context;
  if (seed) await database.read(async db => {
    await db.run('INSERT INTO users(id,name,email,pass) VALUES(1,?,?,?),(2,?,?,?)', ['Aluno Teste','student@example.test',context.passwordHash,'Sem Vínculo','free@example.test',context.passwordHash]);
    await db.run("INSERT INTO courses(id,title,price,active) VALUES(1,'Clean Architecture',997,1),(2,'Docker',497,1),(3,'Inativo',100,0),(4,'Vazio',50,1)");
    await db.run('INSERT INTO enrollments(id,user_id,course_id) VALUES(1,1,1)');
    await db.run("INSERT INTO payments(id,enrollment_id,amount,status) VALUES(1,1,997,'PAID')");
  });
  const server = app.listen(0,'127.0.0.1');
  try { await once(server,'listening'); } catch (error) { await database.close(); throw error; }
  const base = `http://127.0.0.1:${server.address().port}`;
  const close = async () => { await new Promise((resolve,reject) => { server.close(e => e ? reject(e) : resolve()); server.closeAllConnections(); }); await database.close(); };
  if (t) t.after(close);
  async function request(method,url,body,token) {
    const response = await fetch(base+url,{method,headers:{...(body !== undefined ? {'Content-Type':'application/json'} : {}),...(token ? {Authorization:`Bearer ${token}`} : {})},...(body !== undefined ? {body:JSON.stringify(body)} : {}),signal:AbortSignal.timeout(5000)});
    const text = await response.text(); let data; try {data=JSON.parse(text);} catch {data=text;}
    return { status:response.status,data };
  }
  const snapshot = () => database.read(async db => Object.fromEntries(await Promise.all(['users','enrollments','payments','audit_logs'].map(async table => [table,(await db.get(`SELECT COUNT(*) AS count FROM ${table}`)).count]))));
  return {...context, logs, request, close, snapshot};
}
function checkout(overrides={}) { return {usr:'Novo Aluno',eml:'new@example.test',pwd:PASSWORD,c_id:2,card:'4000000000000000',...overrides}; }
module.exports={setup,checkout,TOKEN,PASSWORD,REVISION};
