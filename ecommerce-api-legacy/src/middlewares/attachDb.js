/**
 * Injeta a conexão de banco em cada requisição (req.db), evitando que os models/controllers
 * dependam de uma variável global de conexão.
 */
function attachDb(db) {
    return function attachDbMiddleware(req, res, next) {
        req.db = db;
        next();
    };
}

module.exports = { attachDb };
