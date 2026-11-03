const {financialReport} = require('../models/financial-report');
const users = require('../models/users');
const {positiveId} = require('./validation');
const present = require('../presenters/responses');
function adminControllers(database,cache) {
  return {
    report: async (req,res) => res.json(await database.read(financialReport)),
    remove: async (req,res) => {
      const id=positiveId(req.params.id);
      await database.transaction(db=>users.remove(db,id));
      cache.delete(`last_checkout_${id}`);
      return res.status(200).json(present.deleted());
    }
  };
}
module.exports={adminControllers};
