/**
 * Substitui o objeto global mutável `globalCache` por uma instância encapsulada e injetável.
 */
class CacheStore {
    constructor() {
        this._store = new Map();
    }

    set(key, value) {
        this._store.set(key, value);
    }

    get(key) {
        return this._store.get(key);
    }
}

module.exports = new CacheStore();
