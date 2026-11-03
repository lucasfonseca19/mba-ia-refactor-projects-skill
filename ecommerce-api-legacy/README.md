# ecommerce-api-legacy

API de cursos, matrículas e checkout em JavaScript/CommonJS, Express4 e sqlite3. Refatorada pela skill `refactor-arch` na issue010 após auditoria e aprovação humana.

## Executar

Requer Node.js22 ou superior. Validado com Node24.20.0 e npm11.19.0. Dependências: Express4.22.1 e sqlite3 5.1.7 (lockfile). Em uma instalação nova: `npm ci`.

Defina no terminal `ADMIN_API_TOKEN` com um valor aleatório de pelo menos32 caracteres, sem espaços. Não versionar nem compartilhar esse valor. Depois:

```sh
npm start
```

Servidor padrão em `http://127.0.0.1:3000`. `HOST` e `PORT` configuram endereço/porta. Sem token válido, o boot falha. Nenhum segredo padrão foi incluído.

O banco é **somente em memória** por instância. Reiniciar apaga os dados; não há migração automática de base real. O esquema é preparado antes de abrir a porta. Sem `SEED_DEMO=1`, inicia vazio. Para carregar demonstração sintética, defina também `DEMO_PASSWORD` com uma senha local escolhida por você e execute:

```sh
SEED_DEMO=1 npm start
```

A demonstração cria cursos1/2 (997 e497), usuário `demo@example.test` com senha protegida e uma matrícula/pagamento997. Não há senha padrão. `DEMO_PASSWORD` deve ter até1024 bytes e não ser vazia. O pagamento permanece simulado: texto de cartão com prefixo4 aprova; outro prefixo recusa. Use somente dados sintéticos. Nenhuma cobrança ou mensagem real é executada.

## Contratos

| Operação | Entrada/permissão | Resultado |
|---|---|---|
| POST /api/checkout | JSON usr, eml, pwd, c_id, card; email existente exige senha correta |200 com msg e enrollment_id;400 inválido/recusado;401 senha incorreta/legada;404 curso ausente/inativo |
| GET /api/admin/financial-report | Authorization: Bearer com ADMIN_API_TOKEN |200 array com course, revenue e students (student/paid);401 sem credencial válida |
| DELETE /api/users/:id | Mesmo Bearer administrativo; ID inteiro positivo |200 JSON msg;400 ID inválido;404 usuário ausente;409 usuário com matrícula;401 sem credencial válida |

Falhas internas retornam500 com mensagem genérica. Corpo JSON inválido400 e corpo além do limite do parser413. Strings de nome/email/senha/cartão devem ser não vazias; limites em bytes200/254/1024/128. `c_id` aceita inteiro positivo seguro ou sua representação decimal; os nomes públicos antigos foram preservados. Não há normalização silenciosa de email nem novos endpoints de login.

Usuário novo, matrícula, pagamento e auditoria são confirmados ou desfeitos em conjunto. A fila por conexão impede sobreposição de transações; cache por instância recebe apenas título após commit. Exclusão bloqueia qualquer matrícula vinculada para preservar histórico. Senhas são armazenadas como `scrypt$salt$verificador`, com salt aleatório16 bytes, N16384/r8/p1 e chave64 bytes. Formatos legados são rejeitados e precisam de redefinição explícita; não há conversão por adivinhação.

A autenticação administrativa é um token compartilhado configurado no ambiente, adequado ao escopo desta demonstração. Rotação/distribuição do token e TLS pertencem à operação; não substitui gestão completa de identidades. Integrações reais precisariam de desenho próprio de idempotência/compensação, pois rollback SQL não desfaz cobrança.

## Estrutura

```text
src/
  app.js                  factory de composição, sem boot no import
  server.js               boot e encerramento
  config/                 configuração validada
  database/               conexão, fila, transação, esquema e demo explícita
  models/                 persistência e relatório
  services/checkout.js    coordenação transacional
  controllers/            adaptação HTTP e validação
  routes/                 três métodos/caminhos originais
  presenters/             projeções públicas
  middleware/             admin e tratamento de erros
  security/               proteção/verificação de senha
```

## Skill e validação

A cópia local está em `.agents/skills/refactor-arch/`, idêntica ao Projeto1. Para nova auditoria, trabalhar nesta pasta e pedir explicitamente `$refactor-arch`. A execução desta issue leu e seguiu a skill local; descoberta automática na interface não foi comprovada. Não é necessário alterar a skill só por trocar de stack.

```sh
npm test
```

São38 testes, com SQLite descartável e HTTP em127.0.0.1/porta efêmera, incluindo rollback, concorrência, autorização, senha, relatório, erros e boot/encerramento do processo. Não usam banco real nem integração externa. Não há dependências de teste adicionais. O aviso npm sobre configuração de usuário `timeout`, observado no primeiro comando, não pertence ao projeto; a execução de evidência usou `NPM_CONFIG_USERCONFIG=/dev/null npm test`, sem editar a configuração pessoal.

Coletores opcionais (gravam evidências sanitizadas nos caminhos informados):

```sh
npm run test:baseline
node tests/after.js ../reports/evidence/project-2-http-after.json
node tests/process-smoke.js ../reports/evidence/project-2-process-smoke.json
```

A baseline usa `git show` da revisão original registrada em tests/helpers.js e exige o histórico Git local; carrega apenas AppManager/utils com console isolado, esquema original e fixtures sintéticas. Não inicia o app.js original. Esses coletores encerram servidores e bancos; nenhum log bruto com cartão/chave é salvo.

Relatório, checklist e limitações: [audit-project-2.md](../reports/audit-project-2.md). Evidências: [antes](../reports/evidence/project-2-http-before.json), [depois](../reports/evidence/project-2-http-after.json), [processo](../reports/evidence/project-2-process-smoke.json) e [resumo](../reports/evidence/project-2-validation.json).

A validação não cobre carga, produção, migração, pagamentos reais, política de reset de senhas ou vulnerabilidades transitivas. O relatório não afirma ausência universal de problemas.
