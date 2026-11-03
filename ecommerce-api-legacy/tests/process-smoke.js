const {spawn}=require('node:child_process');
const {once}=require('node:events');
const {TOKEN,PASSWORD}=require('./helpers');
async function smoke(){
 const child=spawn(process.execPath,['src/server.js'],{cwd:require('node:path').resolve(__dirname,'..'),env:{...process.env,ADMIN_API_TOKEN:TOKEN,HOST:'127.0.0.1',PORT:'0',SEED_DEMO:'1',DEMO_PASSWORD:PASSWORD},stdio:['ignore','pipe','pipe']});
 let output='',stderr='';child.stderr.on('data',data=>stderr+=data);
 const exit=once(child,'exit'); let timeout;
 try{
  const ready=await new Promise((resolve,reject)=>{
   timeout=setTimeout(()=>reject(new Error('server readiness timeout')),5000);
   child.once('error',reject);child.once('exit',()=>reject(new Error('server exited before readiness')));
   child.stdout.on('data',data=>{output+=data;for(const line of output.split('\n')){try{const event=JSON.parse(line);if(event.event==='listening')resolve(event);}catch{}}});
  });clearTimeout(timeout);
  const base=`http://127.0.0.1:${ready.port}`;
  async function request(method,path,body){const r=await fetch(base+path,{method,headers:{Authorization:`Bearer ${TOKEN}`,'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(5000)});return{status:r.status,data:await r.json()};}
  const report=await request('GET','/api/admin/financial-report');
  const checkout=await request('POST','/api/checkout',{usr:'Smoke Teste',eml:'smoke@example.test',pwd:PASSWORD,c_id:2,card:'4000000000000000'});
  const deletion=await request('DELETE','/api/users/1');
  const sanitized=!output.includes(TOKEN)&&!output.includes(PASSWORD)&&!output.includes('4000000000000000');
  child.kill('SIGTERM');const [code,signal]=await Promise.race([exit,new Promise((_,reject)=>{timeout=setTimeout(()=>reject(new Error('shutdown timeout')),5000);})]);clearTimeout(timeout);
  return{boot:true,host:ready.host,ephemeralPort:true,reportStatus:report.status,initialRevenue:report.data[0].revenue,checkoutStatus:checkout.status,deleteLinkedStatus:deletion.status,logsSanitized:sanitized,stderrEmpty:stderr.length===0,exitCode:code,signal,processClosed:true};
 }finally{clearTimeout(timeout);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await exit;}}
}
if(require.main===module)smoke().then(result=>{require('node:fs').writeFileSync(process.argv[2],JSON.stringify(result,null,2)+'\n');console.log(result);}).catch(error=>{console.error(error.message);process.exitCode=1;});
module.exports={smoke};
