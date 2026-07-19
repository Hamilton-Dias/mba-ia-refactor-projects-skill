================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   14 analyzed | ~950 lines of code

## Summary
CRITICAL: 1 | HIGH: 4 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL] Hash de Senha com Algoritmo Criptograficamente Quebrado (MD5) + Senha Exposta na API
File: models/user.py:27-32 (set_password/check_password), models/user.py:16-25 (to_dict)
Description: Senhas eram hasheadas com MD5 (`hashlib.md5(pwd.encode()).hexdigest()`), algoritmo considerado quebrado para uso em senhas há mais de uma década (colisões e ataques de força bruta viáveis com hardware comum). Além disso, `to_dict()` incluía o campo `password` (o hash) em toda resposta de API que retornasse um usuário.
Impact: Um vazamento do banco (ou até uma chamada normal à API) expõe o hash de senha de todos os usuários, que pode ser quebrado rapidamente via rainbow tables/GPU.
Recommendation: Trocar para `werkzeug.security.generate_password_hash`/`check_password_hash` (PBKDF2 com salt) e remover o campo de senha do `to_dict()`.

### [HIGH] Lógica de Negócio Duplicada em 3 Lugares (cálculo de "overdue")
File: routes/task_routes.py:30-39, 71-80, routes/user_routes.py:171-180, routes/report_routes.py:33-43
Description: O cálculo de "task atrasada" (comparar `due_date` com agora e checar status) é reimplementado de forma idêntica em quatro pontos diferentes das rotas — apesar de já existir um método `Task.is_overdue()` pronto no model (models/task.py:50-60) que nunca era chamado.
Impact: Qualquer ajuste na regra de negócio (ex.: mudar o que conta como "atrasado") precisa ser replicado em 4 lugares manualmente, com alto risco de divergência.
Recommendation: Usar `task.is_overdue()` (já existente) em todos os pontos, eliminando a duplicação.

### [HIGH] Lógica de Negócio Dentro das Rotas
File: routes/task_routes.py (toda a função `create_task`, linhas 85-154), routes/user_routes.py (toda a função `create_user`), routes/report_routes.py (`summary_report`, linhas 12-101)
Description: Validação de domínio, orquestração de múltiplos passos e regras de negócio (ex.: validar categoria/usuário existente, calcular estatísticas) ficam implementadas diretamente dentro das funções de rota, sem uma camada de serviço.
Impact: Rotas ficam extensas e difíceis de testar isoladamente (dependem do contexto HTTP completo); reuso de lógica entre rotas exige copiar/colar.
Recommendation: Extrair para uma camada de `services/` (task_service, user_service, report_service, category_service), mantendo as rotas finas.

### [HIGH] Queries N+1 em Listagens
File: routes/task_routes.py:11-63 (`get_tasks`), routes/report_routes.py:53-68 (`summary_report`, loop de `user_stats`)
Description: `get_tasks` faz `User.query.get()` e `Category.query.get()` dentro do loop de cada task; `summary_report` faz `Task.query.filter_by(user_id=u.id).all()` dentro do loop de cada usuário.
Impact: Para N tasks/usuários, gera múltiplas queries adicionais por item — degrada conforme a base cresce.
Recommendation: Buscar usuários/categorias relacionados em lote (`WHERE id IN (...)`) uma única vez antes do loop; usar `GROUP BY`/agregação no banco para contagens por usuário em vez de iterar em Python.

### [HIGH] Credenciais SMTP Hardcoded
File: services/notification_service.py:8-9 (`email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'`)
Description: Usuário e senha de e-mail SMTP hardcoded em texto puro no construtor da classe.
Impact: Qualquer pessoa com acesso ao repositório tem a credencial da conta de e-mail usada para notificações.
Recommendation: Mover para variáveis de ambiente via módulo de config central.

### [MEDIUM] `SECRET_KEY` Hardcoded
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` definido diretamente no arquivo de entrada.
Impact: Compromete a segurança de sessões/tokens assinados com essa chave.
Recommendation: Mover para módulo de config lendo de variável de ambiente.

### [MEDIUM] `except:` genérico engolindo erros
File: routes/task_routes.py:62-63 (`except: return jsonify({'error': 'Erro interno'}), 500`), routes/user_routes.py:130-132, 149-151
Description: Vários blocos usam `except:` (sem especificar o tipo de exceção), silenciando qualquer erro — inclusive `KeyboardInterrupt`/`SystemExit` em teoria, e certamente qualquer bug de programação que deveria ser visível em log.
Impact: Erros inesperados ficam invisíveis; debugging em produção fica muito mais difícil.
Recommendation: Remover os `try/except` por rota e centralizar em um error handler único (`@app.errorhandler(Exception)`), deixando exceções inesperadas subirem naturalmente.

### [MEDIUM] Duplicação de Validação (função utilitária pronta não é usada)
File: utils/helpers.py:56-95 (`process_task_data`), routes/task_routes.py:85-154 e 156-223
Description: Existe uma função `process_task_data()` em `utils/helpers.py` que já implementa toda a validação de campos de uma task (título, status, prioridade, data, tags) — mas as rotas `create_task`/`update_task` reimplementam essa mesma validação inteira manualmente, campo a campo, em vez de chamar a função existente.
Impact: Duas implementações da mesma regra de validação podem divergir silenciosamente ao longo do tempo (bug clássico de duplicação por não-reuso).
Recommendation: Fazer as rotas (ou o novo `task_service`) chamarem `process_task_data()` em vez de reimplementar a validação.

### [MEDIUM] API Deprecated: `datetime.utcnow()`
File: models/task.py:16-17,52 · models/user.py:14 · models/category.py:10 · routes/task_routes.py (múltiplas linhas) · routes/report_routes.py (múltiplas linhas) · utils/helpers.py:38 · seed.py (múltiplas linhas)
Description: `datetime.utcnow()` é usado extensivamente. Ele está formalmente deprecated desde o Python 3.12 (emite `DeprecationWarning` em runtime, confirmado ao executar a aplicação) em favor de `datetime.now(timezone.utc)`.
Impact: Em versões futuras do Python a chamada deve ser removida, quebrando a aplicação; hoje já polui os logs com warnings a cada execução.
Recommendation: Criar um helper central `utcnow()` (retornando datetime naive em UTC via `datetime.now(timezone.utc).replace(tzinfo=None)`, para não introduzir datetimes timezone-aware incompatíveis com as colunas SQLite existentes) e substituir todos os usos.

### [MEDIUM] Dependência sem Verificação de Vulnerabilidades
File: requirements.txt:1-6
Description: Versões fixadas (`flask==3.0.0`, `flask-sqlalchemy==3.1.1`, etc.), mas sem nenhum processo de auditoria de dependências no projeto.
Impact: Risco de usar uma versão com vulnerabilidade conhecida sem visibilidade.
Recommendation: Adicionar `pip-audit` (ou similar) ao pipeline de CI.

### [LOW] Token de Login Não é um JWT Real
File: routes/user_routes.py:210 (`'token': 'fake-jwt-token-' + str(user.id)`)
Description: O endpoint `/login` retorna uma string chamada de "token" que apenas concatena um prefixo com o ID do usuário — não é assinado, não expira, não é um JWT de verdade.
Impact: Qualquer cliente pode forjar um "token" válido apenas sabendo o ID de um usuário; não há autenticação real de fato protegendo os demais endpoints.
Recommendation: Implementar JWT real (assinado com `SECRET_KEY`, com expiração) — tratado como risco residual documentado, fora do escopo desta refatoração de arquitetura MVC.

### [LOW] Nomenclatura genérica em variáveis de loop
File: routes/task_routes.py:16 (`t`), routes/user_routes.py:14 (`u`), routes/report_routes.py:55 (`u`)
Description: Uso de nomes de uma letra para variáveis de domínio (task, user) dentro de loops de negócio.
Impact: Reduz legibilidade em trechos que já são densos.
Recommendation: Renomear para `task`, `user`.

### [LOW] Falta de Módulo de Configuração Centralizado
File: app.py:11-13, services/notification_service.py:8-9
Description: Configuração de banco, secret key e SMTP espalhadas em múltiplos arquivos, sem um módulo único.
Impact: Dificulta gerenciar configuração por ambiente (dev/test/produção).
Recommendation: Criar `config/settings.py` centralizando tudo, lido de variáveis de ambiente.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure (adaptada — o projeto já tinha camadas parciais, não foi recriado do zero):
task-manager-api/
├── app.py (composition root, agora enxuto)
├── database.py (instância do SQLAlchemy, mantida)
├── seed.py (ajustado: sem API deprecated, sem senha em texto puro)
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py (NOVO — centraliza env vars)
├── models/
│   ├── task.py (is_overdue reutilizado, datetime.utcnow → utcnow())
│   ├── user.py (hash de senha com werkzeug, senha removida do to_dict)
│   └── category.py
├── services/ (camada equivalente a Controller, mantendo a convenção já usada pelo projeto)
│   ├── task_service.py (NOVO — lógica de negócio + fix de N+1 + reuso de is_overdue)
│   ├── user_service.py (NOVO)
│   ├── report_service.py (NOVO — fix de N+1 nas estatísticas por usuário)
│   ├── category_service.py (NOVO)
│   └── notification_service.py (credenciais SMTP via config)
├── routes/ (agora finas: apenas parse de request + chamada ao service)
│   ├── task_routes.py
│   ├── user_routes.py
│   └── report_routes.py
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py (NOVO — error handler central, remove os `except:` genéricos)
├── utils/
│   └── helpers.py (adiciona utcnow(); process_task_data agora é de fato usado)
└── .claude/skills/refactor-arch/ (copiada da skill original)

## Validation
  ✓ Application boots without errors (python app.py), sem nenhum DeprecationWarning
  ✓ All endpoints respond correctly — testados manualmente:
      GET  /health, GET /tasks, GET /users, POST /login (200 e 401),
      POST /tasks, POST /users (confirma senha ausente na resposta),
      DELETE /users/<id> (confirma que as tasks do usuário são removidas
      em cascata, sem deixar registros órfãos),
      GET /tasks/stats, GET /reports/summary, GET /reports/user/<id>,
      GET /categories
  ✗ Zero anti-patterns remaining — 1 risco residual documentado e aceito
      conscientemente: o token de `/login` continua sendo um mock
      (finding LOW), pois implementar JWT real está fora do escopo de uma
      refatoração de arquitetura MVC e deve ser tratado como iteração futura.
================================
