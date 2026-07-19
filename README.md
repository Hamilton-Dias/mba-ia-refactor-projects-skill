# Desafio de Skills — Auditoria e Refatoração Arquitetural Automatizada

Este repositório contém a solução do desafio "Criação de Skills — Refatoração Arquitetural
Automatizada". Foi criada a skill `refactor-arch` (Claude Code, `.claude/skills/`), aplicada a 3
projetos legados de stacks diferentes (Python/Flask x2, Node.js/Express x1), reestruturando-os
para o padrão MVC e corrigindo os problemas encontrados na auditoria.

- Ferramenta usada: **Claude Code** (`.claude/skills/refactor-arch/`)
- Projetos: `code-smells-project/` (Flask), `ecommerce-api-legacy/` (Express),
  `task-manager-api/` (Flask, parcialmente organizado)
- Relatórios de auditoria: `reports/audit-project-{1,2,3}.md`

---

## A) Análise Manual

### Projeto 1 — code-smells-project (Python/Flask, API de E-commerce)

| Severidade | Problema | Por que importa |
|---|---|---|
| CRITICAL | SQL Injection generalizado — praticamente todas as queries em `models.py` eram montadas por concatenação de string (`"WHERE id = " + str(id)`, incluindo em `login_usuario`, que concatenava até email/senha) | Qualquer campo de entrada permite ler/alterar/apagar qualquer dado do banco |
| CRITICAL | Endpoint `/admin/query` executava SQL arbitrário recebido do corpo da requisição, sem autenticação | Backdoor total do banco exposto publicamente |
| CRITICAL | `SECRET_KEY` hardcoded em `app.py` **e** reexposta em texto puro no `/health` | Qualquer cliente da API lê a chave secreta da aplicação |
| HIGH | Senha armazenada em texto puro (coluna `senha`, sem hash algum) | Vazamento do banco expõe todas as senhas diretamente |
| MEDIUM | Queries N+1 em `get_pedidos_usuario`/`get_todos_pedidos` (query por pedido, por item, por produto) | Degrada severamente com o crescimento da base |
| MEDIUM | `try/except Exception as e: return str(e)` repetido em toda função do controller | Duplicação e vazamento de mensagens de exceção cruas ao cliente |
| LOW | Magic numbers no cálculo de desconto (10000, 5000, 0.1, 0.05) | Regra de negócio escondida em números soltos |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

| Severidade | Problema | Por que importa |
|---|---|---|
| CRITICAL | Classe `AppManager` concentra DB, rotas, pagamento, matrícula e auditoria em um único arquivo (God Class) | Impossível testar isoladamente; qualquer mudança tem raio de efeito enorme |
| CRITICAL | Credenciais de banco e **chave de gateway de pagamento de produção** (`pk_live_...`) hardcoded em `utils.js` | Vazamento do repositório expõe segredos de produção |
| CRITICAL | "Criptografia" de senha (`badCrypto`) apenas repete Base64 10.000 vezes — reversível, não é hash | Senhas recuperáveis trivialmente a partir do banco |
| HIGH | Callback hell de 5 níveis no `/api/checkout` | Extremamente difícil de ler, testar e tratar erro corretamente |
| MEDIUM | Número completo do cartão logado em texto puro no console | Violação direta de PCI-DSS |
| MEDIUM | `globalCache` — objeto mutável global compartilhado por todas as requisições | Race conditions em cenários concorrentes |
| LOW | `DELETE /api/users/:id` reconhecidamente (no próprio texto de resposta) deixa matrículas/pagamentos órfãos | Corrupção de integridade referencial ao longo do tempo — na prática, tratado como HIGH pela skill por ser um bug ativo, não só estético |

### Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)

| Severidade | Problema | Por que importa |
|---|---|---|
| CRITICAL | Hash de senha com **MD5** + senha (hash) incluída em toda resposta de `/users` | MD5 é criptograficamente quebrado para senhas; exposição facilita quebra via rainbow table |
| HIGH | Cálculo de "task atrasada" (`overdue`) reimplementado manualmente em 4 rotas diferentes, apesar de já existir `Task.is_overdue()` pronto e nunca usado | Qualquer ajuste de regra precisa ser replicado manualmente em 4 lugares |
| HIGH | Queries N+1 em `get_tasks` (busca usuário/categoria por task, dentro do loop) e em `summary_report` (busca tasks por usuário, dentro do loop) | Degrada com o crescimento da base |
| MEDIUM | `except:` genérico em várias rotas, engolindo qualquer erro sem diferenciar validação de bug | Debugging em produção fica muito mais difícil |
| MEDIUM | `datetime.utcnow()` usado extensivamente — **deprecated desde Python 3.12** (confirmado via `DeprecationWarning` real ao rodar a aplicação) | Warning hoje, quebra garantida em versão futura do Python |
| LOW | Token de `/login` é um mock (`'fake-jwt-token-' + id`), não um JWT real assinado | Qualquer cliente pode forjar um "token" válido sabendo apenas o ID do usuário |

---

## B) Construção da Skill

### Estrutura

A skill vive em `.claude/skills/refactor-arch/` (copiada, sem alterações, para dentro dos 3
projetos) e é composta por:

- **`SKILL.md`** — o "prompt" que orquestra as 3 fases obrigatórias (Análise → Auditoria com
  pausa de confirmação → Refatoração com validação), com instruções explícitas de formato de
  saída para cada fase.
- **5 arquivos de referência em `references/`**, cada um cobrindo uma das áreas de conhecimento
  exigidas:
  - `project-analysis.md` — heurísticas de detecção de linguagem/framework/banco/domínio/
    arquitetura, organizadas por **sinal observável** (manifests de dependência, imports, nomes de
    tabela) em vez de por stack específica, para garantir que funcionem em qualquer linguagem.
  - `anti-patterns-catalog.md` — 15 anti-patterns com severidade distribuída (CRITICAL → LOW),
    incluindo detecção obrigatória de APIs/dependências deprecated.
  - `report-template.md` — formato exato do relatório de auditoria.
  - `architecture-guidelines.md` — as regras do MVC alvo, com uma seção específica de "como
    adaptar quando o projeto já tem alguma organização" (crucial para o projeto 3).
  - `refactoring-playbook.md` — 12 padrões de transformação com exemplos de código antes/depois.

### Decisões de design

- **Separação entre "o que fazer" (SKILL.md) e "o que saber" (references/)**: o SKILL.md nunca
  entra em detalhe técnico de um anti-pattern específico — ele sempre aponta para o arquivo de
  referência correspondente. Isso deixa o SKILL.md curto e focado no fluxo das 3 fases.
- **Anti-patterns escolhidos**: cobrem simultaneamente segurança (SQL injection, credenciais
  hardcoded, hash de senha fraco), arquitetura (God Class, lógica de negócio em controller/rota,
  acoplamento forte), performance (N+1) e qualidade (duplicação, validação inconsistente,
  nomenclatura). Essa combinação foi escolhida porque é exatamente o que apareceu nos 3 projetos
  reais durante a análise manual — a skill não foi desenhada "no vácuo", foi desenhada a partir dos
  problemas observados.
- **Agnosticismo de tecnologia**: as heurísticas de `project-analysis.md` são organizadas por
  sinal (manifest de dependência, padrão de import, nome de tabela) e não por "se for Python faça
  X, se for Node faça Y". O `refactoring-playbook.md` traz exemplos em Python e Node lado a lado
  para o mesmo padrão de transformação, deixando claro que o padrão é o que importa, não a sintaxe.
  A prova real disso é a execução: a mesma skill, copiada sem nenhuma alteração, funcionou nos 3
  projetos (2 Flask + 1 Express).
- **Adaptação em vez de recriação**: `architecture-guidelines.md` instrui explicitamente a não
  recriar a estrutura de projetos que já têm alguma organização em camadas (caso do
  `task-manager-api`) — em vez disso, a skill deve manter a convenção de nomes já usada
  (`services/` em vez de introduzir `controllers/`) e corrigir só as violações reais.

### Desafios encontrados

- **Distinguir "ter pastas" de "ter arquitetura correta"**: o projeto 3 já tinha `models/`,
  `routes/`, `services/` — mas a lógica de negócio estava toda vazando para dentro das rotas. Foi
  necessário deixar explícito no `project-analysis.md` que a classificação da arquitetura deve
  vir da inspeção do conteúdo dos arquivos, não da existência das pastas.
- **Registros órfãos e outros bugs "estruturais"**: no projeto 2, o próprio código reconhecia (via
  comentário na resposta HTTP) que deletar um usuário deixava lixo no banco. Isso não é um
  anti-pattern "de arquitetura" clássico, mas é uma consequência direta de não ter uma camada de
  Model coesa cuidando de integridade referencial — foi tratado como finding HIGH e corrigido na
  Fase 3 (remoção em cascata).
- **Decidir o que é "risco residual aceitável"**: nem todo finding pode ser corrigido dentro do
  escopo de uma refatoração de arquitetura (ex.: implementar autenticação real com JWT, ou
  autenticação no endpoint `/admin/reset-db`). A skill foi instruída a documentar esses casos
  explicitamente em vez de fingir que "zero anti-patterns restantes" quando isso não é verdade —
  isso está refletido nos 3 relatórios de auditoria.
- **API deprecated real, não hipotética**: ao rodar de fato o projeto 3, o Python emitiu
  `DeprecationWarning` para `datetime.utcnow()`. Isso validou que a exigência do catálogo de
  detectar "APIs deprecated" não é um item de checklist vazio — apareceu um caso real, e a skill
  (e a correção) foram testadas contra ele.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | 4 | 4 | 3 | 3 | 14 |
| 2 — ecommerce-api-legacy | 3 | 4 | 3 | 2 | 12 |
| 3 — task-manager-api | 1 | 4 | 5 | 3 | 13 |

Os relatórios completos estão em `reports/audit-project-{1,2,3}.md`.

### Comparação antes/depois (estrutura)

**Projeto 1:**
```
Antes:                          Depois:
app.py                          app.py (composition root)
controllers.py                  src/
models.py                         config/settings.py
database.py                       models/{database,produto,usuario,pedido}_model.py
                                   controllers/{produto,usuario,pedido,relatorio,admin}_controller.py
                                   views/routes.py
                                   middlewares/error_handler.py
```

**Projeto 2:**
```
Antes:                          Depois:
src/app.js                      src/app.js (composition root)
src/AppManager.js (God Class)     config/index.js
src/utils.js                      models/{db,user,course,enrollment,payment,auditLog}Model.js
                                   controllers/{checkout,report,user}Controller.js
                                   routes/index.js
                                   middlewares/{attachDb,errorHandler}.js
                                   utils/{crypto,cache}.js
```

**Projeto 3** (adaptado, não recriado):
```
Antes:                          Depois:
app.py                          app.py (mais enxuto)
models/{task,user,category}.py    config/settings.py (NOVO)
routes/*.py (lógica embutida)      models/*.py (datetime fix, hash seguro)
services/notification_service.py  services/{task,user,report,category}_service.py (NOVOS)
utils/helpers.py (subutilizado)    routes/*.py (agora finas)
                                    middlewares/error_handler.py (NOVO)
                                    utils/helpers.py (process_task_data finalmente usado)
```

### Checklist de validação (preenchido para os 3 projetos)

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python nos projetos 1/3, JavaScript no projeto 2)
- [x] Framework detectado corretamente (Flask 3.1.1 / Flask 3.0.0 / Express 4.18.2)
- [x] Domínio descrito corretamente (E-commerce / LMS com checkout / Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (4 / 3 / 14)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linha(s) exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (14 / 12 / 13)
- [x] Detecção de API deprecated incluída (endpoint `/admin/query` no projeto 1; `datetime.utcnow()`
      no projeto 3 — confirmado via warning real em runtime)
- [x] Pausa e pede confirmação antes da Fase 3 (formato `[y/n]` presente nos 3 relatórios)

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (adaptada, não recriada, no projeto 3)
- [x] Configuração extraída para módulo de config, sem hardcoded, nos 3 projetos
- [x] Models criados/corrigidos para abstrair dados (queries parametrizadas, PBKDF2/werkzeug)
- [x] Views/Routes separadas para roteamento (Routes finas nos 3 projetos)
- [x] Controllers/Services concentram o fluxo da aplicação
- [x] Error handling centralizado (nos 3 projetos)
- [x] Entry point claro (composition root nos 3 projetos)
- [x] Aplicação inicia sem erros (validado rodando de verdade nos 3 projetos)
- [x] Endpoints originais respondem corretamente (validado com curl/smoke tests nos 3 projetos)

### Logs de validação (resumo — comandos completos na seção D)

**Projeto 1:**
```
GET  /health                       → 200 {"status":"ok", ...}
GET  /produtos                     → 200 (10 produtos)
POST /login                        → 200 {"mensagem":"Login OK", ...}
POST /pedidos                      → 201 {"pedido_id":1,"total":5999.99}
GET  /relatorios/vendas            → 200 (relatório calculado corretamente)
GET  /pedidos/usuario/1            → 200 (itens via JOIN, sem N+1)
```

**Projeto 2:**
```
POST /api/checkout (usuário novo)      → 200 {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout (usuário existente) → 200 {"msg":"Sucesso","enrollment_id":3}
GET  /api/admin/financial-report       → 200 [{"course":"Clean Architecture","revenue":1994,...}]
DELETE /api/users/1                    → 200 {"message":"Usuário e registros relacionados removidos..."}
GET  /api/admin/financial-report       → 200 (revenue caiu corretamente, confirma sem órfãos)
```

**Projeto 3:**
```
GET  /health                       → 200, sem DeprecationWarning
POST /tasks                        → 201 (task criada)
POST /users                        → 201 (resposta SEM campo "password")
POST /login (senha errada)         → 401
DELETE /users/2                    → 200
GET  /tasks                        → 200 (tasks do user_id 2 removidas em cascata, sem órfãs)
```

### Observações sobre o comportamento em stacks diferentes

A mesma skill (`SKILL.md` + `references/`), copiada **sem nenhuma alteração**, funcionou nos 3
projetos. As diferenças de comportamento observadas foram inteiramente no **conteúdo** dos
findings/refatoração (esperado, já que o código-fonte é diferente), não na lógica da skill em si:
- No projeto 2 (Node/callback-based), a Fase 3 precisou aplicar o padrão "callback hell →
  async/await", que não existe nos projetos Python.
- No projeto 3 (já parcialmente organizado), a Fase 3 corretamente **não recriou a estrutura**,
  apenas adicionou a camada de serviço ausente e corrigiu os problemas pontuais — validando a
  seção de "adaptação a projetos parcialmente organizados" do `architecture-guidelines.md`.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e configurado
- Python 3.11+ e `pip` (projetos 1 e 3)
- Node.js 18+ e `npm` (projeto 2)

### Executar a skill em cada projeto

```bash
# Projeto 1 — code-smells-project
cd code-smells-project
claude "/refactor-arch"
# revisar o relatório impresso na Fase 2, responder "y" para prosseguir com a Fase 3

# Projeto 2 — ecommerce-api-legacy
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api
cd ../task-manager-api
claude "/refactor-arch"
```

### Validar que a refatoração funciona (cada projeto já vem refatorado neste repositório)

**Projeto 1:**
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py &
curl http://localhost:5000/health
curl http://localhost:5000/produtos
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"admin@loja.com","senha":"admin123"}'
kill %1
```

**Projeto 2:**
```bash
cd ecommerce-api-legacy
npm install
node src/app.js &
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@x.com","pwd":"123456","c_id":1,"card":"4111111111111111"}'
curl http://localhost:3000/api/admin/financial-report
kill %1
```

**Projeto 3:**
```bash
cd task-manager-api
pip install -r requirements.txt
python app.py &
python seed.py
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
kill %1
```

Os relatórios de auditoria completos (saída da Fase 2 de cada execução) estão em
`reports/audit-project-{1,2,3}.md`.