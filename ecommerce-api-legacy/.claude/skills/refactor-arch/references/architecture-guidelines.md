# Guidelines de Arquitetura — MVC Alvo

Estas regras definem o "MVC" que a Fase 3 deve produzir, de forma agnóstica de linguagem. Adapte
nomes de pasta à convenção idiomática da stack (ex.: Node normalmente usa `routes/` em vez de
`views/` para APIs REST — isso é aceitável, desde que a responsabilidade seja a mesma).

## Estrutura de diretórios alvo (genérica)

```
src/
├── config/          # configuração central: env vars, constantes, factory de conexão
├── models/          # acesso a dados e regras de validação de dado (1 arquivo por entidade/domínio)
├── views/  (routes/) # definição de rotas HTTP: parsing de request, chamada ao controller, serialização de response
├── controllers/      # orquestração do caso de uso: chama models/services, aplica regras de negócio, decide o fluxo
├── middlewares/       # cross-cutting: error handler central, CORS, logging, auth
└── (services/, se necessário para lógica de domínio complexa reutilizável por múltiplos controllers)
app.py / app.js (ou index.*)  # composition root: monta a aplicação, injeta dependências, registra rotas
```

## Responsabilidade de cada camada

### Config
- Único lugar que lê variáveis de ambiente / arquivo `.env`.
- Nenhum outro módulo deve conter uma credencial, chave ou string de conexão literal.
- Deve expor valores com defaults seguros para desenvolvimento, nunca defaults "prontos para
  produção" com segredos reais.

### Models
- Toda leitura/escrita de dados passa por aqui — nenhuma rota ou controller executa SQL/queries
  diretamente.
- Toda query com parâmetros do usuário usa parametrização (placeholders `?`/`%s`, ou métodos do
  ORM) — **nunca concatenação de string**.
- Retorna dados já formatados como estruturas simples (dict/objeto) ou instâncias de modelo —
  não retorna cursors/objetos de baixo nível para fora da camada.
- Não contém lógica de apresentação HTTP (sem `jsonify`, sem `res.json`, sem status code HTTP
  aqui).

### Views / Routes
- Define os endpoints e métodos HTTP.
- Faz apenas: parse do request (body/query/params) → chama o controller → serializa a resposta.
- Não contém regra de negócio, não acessa o banco diretamente.
- Um arquivo de rotas por domínio/recurso quando o projeto crescer (ex.: `produto_routes`,
  `usuario_routes`), registrado no composition root.

### Controllers
- Recebe dados já parseados da view, orquestra a chamada aos models (e services, se existirem).
- Aplica regras de negócio e validação de domínio (o que é uma regra de negócio válida, não apenas
  "o campo existe" — isso pode estar na borda da view/schema também, mas a decisão de fluxo é do
  controller).
- Traduz o resultado (incluindo erros esperados) em algo que a view consiga serializar — não
  conhece detalhes de framework HTTP quando possível (para ser testável isoladamente).

### Middlewares
- Um error handler central captura exceções não tratadas e retorna uma resposta padronizada —
  elimina o `try/except`/`try/catch` repetido em toda rota.
- CORS, autenticação e logging de requisição, quando existentes, ficam aqui, aplicados de forma
  consistente a todas as rotas relevantes (não ad-hoc por rota).

### Composition Root (entry point)
- É o único lugar onde tudo é "montado": cria a app, injeta config, registra middlewares e rotas,
  inicializa o banco.
- Deve ser enxuto — se o entry point tem mais de ~40-50 linhas de lógica de negócio, é sinal de que
  algo vazou para o lugar errado.

## Critérios de "MVC bem aplicado" (o que a Fase 3 deve garantir)

1. Nenhuma credencial/segredo hardcoded em nenhum arquivo.
2. Nenhuma query SQL concatenada com dado externo.
3. Nenhuma lógica de negócio dentro de uma função de rota.
4. Nenhum SQL/acesso a dado fora da camada de model.
5. Tratamento de erro centralizado, não duplicado rota a rota.
6. Toda senha armazenada com hash forte e nunca retornada em respostas de API.
7. Sem estado global mutável compartilhado entre requisições sem controle.
8. Endpoints originais preservados em contrato (rota, verbo, formato de entrada/saída), exceto
   quando o próprio relatório de auditoria justificou remoção por risco de segurança inaceitável.

## Adaptação a projetos parcialmente organizados

Quando o projeto já possuir pastas como `models/`, `routes/`, `services/` (caso comum em projetos
"médios"), a Fase 3 não deve recriar a estrutura do zero. Em vez disso:
- Mantenha a convenção de nomes já usada pelo projeto.
- Extraia lógica de negócio que está indevidamente dentro das rotas para dentro de um controller
  ou service.
- Corrija os problemas pontuais identificados no relatório (N+1, credenciais, hashing fraco,
  duplicação) sem mover arquivos que já estão no lugar correto.
