function validateToken(token) {
  if (typeof token !== 'string' || token.length < 32 || /\s/.test(token)) throw new Error('ADMIN_API_TOKEN deve ter ao menos 32 caracteres sem espaços');
  return token;
}
function loadConfig(env = process.env) {
  const port = env.PORT === undefined ? 3000 : Number(env.PORT);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT inválida');
  if (env.SEED_DEMO && !['0','1'].includes(env.SEED_DEMO)) throw new Error('SEED_DEMO deve ser 0 ou 1');
  const seedDemo = env.SEED_DEMO === '1';
  if (seedDemo && (typeof env.DEMO_PASSWORD !== 'string' || !env.DEMO_PASSWORD.trim() || Buffer.byteLength(env.DEMO_PASSWORD) > 1024)) throw new Error('DEMO_PASSWORD é obrigatória para SEED_DEMO=1 (até 1024 bytes)');
  return {adminToken: validateToken(env.ADMIN_API_TOKEN), port, host: env.HOST || '127.0.0.1', seedDemo, demoPassword: env.DEMO_PASSWORD};
}
module.exports = {loadConfig, validateToken};
