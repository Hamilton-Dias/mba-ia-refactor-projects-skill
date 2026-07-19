================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~190 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] God Class (AppManager)
File: src/AppManager.js:1-142
Description: Uma única classe concentra inicialização de banco, schema, seed, roteamento HTTP, processamento de pagamento, matrícula, auditoria e geração de relatório financeiro — três endpoints inteiros e toda a lógica de domínio vivem no mesmo arquivo.
Impact: Impossível testar qualquer regra isoladamente; qualquer alteração em um fluxo (ex.: checkout) arrisca quebrar os demais (relatório, exclusão de usuário).
Recommendation: Separar em `models/` (userModel, courseModel, enrollmentModel, paymentModel, auditLogModel), `controllers/` (checkout, report, user) e `routes/`.

### [CRITICAL] Credenciais e Chave de Gateway de Pagamento Hardcoded
File: src/utils.js:1-7
Description: `dbPass`, `paymentGatewayKey` (`pk_live_...`, indicando ser uma chave de produção) e `smtpUser` estão hardcoded em texto puro no objeto `config`.
Impact: Qualquer pessoa com acesso ao repositório tem a chave de produção do gateway de pagamento e credenciais de banco/SMTP.
Recommendation: Mover tudo para variáveis de ambiente via módulo `config/index.js`, com defaults de desenvolvimento não sensíveis.

### [CRITICAL] "Criptografia" de senha inexistente (Base64 repetido)
File: src/utils.js:17-23 (`badCrypto`)
Description: A função usada para "hashear" a senha apenas repete a codificação Base64 da senha 10.000 vezes e trunca o resultado — Base64 é codificação reversível, não criptografia; o resultado nem sequer varia de forma segura com a senha original.
Impact: Senhas podem ser recuperadas trivialmente a partir do "hash" armazenado; qualquer vazamento do banco expõe as senhas reais dos usuários.
Recommendation: Substituir por PBKDF2 (`crypto.pbkdf2Sync` nativo do Node, com salt aleatório) ou bcrypt.

### [HIGH] Callback Hell / Pirâmide de Callbacks
File: src/AppManager.js:37-77 (rota `/api/checkout`)
Description: 5 níveis de callbacks aninhados (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`) misturando fluxo assíncrono, lógica de negócio e acesso a dado no mesmo bloco.
Impact: Extremamente difícil de ler, testar e adicionar tratamento de erro consistente; qualquer novo passo aumenta ainda mais o aninhamento.
Recommendation: Reescrever com `async/await` sobre helpers promisificados de `db.run/get/all`.

### [HIGH] Estado Global Mutável
File: src/utils.js:9-15 (`globalCache`), 10 (`totalRevenue`)
Description: `globalCache` é um objeto simples em nível de módulo, escrito por `logAndCache()` e compartilhado por todas as requisições concorrentes, sem nenhum controle de acesso.
Impact: Em um servidor com múltiplas requisições simultâneas, race conditions podem corromper ou misturar dados de contextos diferentes.
Recommendation: Encapsular em uma classe (`CacheStore`) com uma instância única e controlada, injetável em testes.

### [HIGH] Queries N+1 no Relatório Financeiro
File: src/AppManager.js:80-129 (`/api/admin/financial-report`)
Description: Para cada curso, busca as matrículas; para cada matrícula, busca o usuário e o pagamento individualmente — três níveis de loop com query dentro de cada um.
Impact: Para C cursos com E matrículas cada, gera até C + C*E*2 queries — degrada severamente com o crescimento da base.
Recommendation: Buscar pagamentos e usuários em lote (`WHERE id IN (...)`) por curso, uma query por lote em vez de uma por item.

### [HIGH] Exclusão de Usuário Deixa Registros Órfãos
File: src/AppManager.js:131-137 (`DELETE /api/users/:id`)
Description: O próprio endpoint deleta o usuário e retorna a mensagem "matrículas e pagamentos ficaram sujos no banco" — um comentário reconhecendo o bug, sem correção.
Impact: Dados órfãos se acumulam no banco (matrículas/pagamentos referenciando um `user_id` inexistente), quebrando integridade referencial e distorcendo relatórios.
Recommendation: Antes de deletar o usuário, remover em cascata os pagamentos e matrículas relacionados.

### [MEDIUM] Log de Dados Sensíveis de Cartão
File: src/AppManager.js:45
Description: O número completo do cartão de crédito (`cc`) é logado em texto puro no console (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`).
Impact: Violação direta de práticas de conformidade PCI-DSS — logs não devem conter PAN completo de cartão.
Recommendation: Mascarar o número do cartão em qualquer log (mostrar apenas os últimos 4 dígitos).

### [MEDIUM] Nomenclatura Genérica de Variáveis
File: src/AppManager.js:29-33 (`u`, `e`, `p`, `cid`, `cc`)
Description: Variáveis de domínio de negócio (usuário, email, senha, id do curso, cartão) recebem nomes de 1-2 letras sem contexto.
Impact: Reduz legibilidade e aumenta risco de troca acidental entre variáveis parecidas.
Recommendation: Renomear para `name`, `email`, `password`, `courseId`, `card`.

### [MEDIUM] Ausência de Dependência de Ambiente / Sem `.env`
File: package.json:1-14
Description: O projeto não tem `dotenv` nem qualquer mecanismo de carregar configuração por ambiente — os valores de `config` em `utils.js` são a única fonte, hardcoded.
Impact: Impossível trocar configuração entre dev/test/produção sem editar código-fonte.
Recommendation: Introduzir `process.env` como fonte de configuração (não requer nova dependência para o mínimo necessário).

### [LOW] Resposta HTTP com Texto Plano em Vez de JSON Consistente
File: src/AppManager.js:135 (`res.send("Usuário deletado, mas as matrículas...")`)
Description: A maioria das rotas responde com JSON, mas esta responde com uma string de texto plano, quebrando a consistência do contrato de API.
Impact: Clientes da API precisam tratar formatos de resposta diferentes para o mesmo tipo de recurso.
Recommendation: Padronizar todas as respostas como JSON.

### [LOW] Falta de Módulo de Configuração Dedicado
File: src/utils.js:1-7
Description: O objeto de configuração vive junto com funções utilitárias não relacionadas (`logAndCache`, `badCrypto`) no mesmo arquivo `utils.js`.
Impact: Mistura de responsabilidades no mesmo módulo dificulta localizar e auditar configuração.
Recommendation: Extrair para `config/index.js` dedicado.

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
ecommerce-api-legacy/
├── src/
│   ├── app.js (composition root)
│   ├── config/
│   │   └── index.js
│   ├── models/
│   │   ├── db.js
│   │   ├── userModel.js
│   │   ├── courseModel.js
│   │   ├── enrollmentModel.js
│   │   ├── paymentModel.js
│   │   └── auditLogModel.js
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── reportController.js
│   │   └── userController.js
│   ├── routes/
│   │   └── index.js
│   ├── middlewares/
│   │   ├── attachDb.js
│   │   └── errorHandler.js
│   └── utils/
│       ├── crypto.js
│       └── cache.js
├── package.json
└── .claude/skills/refactor-arch/ (copiado da skill original)

## Validation
  ✓ Application boots without errors (node src/app.js)
  ✓ All endpoints respond correctly:
      POST /api/checkout (usuário novo)        → 200 { msg: "Sucesso", enrollment_id }
      POST /api/checkout (usuário existente)   → 200 { msg: "Sucesso", enrollment_id }
      GET  /api/admin/financial-report         → 200 [ ... ]
      DELETE /api/users/:id                    → 200, e relatório subsequente confirma
                                                  que os registros relacionados foram
                                                  removidos (revenue do curso caiu
                                                  corretamente, sem lixo órfão)
  ✓ Zero anti-patterns remaining
================================
