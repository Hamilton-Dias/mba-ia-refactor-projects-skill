# Playbook de Refatoração

Um padrão de transformação por anti-pattern do catálogo, com exemplo de código antes/depois. Os
exemplos usam Python/Flask e Node/Express como ilustração, mas o **padrão de transformação** deve
ser aplicado independentemente da linguagem real do projeto.

---

### 1. God Class/Method → Separar por domínio (Model + Controller)

**Antes** (`models.py` concentrando tudo):
```python
def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    return cursor.fetchone()

def criar_usuario(nome, email, senha):
    ...
def criar_pedido(usuario_id, itens):
    ...
```

**Depois** (um arquivo de model por domínio):
```python
# models/produto_model.py
def get_produto_por_id(db, produto_id: int):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    return cursor.fetchone()
```
```python
# models/usuario_model.py
def criar_usuario(db, nome, email, senha_hash):
    ...
```
Cada domínio (produto, usuário, pedido) ganha seu próprio model e controller; o entry point
apenas registra as rotas de cada um.

---

### 2. Credenciais Hardcoded → Config via variáveis de ambiente

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Depois:**
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
```
```python
# app.py
from config.settings import Settings
app.config.from_object(Settings)
```

---

### 3. SQL Injection (concatenação) → Query parametrizada

**Antes:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**Depois:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

Em Node.js (driver `sqlite3`), o mesmo padrão:
```js
// Antes
db.all(`SELECT * FROM users WHERE email = '${email}'`, ...)

// Depois
db.all("SELECT * FROM users WHERE email = ?", [email], (err, rows) => { ... })
```

---

### 4. Senha em texto puro / hash fraco → Hash forte, nunca exposta

**Antes:**
```python
def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password_hash = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password_hash, pwd)
```
E em qualquer serialização (`to_dict`), o campo de senha/hash **nunca** é incluído na resposta.

---

### 5. Lógica de negócio no Controller/Rota → Extrair para Controller/Service dedicado

**Antes** (rota Express fazendo tudo: validação, pagamento, matrícula, log, tudo junto):
```js
app.post('/api/checkout', (req, res) => {
    // parse + valida + processa pagamento + cria matrícula + grava log, tudo aqui
});
```

**Depois:**
```js
// routes/checkoutRoutes.js
router.post('/checkout', checkoutController.checkout);
```
```js
// controllers/checkoutController.js
async function checkout(req, res, next) {
  try {
    const result = await checkoutService.process(req.body);
    res.status(200).json(result);
  } catch (err) {
    next(err); // delega ao error handler central
  }
}
```
```js
// services/checkoutService.js — orquestra o caso de uso passo a passo, cada passo delegado a um model
```

---

### 6. Estado Global Mutável → Encapsular e injetar

**Antes:**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```

**Depois:**
```js
// config/cache.js
class CacheStore {
  constructor() { this._store = new Map(); }
  set(key, value) { this._store.set(key, value); }
  get(key) { return this._store.get(key); }
}
module.exports = new CacheStore(); // instância única, controlada, injetável em testes
```

---

### 7. Callback Hell → async/await (ou Promises encadeadas)

**Antes:**
```js
this.db.get(q1, [id], (err, a) => {
  this.db.get(q2, [a.id], (err, b) => {
    this.db.run(q3, [b.id], (err) => { res.json(...) });
  });
});
```

**Depois:**
```js
const dbGet = (sql, params) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => err ? reject(err) : resolve(row)));

async function checkout(data) {
  const course = await dbGet(q1, [data.id]);
  const user = await dbGet(q2, [course.id]);
  await dbRun(q3, [user.id]);
  return { ok: true };
}
```

---

### 8. Queries N+1 → JOIN ou eager loading / batch fetch

**Antes:**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois:**
```python
cursor.execute("""
    SELECT p.id AS pedido_id, i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    JOIN itens_pedido i ON i.pedido_id = p.id
    JOIN produtos pr ON pr.id = i.produto_id
    WHERE p.usuario_id = ?
""", (usuario_id,))
# uma única query recupera tudo; agrupar em memória por pedido_id
```

Em ORMs (SQLAlchemy, Sequelize, etc.), o equivalente é usar eager loading
(`joinedload`, `include`) em vez de acessar relacionamentos em loop.

---

### 9. Validação inconsistente / `except` genérico → Validação explícita + erro tipado

**Antes:**
```python
try:
    tasks = Task.query.all()
    ...
except:
    return jsonify({'error': 'Erro interno'}), 500
```

**Depois:**
```python
# controller valida explicitamente e deixa exceções inesperadas subirem para o error handler central
tasks = Task.query.all()
return jsonify([serialize(t) for t in tasks]), 200
```
```python
# middlewares/error_handler.py
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(e)
    return jsonify({"error": "Erro interno do servidor"}), 500
```

---

### 10. Duplicação de lógica → Extrair função compartilhada e reutilizar

**Antes:** cálculo de "overdue" reimplementado em 3 rotas diferentes.

**Depois:**
```python
# services/task_service.py
def is_overdue(task) -> bool:
    if not task.due_date:
        return False
    return task.due_date < datetime.utcnow() and task.status not in ("done", "cancelled")
```
Todas as rotas/controllers passam a chamar `is_overdue(task)` em vez de reimplementar a condição.

---

### 11. Config espalhada → Módulo único de configuração

**Antes:** porta, path do banco e flags de debug definidos diretamente no arquivo de entrada.

**Depois:** um único `config/settings.py` (ou `config/index.js`) exporta todos os valores, lidos de
env vars, e é o único ponto importado por quem precisa dessas configurações.

---

### 12. Endpoint de execução de SQL arbitrário (backdoor) → Remoção ou isolamento

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)  # SQL arbitrário vindo do cliente
```

**Depois:** o endpoint é **removido** do código de produção (não existe caso de uso legítimo para
executar SQL arbitrário vindo do request em uma API pública). Caso exista uma necessidade real de
ferramenta administrativa, ela deve rodar fora do processo da API, autenticada e sem input direto
do cliente. Documente essa remoção explicitamente no relatório de auditoria e no resumo da Fase 3.
