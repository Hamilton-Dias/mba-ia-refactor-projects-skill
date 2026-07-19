const { dbRun, dbGet, dbAll } = require('./db');

async function create(db, { enrollmentId, amount, status }) {
    const result = await dbRun(
        db,
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]
    );
    return result.lastID;
}

async function findByEnrollmentId(db, enrollmentId) {
    return dbGet(db, 'SELECT amount, status FROM payments WHERE enrollment_id = ?', [enrollmentId]);
}

/**
 * Busca pagamentos para uma lista de enrollment_ids em uma única query (evita N+1).
 * Retorna um Map<enrollment_id, payment>.
 */
async function findByEnrollmentIds(db, enrollmentIds) {
    if (enrollmentIds.length === 0) return new Map();
    const placeholders = enrollmentIds.map(() => '?').join(',');
    const rows = await dbAll(
        db,
        `SELECT * FROM payments WHERE enrollment_id IN (${placeholders})`,
        enrollmentIds
    );
    return new Map(rows.map((row) => [row.enrollment_id, row]));
}

async function removeByEnrollmentIds(db, enrollmentIds) {
    if (enrollmentIds.length === 0) return;
    const placeholders = enrollmentIds.map(() => '?').join(',');
    await dbRun(db, `DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
}

module.exports = { create, findByEnrollmentId, findByEnrollmentIds, removeByEnrollmentIds };
