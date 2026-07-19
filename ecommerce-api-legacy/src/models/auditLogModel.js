const { dbRun } = require('./db');

async function log(db, action) {
    return dbRun(db, "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [
        action,
    ]);
}

module.exports = { log };
