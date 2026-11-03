class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
const asyncHandler = handler => (req, res, next) => Promise.resolve().then(() => handler(req,res)).catch(next);
function errorHandler(logger) {
  return (error, req, res, next) => {
    if (res.headersSent) return next(error);
    const invalidParameter = error instanceof URIError && error.status === 400;
    const status = invalidParameter ? 400 : error instanceof HttpError ? error.status : error.type === 'entity.parse.failed' ? 400 : error.type === 'entity.too.large' ? 413 : 500;
    // Do not log error.message, request bodies or authorization headers.
    try { logger({event:'request_failed',status}); } catch {}
    return res.status(status).json({error: invalidParameter ? 'Parâmetro inválido' : status === 500 ? 'Falha interna' : status === 400 && !(error instanceof HttpError) ? 'JSON inválido' : status === 413 ? 'Corpo muito grande' : error.message});
  };
}
module.exports = {HttpError, asyncHandler, errorHandler};
