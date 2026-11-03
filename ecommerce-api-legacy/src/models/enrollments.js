module.exports = {
  async create(db,userId,courseId) { return (await db.run('INSERT INTO enrollments(user_id,course_id) VALUES(?,?)',[userId,courseId])).lastID; },
  recordPayment: (db,id,amount,status) => db.run('INSERT INTO payments(enrollment_id,amount,status) VALUES(?,?,?)',[id,amount,status]),
  recordAudit: (db,courseId,userId) => db.run("INSERT INTO audit_logs(action,created_at) VALUES(?,datetime('now'))",[`Checkout curso ${courseId} por ${userId}`])
};
