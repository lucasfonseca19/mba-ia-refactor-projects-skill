async function initializeSchema(database) {
  await database.read(db => db.exec(`
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, pass TEXT NOT NULL);
    CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT NOT NULL, price REAL NOT NULL, active INTEGER NOT NULL);
    CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT, course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE RESTRICT);
    CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE RESTRICT, amount REAL NOT NULL, status TEXT NOT NULL);
    CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT NOT NULL, created_at DATETIME NOT NULL);
  `));
}
module.exports = {initializeSchema};
