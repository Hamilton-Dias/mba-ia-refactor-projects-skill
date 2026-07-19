/**
 * Controller de Usuário. A versão original deletava o usuário e deixava matrículas/pagamentos
 * órfãos no banco. Aqui, a exclusão limpa também os registros relacionados.
 */
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');

async function deleteUser(req, res, next) {
    try {
        const { id } = req.params;

        const enrollments = await enrollmentModel.findByUserId(req.db, id);
        const enrollmentIds = enrollments.map((e) => e.id);

        await paymentModel.removeByEnrollmentIds(req.db, enrollmentIds);
        await enrollmentModel.removeByUserId(req.db, id);
        const removed = await userModel.remove(req.db, id);

        if (!removed) {
            return res.status(404).json({ error: 'Usuário não encontrado' });
        }

        return res.json({ message: 'Usuário e registros relacionados removidos com sucesso' });
    } catch (err) {
        next(err);
    }
}

module.exports = { deleteUser };
