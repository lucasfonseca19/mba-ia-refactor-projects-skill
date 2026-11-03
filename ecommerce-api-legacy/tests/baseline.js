const fs=require('node:fs');
const {setup,checkout,TOKEN,REVISION}=require('./helpers');
(async()=>{
 const evidence={revision:REVISION,mode:'original sources loaded with vm; synthetic fixtures; real loopback HTTP; SQLite :memory:',scenarios:[]};
 for(const [name,action] of [
 ['checkout-approved',c=>c.request('POST','/api/checkout',checkout())],
 ['checkout-denied',c=>c.request('POST','/api/checkout',checkout({card:'5000000000000000'}))],
 ['checkout-wrong-password',c=>c.request('POST','/api/checkout',checkout({eml:'student@example.test',pwd:'wrong'}))],
 ['report-without-auth',c=>c.request('GET','/api/admin/financial-report')],
 ['delete-linked-without-auth',c=>c.request('DELETE','/api/users/1')],
 ['delete-unlinked',c=>c.request('DELETE','/api/users/2',undefined,TOKEN)],
 ['delete-absent',c=>c.request('DELETE','/api/users/999',undefined,TOKEN)],
 ['payment-write-failure',async c=>{await c.database.read(db=>db.exec("CREATE TRIGGER reject_write BEFORE INSERT ON payments BEGIN SELECT RAISE(ABORT,'synthetic'); END;"));return c.request('POST','/api/checkout',checkout());}],
 ['audit-write-failure',async c=>{await c.database.read(db=>db.exec("CREATE TRIGGER reject_write BEFORE INSERT ON audit_logs BEGIN SELECT RAISE(ABORT,'synthetic'); END;"));return c.request('POST','/api/checkout',checkout());}]
 ]) {
  const c=await setup(null,{baseline:true});
  try {const before=await c.snapshot(),response=await action(c);evidence.scenarios.push({name,status:response.status,before,after:await c.snapshot(),cardInLogs:c.logs.some(x=>x.includes('4000000000000000')||x.includes('5000000000000000'))});}
  finally{await c.close();}
 }
 evidence.resourcesClosed=true;
 fs.writeFileSync(process.argv[2],JSON.stringify(evidence,null,2)+'\n');
 console.log(JSON.stringify(evidence,null,2));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
