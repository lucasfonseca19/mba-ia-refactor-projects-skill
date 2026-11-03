const {scrypt, randomBytes, timingSafeEqual} = require('node:crypto');
const {promisify} = require('node:util');
const derive = promisify(scrypt);
const OPTIONS = {N: 16384, r: 8, p: 1};
async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const key = await derive(password, salt, 64, OPTIONS);
  return `scrypt$${salt}$${key.toString('hex')}`;
}
async function verifyPassword(stored, password) {
  if (typeof stored !== 'string' || !/^scrypt\$[a-f0-9]{32}\$[a-f0-9]{128}$/.test(stored)) return false;
  const [,salt,encoded] = stored.split('$');
  const actual = await derive(password, salt, 64, OPTIONS);
  return timingSafeEqual(Buffer.from(encoded,'hex'), actual);
}
module.exports = {hashPassword, verifyPassword};
