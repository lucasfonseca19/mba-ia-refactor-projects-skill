const {createHash, timingSafeEqual} = require('node:crypto');
const {HttpError} = require('./errors');
function requireAdmin(token) {
  const digest = value => createHash('sha256').update(value).digest();
  const expected = digest(token);
  return (req,res,next) => {
    const authorization = req.get('Authorization') || '';
    const match = /^Bearer ([^\s]+)$/i.exec(authorization);
    if (!match || !timingSafeEqual(expected,digest(match[1]))) return next(new HttpError(401,'Credencial administrativa necessária'));
    return next();
  };
}
module.exports = {requireAdmin};
