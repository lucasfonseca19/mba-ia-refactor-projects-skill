const sqlite3 = require('sqlite3');

async function openDatabase() {
  const raw = await new Promise((resolve, reject) => {
    const connection = new sqlite3.Database(':memory:', error => error ? reject(error) : resolve(connection));
  });
  let tail = Promise.resolve();
  let closed = false;
  let queryCount = 0;
  const session = Object.fromEntries(['run', 'get', 'all', 'exec'].map(method => [method, (sql, params = []) => new Promise((resolve, reject) => {
    queryCount++;
    const callback = function(error, value) {
      if (error) reject(error);
      else resolve(method === 'run' ? {lastID: this.lastID, changes: this.changes} : value);
    };
    if (method === 'exec') raw.exec(sql, callback);
    else raw[method](sql, params, callback);
  })]));
  function enqueue(work) {
    if (closed) return Promise.reject(new Error('Banco encerrado'));
    const result = tail.then(() => work(session));
    tail = result.catch(() => {});
    return result;
  }
  await session.exec('PRAGMA foreign_keys = ON');
  return {
    read: enqueue,
    transaction(work) {
      return enqueue(async db => {
        await db.exec('BEGIN IMMEDIATE');
        try {
          const result = await work(db);
          await db.exec('COMMIT');
          return result;
        } catch (error) {
          await db.exec('ROLLBACK');
          throw error;
        }
      });
    },
    get queryCount() { return queryCount; },
    async close() {
      if (closed) return;
      closed = true;
      await tail;
      await new Promise((resolve, reject) => raw.close(error => error ? reject(error) : resolve()));
    }
  };
}
module.exports = {openDatabase};
