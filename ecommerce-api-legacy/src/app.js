/**
 * Composition root — monta a aplicação Express: carrega config, inicializa banco,
 * injeta a conexão via middleware, registra rotas e o error handler central.
 * Nenhuma lógica de negócio deve viver aqui.
 */
const express = require('express');
const { config } = require('./config');
const { initDb } = require('./models/db');
const { attachDb } = require('./middlewares/attachDb');
const { errorHandler } = require('./middlewares/errorHandler');
const { buildRouter } = require('./routes');

async function createApp() {
    const app = express();
    app.use(express.json());

    const db = await initDb();
    app.use(attachDb(db));
    app.use(buildRouter());

    // Error handler sempre é o último middleware registrado.
    app.use(errorHandler);

    return app;
}

async function start() {
    const app = await createApp();
    app.listen(config.port, () => {
        console.log(`LMS API rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    start();
}

module.exports = { createApp };
