const {HttpError} = require('../middleware/errors');
function positiveId(value) {
  if (!(typeof value === 'number' || typeof value === 'string' && /^[1-9]\d*$/.test(value))) throw new HttpError(400,'ID inválido');
  const id=Number(value);
  if (!Number.isSafeInteger(id) || id<=0) throw new HttpError(400,'ID inválido');
  return id;
}
function text(value,maxBytes) { return typeof value==='string' && value.trim().length>0 && Buffer.byteLength(value)<=maxBytes; }
function checkoutInput(body) {
  if (!body || typeof body!=='object' || Array.isArray(body) || !text(body.usr,200) || !text(body.eml,254) || !text(body.pwd,1024) || !text(body.card,128)) throw new HttpError(400,'Dados de checkout inválidos');
  return {name:body.usr,email:body.eml,password:body.pwd,card:body.card,courseId:positiveId(body.c_id)};
}
module.exports={checkoutInput,positiveId};
