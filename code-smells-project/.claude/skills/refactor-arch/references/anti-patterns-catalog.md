# Catálogo de Anti-Patterns

Escala de severidade usada em todo o catálogo:

- **CRITICAL**: falhas graves de arquitetura ou segurança que impedem funcionamento correto,
  expõem dados sensíveis, ou violam completamente a separação de responsabilidades.
- **HIGH**: fortes violações de MVC/SOLID que dificultam muito manutenção e testes.
- **MEDIUM**: padronização, duplicação, ou gargalos de performance moderada.
- **LOW**: legibilidade, nomenclatura, magic numbers.

Para cada anti-pattern: sinais de detecção (o que procurar no código) + severidade típica. A
severidade "típica" pode ser ajustada para cima/baixo conforme o impacto real observado.

---

### 1. God Class / God Method — **CRITICAL**
**Sinais:** um único arquivo/classe/função concentra SQL, regras de negócio, validação e
formatação de múltiplos domínios diferentes (ex.: um `models.py` de 300+ linhas cobrindo produtos,
usuários e pedidos; uma classe `AppManager` que faz tudo: DB, rotas, pagamento, auditoria).
**Impacto:** impossível testar em isolamento; qualquer mudança tem raio de efeito enorme.

### 2. Credenciais e Segredos Hardcoded — **CRITICAL**
**Sinais:** strings literais como `SECRET_KEY = "..."`, senhas de banco, API keys de gateway de
pagamento, credenciais SMTP, diretamente no código-fonte (não em variáveis de ambiente/`.env`).
Também conta se o segredo é **exposto** em uma resposta HTTP (ex.: endpoint de health check
retornando a secret key).

### 3. SQL Injection (Concatenação de Query) — **CRITICAL**
**Sinais:** montagem de queries SQL via concatenação de string ou f-string com dados vindos
diretamente do request (`"SELECT * FROM x WHERE id = " + str(id)`, `` `...${input}...` ``).
Inclui endpoints que aceitam SQL arbitrário do cliente e o executam diretamente.

### 4. Armazenamento de Senha em Texto Puro ou Hash Fraco/Deprecated — **CRITICAL**
**Sinais:** senha salva sem hash algum; ou hash com algoritmo criptograficamente quebrado/impróprio
para senhas (MD5, SHA1, "criptografia" caseira como Base64 repetido). Também conta se a senha (ou
seu hash) é incluída em respostas de API (`to_dict()` retornando o campo `password`).

### 5. Lógica de Negócio Dentro de Controller/Rota — **HIGH**
**Sinais:** cálculos de negócio, regras condicionais complexas, orquestração de múltiplos passos
(ex.: checkout completo: validar → cobrar → matricular → logar → notificar) implementados
diretamente dentro da função de rota, sem uma camada de serviço/controller separada.

### 6. Estado Global Mutável — **HIGH**
**Sinais:** variáveis em nível de módulo que são lidas/escritas por múltiplas requisições
concorrentes (cache global em objeto simples, contadores globais, conexão de banco única global
sem gerenciamento de ciclo de vida/pool).

### 7. Acoplamento Forte / Ausência de Injeção de Dependência — **HIGH**
**Sinais:** módulos importam e instanciam diretamente suas dependências (ex.: uma classe cria sua
própria conexão de banco no construtor, sem possibilidade de substituição/mock), dificultando
testes unitários.

### 8. Callback Hell / Pirâmide de Callbacks Aninhados — **HIGH**
**Sinais:** (tipicamente Node.js com drivers callback-based) múltiplos níveis de callbacks
aninhados dentro de uma única rota, misturando controle de fluxo assíncrono com lógica de negócio
e acesso a dados no mesmo bloco.

### 9. Queries N+1 — **MEDIUM**
**Sinais:** um loop `for` que, a cada iteração, dispara uma nova query ao banco (buscar o "pai" com
uma query e depois, para cada item relacionado, buscar individualmente em vez de usar JOIN/eager
loading/`IN (...)`). Muito comum em relatórios e listagens com dados relacionados.

### 10. Validação Ausente ou Inconsistente nas Rotas — **MEDIUM**
**Sinais:** algumas rotas validam tipo/formato/obrigatoriedade dos campos de entrada e outras não;
uso de `try/except`/`try/catch` genérico (bare `except:`/`catch (e) {}`) que engole qualquer erro
sem diferenciar validação de erro interno.

### 11. Duplicação de Código / Lógica Repetida — **MEDIUM**
**Sinais:** o mesmo trecho de lógica (ex.: cálculo de "atrasado"/overdue, cálculo de percentual,
validação de e-mail) reimplementado em múltiplos arquivos em vez de extraído para uma função
compartilhada — inclusive quando já existe uma função utilitária pronta para isso e ela não está
sendo usada (duplicação por não-reuso).

### 12. Middleware/Camada Transversal Mal Utilizada — **MEDIUM**
**Sinais:** tratamento de erros feito individualmente em cada rota (`try/except` repetido em toda
função) em vez de um middleware/error handler central; CORS, logging ou autenticação aplicados de
forma inconsistente entre rotas.

### 13. Nomenclatura Ruim / Variáveis Pouco Descritivas — **LOW**
**Sinais:** variáveis de uma ou duas letras sem contexto (`u`, `e`, `p`, `cc`, `cid`) em código de
domínio de negócio (fora de escopos triviais como índices de loop curtos).

### 14. Magic Numbers / Strings Soltas — **LOW**
**Sinais:** valores literais de negócio espalhados pelo código sem constante nomeada (limites de
desconto, thresholds de estoque, códigos de status repetidos como string literal em vários
lugares).

### 15. Falta de Camada de Configuração — **LOW/MEDIUM**
**Sinais:** valores de configuração (porta, path do banco, flags de debug/ambiente) espalhados
diretamente no arquivo de entrada em vez de centralizados em um módulo único de config.

---

## APIs e Dependências Deprecated (obrigatório verificar)

Sempre analise o manifest de dependências (`requirements.txt`, `package.json`, etc.) e o uso de
APIs no código, procurando por:

- **Dependências com versão significativamente desatualizada** frente à major atual conhecida do
  pacote (ex.: uma versão major antiga de um framework com EOL/fim de suporte).
- **APIs/métodos marcados como deprecated pela própria biblioteca/framework** (ex.: uso de
  callbacks de driver que hoje têm equivalente `async/await` ou `Promise` recomendado pela própria
  lib; uso de métodos de ORM descontinuados em favor de uma API mais nova).
- **Padrões criptográficos obsoletos** tratados como "deprecated" para fins de segurança mesmo que
  a função ainda exista na linguagem (MD5/SHA1 para senha, por exemplo — ver item 4).
- **Ausência de pinning de versão** (dependência sem versão fixada), que é um risco de build
  quebrar/mudar comportamento silenciosamente.

Reporte esses achados com severidade MEDIUM (funcional, mas datado/arriscado) ou HIGH quando a API
deprecated tiver implicação direta de segurança.
