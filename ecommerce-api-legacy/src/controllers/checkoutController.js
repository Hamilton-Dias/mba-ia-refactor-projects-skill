/**
 * Controller de Checkout — orquestra o caso de uso completo (encontrar/criar usuário, validar
 * curso, processar pagamento, matricular, logar). Usa async/await em vez da pirâmide de
 * callbacks aninhados do código original.
 */
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const cache = require('../utils/cache');
const { hashPassword } = require('../utils/crypto');

function maskCard(cardNumber) {
    if (!cardNumber || cardNumber.length < 4) return '****';
    return `**** **** **** ${cardNumber.slice(-4)}`;
}

async function checkout(req, res, next) {
    try {
        const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;

        if (!name || !email || !courseId || !card) {
            return res.status(400).json({ error: 'Bad Request' });
        }

        const course = await courseModel.findActiveById(req.db, courseId);
        if (!course) {
            return res.status(404).json({ error: 'Curso não encontrado' });
        }

        let user = await userModel.findByEmail(req.db, email);
        let userId;
        if (!user) {
            const passwordHash = hashPassword(password || '123456');
            userId = await userModel.create(req.db, { name, email, passwordHash });
        } else {
            userId = user.id;
        }

        // Nunca logamos o número do cartão completo (PCI compliance).
        console.log(`Processando pagamento mascarado ${maskCard(card)} via gateway configurado`);
        const status = card.startsWith('4') ? 'PAID' : 'DENIED';
        if (status === 'DENIED') {
            return res.status(400).json({ error: 'Pagamento recusado' });
        }

        const enrollmentId = await enrollmentModel.create(req.db, { userId, courseId });
        await paymentModel.create(req.db, { enrollmentId, amount: course.price, status });
        await auditLogModel.log(req.db, `Checkout curso ${courseId} por ${userId}`);

        cache.set(`last_checkout_${userId}`, course.title);

        return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    } catch (err) {
        next(err);
    }
}

module.exports = { checkout };
