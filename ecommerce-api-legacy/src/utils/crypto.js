/**
 * Hashing de senha com PBKDF2 (módulo `crypto` nativo do Node — sem dependência externa).
 * Substitui a "criptografia" caseira anterior (base64 repetido), que não oferecia nenhuma
 * proteção real.
 */
const crypto = require('crypto');

const ITERATIONS = 100000;
const KEYLEN = 64;
const DIGEST = 'sha512';

function hashPassword(plain) {
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.pbkdf2Sync(plain, salt, ITERATIONS, KEYLEN, DIGEST).toString('hex');
    return `${salt}:${hash}`;
}

function verifyPassword(plain, stored) {
    if (!stored || !stored.includes(':')) return false;
    const [salt, hash] = stored.split(':');
    const candidate = crypto.pbkdf2Sync(plain, salt, ITERATIONS, KEYLEN, DIGEST).toString('hex');
    return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), Buffer.from(candidate, 'hex'));
}

module.exports = { hashPassword, verifyPassword };
