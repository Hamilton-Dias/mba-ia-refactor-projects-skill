# Análise de Projeto — Heurísticas de Detecção

Este arquivo orienta a Fase 1 (Análise). O objetivo é identificar a stack e a arquitetura atual
**sem depender de nenhuma linguagem específica** — as heurísticas abaixo são organizadas por sinal
observável, não por framework.

## 1. Detecção de Linguagem

| Sinal | Linguagem provável |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, arquivos `.py` | Python |
| `package.json`, arquivos `.js`/`.ts`/`.mjs` | JavaScript/Node.js (ou TypeScript se houver `.ts`/`tsconfig.json`) |
| `pom.xml`, `build.gradle`, arquivos `.java` | Java |
| `go.mod`, arquivos `.go` | Go |
| `Gemfile`, arquivos `.rb` | Ruby |
| `composer.json`, arquivos `.php` | PHP |

## 2. Detecção de Framework

- **Python**: procure imports/dependências (`flask`, `django`, `fastapi`) no manifest e no código
  (`from flask import Flask`, `app = Flask(__name__)`, etc). A versão vem do manifest de
  dependências (`requirements.txt`, `pyproject.toml`).
- **Node.js**: leia `package.json` → `dependencies`/`devDependencies` (`express`, `koa`, `fastify`,
  `nestjs`). A versão declarada no `package.json` é a fonte da verdade (não assuma a versão
  instalada realmente, mas informe a declarada).
- Outras stacks: aplique o mesmo princípio — manifest de dependências é a fonte primária, uso no
  código confirma.

## 3. Detecção de Banco de Dados

Procure por:
- Import/uso de drivers (`sqlite3`, `psycopg2`, `mysql-connector`, `pymongo`, pacote `sqlite3`/`pg`
  em Node, etc.)
- ORMs (`SQLAlchemy`, `Flask-SQLAlchemy`, `Sequelize`, `Prisma`, `TypeORM`, `Django ORM`)
- Arquivos de schema/migrations (`CREATE TABLE`, arquivos em pastas `migrations/`)
- Classes de modelo ORM (`class X(db.Model)`, `class X(models.Model)`, `Schema` do Prisma)

Para listar as tabelas/entidades:
- Se houver `CREATE TABLE` explícito no código (comum em projetos sem ORM) → extraia o nome de
  cada tabela criada.
- Se houver classes de modelo ORM → o nome da classe/`__tablename__` é a entidade.

## 4. Detecção de Domínio da Aplicação

Infira o domínio a partir de:
- Nomes de rotas/endpoints (ex.: `/produtos`, `/pedidos`, `/checkout` → e-commerce)
- Nomes de tabelas/entidades (ex.: `courses`, `enrollments`, `payments` → LMS/plataforma de cursos)
- Nomes de arquivos e comentários/README do projeto, se existirem

Descreva o domínio em uma frase curta e específica (ex.: "API de E-commerce (produtos, pedidos,
usuários)", não apenas "API REST").

## 5. Mapeamento da Arquitetura Atual

Classifique em uma das categorias (ou descreva um híbrido):
- **Monolítica em poucos arquivos**: toda a lógica (rotas, regras de negócio, acesso a dados) está
  concentrada em 1-4 arquivos, sem separação de camadas.
- **Camadas parciais**: já existem pastas/módulos separando algo (ex.: `models/`, `routes/`), mas
  as responsabilidades vazam entre camadas (ex.: lógica de negócio pesada dentro das rotas, ou
  queries feitas diretamente no controller).
- **MVC bem aplicado**: separação clara e responsabilidades respeitadas (raro em projetos legados,
  mas é o alvo da Fase 3).

Não confunda "ter pastas" com "arquitetura correta" — sempre inspecione o conteúdo dos arquivos
antes de classificar.

## 6. Contagem de Arquivos

Conte apenas arquivos de código-fonte relevantes para a aplicação (ignore configs de IDE,
lockfiles, testes de terceiros, `node_modules`, ambientes virtuais, cache, `.git`). Esse número
deve ser exibido no resumo da Fase 1 e deve corresponder à realidade — reconte se o projeto for
alterado (ex.: reexecução da skill).
