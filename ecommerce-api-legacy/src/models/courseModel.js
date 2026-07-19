const { dbGet, dbAll } = require('./db');

async function findActiveById(db, id) {
    return dbGet(db, 'SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

async function findAll(db) {
    return dbAll(db, 'SELECT * FROM courses');
}

module.exports = { findActiveById, findAll };
