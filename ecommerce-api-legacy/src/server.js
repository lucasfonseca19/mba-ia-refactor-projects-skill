const {once} = require('node:events');
const {loadConfig} = require('./config');
const {createApplication} = require('./app');
const {seedDemo} = require('./database/demo');
async function start(env=process.env) {
  const config=loadConfig(env);
  const {app,database}=await createApplication({config});
  let server;
  try {
    if(config.seedDemo) await seedDemo(database,config.demoPassword);
    server=app.listen(config.port,config.host);
    await once(server,'listening');
  } catch(error) { await database.close(); throw error; }
  console.log(JSON.stringify({event:'listening',host:config.host,port:server.address().port}));
  let stopping;
  const stop=()=> stopping ||= (async()=>{
    await new Promise((resolve,reject)=>server.close(error=>error?reject(error):resolve()));
    await database.close();
  })();
  process.once('SIGINT',()=>stop().catch(()=>{process.exitCode=1;}));
  process.once('SIGTERM',()=>stop().catch(()=>{process.exitCode=1;}));
  return {server,database,stop};
}
if(require.main===module) start().catch(()=>{console.error('Falha ao iniciar: confira configuração e banco');process.exitCode=1;});
module.exports={start};
