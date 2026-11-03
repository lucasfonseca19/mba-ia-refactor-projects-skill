const {hashPassword} = require('../security/passwords');
async function seedDemo(database,password) {
  const hash=await hashPassword(password);
  await database.transaction(async db=>{
    await db.run('INSERT INTO users(id,name,email,pass) VALUES(1,?,?,?)',['Aluno Demo','demo@example.test',hash]);
    await db.run("INSERT INTO courses(id,title,price,active) VALUES(1,'Clean Architecture',997,1),(2,'Docker',497,1)");
    await db.run('INSERT INTO enrollments(id,user_id,course_id) VALUES(1,1,1)');
    await db.run("INSERT INTO payments(enrollment_id,amount,status) VALUES(1,997,'PAID')");
  });
}
module.exports={seedDemo};
