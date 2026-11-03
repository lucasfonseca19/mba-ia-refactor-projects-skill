const {checkoutInput} = require('./validation');
const present = require('../presenters/responses');
module.exports = checkout => async (req,res) => res.status(200).json(present.checkout(await checkout(checkoutInput(req.body))));
