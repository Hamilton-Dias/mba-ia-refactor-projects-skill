const { dbGet, dbRun, dbAll } = require('./db');

async function findByEmail(db, email) {
    return dbGet(db, 'SELECT * FROM users WHERE email = ?', [email]);
}

async function findById(db, id) {
    return dbGet(db, 'SELECT * FROM users WHERE id = ?', [id]);
}

/** Busca múltiplos usuários em uma única query (evita N+1). Retorna Map<id, user>. */
async function findByIds(db, ids) {
    if (ids.length === 0) return new Map();
    const placeholders = ids.map(() => '?').join(',');
    const rows = await dbAll(db, `SELECT * FROM users WHERE id IN (${placeholders})`, ids);
    return new Map(rows.map((row) => [row.id, row]));
}

async function create(db, { name, email, passwordHash }) {
    const result = await dbRun(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        name,
        email,
        passwordHash,
    ]);
    return result.lastID;
}

async function remove(db, id) {
    const result = await dbRun(db, 'DELETE FROM users WHERE id = ?', [id]);
    return result.changes > 0;
}

module.exports = { findByEmail, findById, findByIds, create, remove };
