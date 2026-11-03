const {HttpError} = require('../middleware/errors');
const users = {
  findByEmail: (db,email) => db.get('SELECT id,pass FROM users WHERE email=?',[email]),
  async create(db,{name,email,passwordHash}) {
    return (await db.run('INSERT INTO users(name,email,pass) VALUES(?,?,?)',[name,email,passwordHash])).lastID;
  },
  async remove(db,id) {
    if (!await db.get('SELECT id FROM users WHERE id=?',[id])) throw new HttpError(404,'Usuário não encontrado');
    if (await db.get('SELECT id FROM enrollments WHERE user_id=? LIMIT 1',[id])) throw new HttpError(409,'Usuário possui histórico de matrículas');
    await db.run('DELETE FROM users WHERE id=?',[id]);
  }
};
module.exports = users;
