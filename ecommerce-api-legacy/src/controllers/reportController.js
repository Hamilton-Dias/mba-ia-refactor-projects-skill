/**
 * Controller de Relatório Financeiro. A versão original disparava uma query por matrícula e
 * outra por pagamento dentro de loops aninhados (N+1). Aqui, os pagamentos de todas as
 * matrículas de um curso são buscados em uma única query (findByEnrollmentIds).
 */
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const userModel = require('../models/userModel');

async function financialReport(req, res, next) {
    try {
        const courses = await courseModel.findAll(req.db);
        const report = [];

        for (const course of courses) {
            const enrollments = await enrollmentModel.findByCourseId(req.db, course.id);
            const enrollmentIds = enrollments.map((e) => e.id);
            const userIds = enrollments.map((e) => e.user_id);
            const paymentsByEnrollment = await paymentModel.findByEnrollmentIds(req.db, enrollmentIds);
            const usersById = await userModel.findByIds(req.db, userIds);

            const courseData = { course: course.title, revenue: 0, students: [] };

            for (const enrollment of enrollments) {
                const user = usersById.get(enrollment.user_id);
                const payment = paymentsByEnrollment.get(enrollment.id);

                if (payment && payment.status === 'PAID') {
                    courseData.revenue += payment.amount;
                }

                courseData.students.push({
                    student: user ? user.name : 'Unknown',
                    paid: payment ? payment.amount : 0,
                });
            }

            report.push(courseData);
        }

        return res.json(report);
    } catch (err) {
        next(err);
    }
}

module.exports = { financialReport };
