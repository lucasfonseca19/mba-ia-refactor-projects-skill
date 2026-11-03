const {test}=require('node:test');
const assert=require('node:assert/strict');
const legacy=process.env.BASELINE==='1';
const security=legacy?{hashPassword:async value=>require('../src/utils').badCrypto(value)}:require('../src/security/passwords');
test('senhas com prefixo igual não colidem e possuem salt próprio',async()=>{
 const first=await security.hashPassword('Alpha-password-one'),second=await security.hashPassword('Alpha-password-two'),third=await security.hashPassword('Alpha-password-one');
 assert.notEqual(first,second); assert.notEqual(first,third);
 if(!legacy){assert.equal(await security.verifyPassword(first,'Alpha-password-one'),true);assert.equal(await security.verifyPassword(first,'Alpha-password-two'),false);}
});
if(!legacy){
 test('senhas legadas e formatos corrompidos não autenticam',async()=>{
  for(const stored of ['123','QUQUQUQUQU','scrypt$bad$bad',null]) assert.equal(await security.verifyPassword(stored,'Alpha-password-one'),false);
 });
 test('configuração rejeita token ausente, fraco e porta inválida',()=>{
  const {loadConfig}=require('../src/config');
  for(const env of [{},{ADMIN_API_TOKEN:'short'},{ADMIN_API_TOKEN:'a'.repeat(32),PORT:'wrong'},{ADMIN_API_TOKEN:'a'.repeat(32),SEED_DEMO:'1'}])assert.throws(()=>loadConfig(env));
  assert.equal(loadConfig({ADMIN_API_TOKEN:'a'.repeat(32),PORT:'0'}).port,0);
 });
}
