/**
 * Configuração central da aplicação.
 * Nenhum outro módulo deve conter segredos/credenciais literais — tudo passa por aqui,
 * lido de variáveis de ambiente, com defaults seguros apenas para desenvolvimento local.
 */
const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbUser: process.env.DB_USER || 'dev_user',
    dbPass: process.env.DB_PASS || 'dev-only-change-me',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'pk_test_dev-only',
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
};

module.exports = { config };
