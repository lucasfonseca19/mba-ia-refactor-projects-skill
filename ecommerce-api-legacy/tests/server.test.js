const {test}=require('node:test');
const assert=require('node:assert/strict');
const {execFileSync,spawnSync}=require('node:child_process');
const path=require('node:path');
const cwd=path.resolve(__dirname,'..');
test('importar app não inicia servidor nem banco',()=>{
 assert.equal(execFileSync(process.execPath,['-e',"require('./src/app')"],{cwd,encoding:'utf8',timeout:5000}), '');
});
test('boot sem token falha sem revelar configuração',()=>{
 const child=spawnSync(process.execPath,['src/server.js'],{cwd,encoding:'utf8',env:{...process.env,ADMIN_API_TOKEN:''},timeout:5000});
 assert.equal(child.status,1);assert.match(child.stderr,/Falha ao iniciar/);assert.equal(child.stdout,'');
});
test('processo real inicia, atende endpoints e encerra limpo',async()=>{
 const result=await require('./process-smoke').smoke();
 assert.deepEqual(result,{boot:true,host:'127.0.0.1',ephemeralPort:true,reportStatus:200,initialRevenue:997,checkoutStatus:200,deleteLinkedStatus:409,logsSanitized:true,stderrEmpty:true,exitCode:0,signal:null,processClosed:true});
});
