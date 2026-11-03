const users = require('../models/users');
const courses = require('../models/courses');
const enrollments = require('../models/enrollments');
const {hashPassword,verifyPassword} = require('../security/passwords');
const {HttpError} = require('../middleware/errors');
const simulatePayment = async card => card.startsWith('4') ? 'PAID' : 'DENIED';
function createCheckout({database,payment=simulatePayment,cache,logger}) {
  return async input => {
    const result = await database.transaction(async db => {
      const course = await courses.findActive(db,input.courseId);
      if (!course) throw new HttpError(404,'Curso não encontrado');
      let user = await users.findByEmail(db,input.email);
      if (user && !await verifyPassword(user.pass,input.password)) throw new HttpError(401,'Credenciais inválidas ou senha legada requer redefinição');
      const status = await payment(input.card);
      if (status !== 'PAID') throw new HttpError(400,'Pagamento recusado');
      if (!user) user = {id: await users.create(db,{name:input.name,email:input.email,passwordHash:await hashPassword(input.password)})};
      const enrollmentId = await enrollments.create(db,user.id,course.id);
      await enrollments.recordPayment(db,enrollmentId,course.price,status);
      await enrollments.recordAudit(db,course.id,user.id);
      return {enrollmentId,userId:user.id,courseTitle:course.title};
    });
    // Cache is advisory, instance-scoped, and receives no card or credentials.
    cache.set(`last_checkout_${result.userId}`,result.courseTitle);
    try {logger({event:'checkout_completed',enrollmentId:result.enrollmentId});} catch {}
    return result.enrollmentId;
  };
}
module.exports = {createCheckout, simulatePayment};
