/**
 * Tratamento de erro centralizado — substitui os `err` ignorados/tratados de forma inconsistente
 * espalhados pelo código original.
 */
function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
    console.error('Erro não tratado:', err);
    res.status(500).json({ error: 'Erro interno do servidor' });
}

module.exports = { errorHandler };
