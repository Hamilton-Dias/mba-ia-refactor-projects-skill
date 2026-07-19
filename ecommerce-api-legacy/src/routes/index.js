/**
 * Camada de Routes — apenas define endpoints e delega ao controller. Nenhuma regra de negócio
 * ou acesso a dado deve existir aqui.
 */
const express = require('express');
const checkoutController = require('../controllers/checkoutController');
const reportController = require('../controllers/reportController');
const userController = require('../controllers/userController');

function buildRouter() {
    const router = express.Router();

    router.post('/api/checkout', checkoutController.checkout);
    router.get('/api/admin/financial-report', reportController.financialReport);
    router.delete('/api/users/:id', userController.deleteUser);

    return router;
}

module.exports = { buildRouter };
