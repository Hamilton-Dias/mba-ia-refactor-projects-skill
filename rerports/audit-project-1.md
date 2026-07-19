================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-315
Description: Um único arquivo concentra acesso a dados, SQL manual, validação e formatação para 4 domínios diferentes (produtos, usuários, pedidos, relatórios).
Impact: Impossível testar em isolamento; qualquer mudança em um domínio arrisca quebrar outro.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`, cada um com seu controller correspondente.

### [CRITICAL] Credenciais Hardcoded + Exposição de Segredo
File: app.py:7-8, controllers.py:289
Description: `SECRET_KEY` hardcoded em texto puro (`"minha-chave-super-secreta-123"`) e reexposta em texto puro na resposta do endpoint `/health` (`"secret_key": "minha-chave-super-secreta-123"`).
Impact: Qualquer cliente da API consegue ler a chave secreta da aplicação simplesmente chamando `/health`, permitindo forjar sessões/tokens.
Recommendation: Mover `SECRET_KEY` para variável de ambiente via módulo de config; remover o campo do payload de `/health`.

### [CRITICAL] SQL Injection generalizado
File: models.py:28, 48-50, 58-60, 68, 92, 109-111, 126-128, 140, 148-151, 155, 158-161, 163-165, 174, 188, 192, 220, 224, 280, 291-297
Description: Praticamente todas as queries são montadas por concatenação de string com dados vindos diretamente do request (ex.: `"SELECT * FROM produtos WHERE id = " + str(id)`, `"...WHERE email = '" + email + "' AND senha = '" + senha + "'"`).
Impact: Qualquer campo de entrada (id, nome, email, termo de busca, status) pode ser usado para injetar SQL arbitrário, lendo/alterando/apagando qualquer dado do banco.
Recommendation: Reescrever todas as queries usando parametrização (`?` do sqlite3), nunca concatenação.

### [CRITICAL] Endpoint de execução de SQL arbitrário
File: app.py:59-78
Description: A rota `/admin/query` recebe uma string SQL diretamente do corpo da requisição e a executa sem nenhuma validação, sanitização ou autenticação.
Impact: É, na prática, um backdoor total do banco de dados exposto publicamente — permite DROP TABLE, leitura de senhas, alteração de qualquer registro.
Recommendation: Remover completamente o endpoint (não há uso legítimo para isso em uma API pública).

### [HIGH] Senha em texto puro
File: models.py:83, 99, 105-120, database.py:75-79
Description: A coluna `senha` armazena a senha em texto puro (sem hash algum), incluindo os dados de seed (`"admin123"`, `"123456"`).
Impact: Vazamento do banco expõe todas as senhas diretamente; login compara texto puro com texto puro.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash`; nunca retornar a senha/hash em resposta de API.

### [HIGH] Queries N+1 em listagem de pedidos
File: models.py:171-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` fazem 1 query para os pedidos e, para cada pedido, mais uma query de itens, e para cada item mais uma query de produto (3 níveis de loop com query dentro).
Impact: Para N pedidos com M itens cada, gera até N + N*M + N*M queries — degradação severa de performance conforme a base cresce.
Recommendation: Substituir por uma única query com JOIN entre `pedidos`, `itens_pedido` e `produtos`, agrupando em memória por `pedido_id`.

### [HIGH] Endpoint administrativo sem autenticação
File: app.py:47-57
Description: `/admin/reset-db` apaga todos os dados do banco (`DELETE FROM` em todas as tabelas) sem nenhuma verificação de autenticação/autorização.
Impact: Qualquer cliente pode zerar a base de produção com uma única requisição POST.
Recommendation: Adicionar camada de autenticação/autorização (fora do escopo desta refatoração de arquitetura MVC — documentado como risco residual).

### [HIGH] Lógica de negócio dentro do Controller
File: controllers.py:208-210
Description: Simulação de disparo de e-mail/SMS/push feita via `print()` direto dentro da função de rota `criar_pedido`, sem nenhuma camada de serviço de notificação.
Impact: Mistura responsabilidade de orquestração HTTP com lógica de notificação, dificultando reuso/teste.
Recommendation: Extrair para uma função dedicada de notificação, chamada pelo controller.

### [MEDIUM] Validação inconsistente / tratamento de erro repetido
File: controllers.py (todas as funções, ex.: linhas 5-12, 14-22, 128-134)
Description: Cada função de controller repete o mesmo bloco `try/except Exception as e: return jsonify({"erro": str(e)}), 500`, em vez de um handler central.
Impact: Duplicação de código e inconsistência: erros internos vazam mensagens de exceção cruas ao cliente.
Recommendation: Centralizar em um error handler (`@app.errorhandler`), removendo os try/except individuais.

### [MEDIUM] Print como logging
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, database.py (implícito via prints em outros módulos)
Description: Uso de `print()` para logging de eventos de aplicação e erros, em vez de um logger configurado.
Impact: Sem níveis de log, sem timestamps padronizados, sem possibilidade de desabilitar/filtrar em produção.
Recommendation: Substituir por `logging` padrão do Python.

### [MEDIUM] Dependência sem pin de versão exata / sem verificação de deprecação
File: requirements.txt:1-2
Description: `flask==3.1.1` e `flask-cors==5.0.1` estão fixadas, mas o projeto não possui nenhum arquivo de lock (`requirements.txt` gerado sem hashes) nem processo de checagem de vulnerabilidades/deprecações.
Impact: Risco de builds inconsistentes entre ambientes e de não perceber quando uma dependência crítica for descontinuada.
Recommendation: Adicionar processo de auditoria de dependências (ex.: `pip-audit`) ao pipeline.

### [LOW] Nomenclatura genérica em variáveis de fluxo
File: models.py:139 (`item`), controllers.py:60-62 (`e` para exceção, aceitável, mas usado de forma inconsistente com `except Exception as e` vs. sem captura em outros lugares)
Description: Uso inconsistente de nomes curtos e genéricos em blocos de negócio (ex.: `id` sombreando builtin em várias funções).
Impact: Reduz legibilidade e facilita bugs sutis (shadowing do builtin `id`).
Recommendation: Renomear parâmetros para `produto_id`, `usuario_id`, `pedido_id` conforme o domínio.

### [LOW] Magic numbers no cálculo de desconto
File: models.py:256-262
Description: Faixas de desconto (10000, 5000, 1000) e percentuais (0.1, 0.05, 0.02) são literais soltos no meio da função `relatorio_vendas`.
Impact: Regra de negócio importante fica escondida em números mágicos, difícil de localizar/ajustar.
Recommendation: Extrair para constantes nomeadas (ex.: `FAIXA_DESCONTO_ALTO = 10000`).

### [LOW] Ausência de módulo de configuração centralizado
File: app.py:6-8, database.py:5
Description: Porta, path do banco (`"loja.db"`) e flags de debug são definidos diretamente nos arquivos de entrada, sem um módulo único de config.
Impact: Dificulta trocar configuração por ambiente (dev/test/prod) sem editar código.
Recommendation: Criar `config/settings.py` lendo de variáveis de ambiente.

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
code-smells-project/
├── app.py (composition root)
├── requirements.txt
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── models/
│   │   ├── database.py
│   │   ├── produto_model.py
│   │   ├── usuario_model.py
│   │   └── pedido_model.py
│   ├── controllers/
│   │   ├── produto_controller.py
│   │   ├── usuario_controller.py
│   │   ├── pedido_controller.py
│   │   ├── relatorio_controller.py
│   │   └── admin_controller.py
│   ├── views/
│   │   └── routes.py
│   └── middlewares/
│       └── error_handler.py
└── .claude/skills/refactor-arch/

## Validation
  ✓ Application boots without errors (python app.py)
  ✓ All endpoints respond correctly (/health, /produtos, /login, /pedidos, /relatorios/vendas, /pedidos/usuario/1 testados manualmente com curl)
  ✗ Zero anti-patterns remaining — 1 risco residual documentado e aceito conscientemente:
      endpoint /admin/reset-db permanece sem autenticação (finding HIGH), pois implementar um
      sistema de autenticação/autorização está fora do escopo de uma refatoração de arquitetura
      MVC e deve ser tratado como uma iteração futura dedicada.
================================
