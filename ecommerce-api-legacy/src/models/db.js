/**
 * Camada de conexão de banco. Único lugar que sabe abrir/inicializar o SQLite e expõe
 * helpers promisificados (dbRun/dbGet/dbAll) para o restante da camada de Models — elimina
 * o callback hell que existia no código original.
 */
const sqlite3 = require('sqlite3').verbose();

function createConnection() {
    return new sqlite3.Database(':memory:');
}

function dbRun(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function callback(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function dbGet(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function dbAll(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

async function initSchema(db) {
    await dbRun(db, 'CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await dbRun(db, 'CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await dbRun(db, 'CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await dbRun(db, 'CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await dbRun(db, 'CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

async function seed(db) {
    const { hashPassword } = require('../utils/crypto');
    await dbRun(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        'Leonan',
        'leonan@fullcycle.com.br',
        hashPassword('123'),
    ]);
    await dbRun(db, 'INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)', [
        'Clean Architecture',
        997.0,
        'Docker',
        497.0,
    ]);
    await dbRun(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    const enrollment = await dbGet(db, 'SELECT id FROM enrollments WHERE user_id = 1 AND course_id = 1');
    await dbRun(db, 'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
        enrollment.id,
        997.0,
        'PAID',
    ]);
}

async function initDb() {
    const db = createConnection();
    await initSchema(db);
    await seed(db);
    return db;
}

module.exports = { initDb, dbRun, dbGet, dbAll };
