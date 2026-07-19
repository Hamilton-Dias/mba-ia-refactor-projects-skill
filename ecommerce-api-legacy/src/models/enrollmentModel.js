const { dbRun, dbAll } = require('./db');

async function create(db, { userId, courseId }) {
    const result = await dbRun(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        userId,
        courseId,
    ]);
    return result.lastID;
}

async function findByCourseId(db, courseId) {
    return dbAll(db, 'SELECT * FROM enrollments WHERE course_id = ?', [courseId]);
}

async function findByUserId(db, userId) {
    return dbAll(db, 'SELECT * FROM enrollments WHERE user_id = ?', [userId]);
}

async function removeByUserId(db, userId) {
    return dbRun(db, 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
}

module.exports = { create, findByCourseId, findByUserId, removeByUserId };
