const {Router} = require('express');
const {asyncHandler} = require('../middleware/errors');
const {requireAdmin} = require('../middleware/admin');
const checkoutController = require('../controllers/checkout');
const {adminControllers} = require('../controllers/admin');
function routes({checkout,database,cache,adminToken}) {
  const router=Router(), admin=adminControllers(database,cache), authorize=requireAdmin(adminToken);
  router.post('/api/checkout',asyncHandler(checkoutController(checkout)));
  router.get('/api/admin/financial-report',authorize,asyncHandler(admin.report));
  router.delete('/api/users/:id',authorize,asyncHandler(admin.remove));
  return router;
}
module.exports={routes};
