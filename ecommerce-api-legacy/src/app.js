const express = require('express');
const {openDatabase} = require('./database/connection');
const {initializeSchema} = require('./database/schema');
const {validateToken} = require('./config');
const {createCheckout} = require('./services/checkout');
const {routes} = require('./routes');
const {errorHandler} = require('./middleware/errors');
async function createApplication({config, database, payment, logger=event=>console.log(JSON.stringify(event))}={}) {
  validateToken(config?.adminToken);
  const connection=database || await openDatabase();
  try {
    await initializeSchema(connection);
    const cache=new Map(), app=express();
    app.disable('x-powered-by');
    app.use(express.json());
    const checkout=createCheckout({database:connection,payment,cache,logger});
    app.use(routes({checkout,database:connection,cache,adminToken:config.adminToken}));
    app.use(errorHandler(logger));
    return {app,database:connection};
  } catch(error) { if (!database) await connection.close(); throw error; }
}
module.exports={createApplication};
