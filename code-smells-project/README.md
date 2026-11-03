# code-smells-project

API de e-commerce em Python/Flask, refatorada e validada na issue 009. Os 19 métodos/caminhos originais foram preservados, com as correções de segurança e validação aprovadas por Lucas.

## Como rodar em um banco novo

Com as dependências de `requirements.txt` disponíveis na `.venv`:

```sh
mkdir -p instance
export DATABASE_PATH="$PWD/instance/loja.db"
export SECRET_KEY="$(.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')"
export SESSION_COOKIE_SECURE=false  # Apenas para desenvolvimento HTTP local.
.venv/bin/python -B -m flask --app app:create_app init-db
.venv/bin/python -B -m flask --app app:create_app create-admin
.venv/bin/python -B app.py
```

O servidor local usa `127.0.0.1:5000`. `init-db` cria tabelas sem apagar dados e sem usuários/senhas de exemplo. `create-admin` pede nome, email e senha, sem senha em argumentos de processo. Guarde uma chave estável fora do repositório para manter sessões entre reinícios; gerar outra chave invalida cookies anteriores. Em HTTPS, mantenha `SESSION_COOKIE_SECURE=true`, que é o padrão. Não há deploy preparado nesta issue.

Importar o módulo ou criar a aplicação não abre o banco. O caminho do banco e a chave são obrigatórios; debug e ferramentas administrativas ficam desabilitados por padrão. A pasta pai do banco deve existir.

## Acesso e contratos

| Operações | Acesso |
| --- | --- |
| Índice, health, leitura/busca de produtos, cadastro e login | Público |
| Criar/editar/excluir produtos, listar usuários/todos os pedidos, relatório e status | Administrador |
| Consultar usuário ou pedidos de usuário | Titular ou administrador |
| Criar pedido | Titular do `usuario_id` ou administrador |
| `/admin/query` e `/admin/reset-db` | Administrador e `ADMIN_TOOLS_ENABLED=true` |

`POST /login` recebe `{"email":"...","senha":"..."}`. O JSON mantém `dados`, `sucesso` e `mensagem`, acrescentando `csrf_token`, e estabelece cookie de sessão. Preserve o cookie nas chamadas seguintes e envie o token no header `X-CSRF-Token` em escritas autenticadas. Login inválido limpa a sessão anterior. A autorização lê o papel atual no banco, sem confiar no campo `tipo` do cadastro ou no corpo do pedido.

Senha e hash não aparecem nas representações de usuário. O health check não divulga chave, debug ou caminho do banco. Falta de identidade retorna 401; falta de permissão ou CSRF inválido, 403; entrada inválida, 400; recurso ausente, 404; falhas internas, 500 sem detalhes SQL. Nome/categoria são validados igualmente em POST e PUT. Quantidades são inteiros positivos; demanda repetida é somada para conferir estoque, preservando as linhas do pedido.

O frontend no mesmo domínio não precisa de CORS. Para outro domínio, configure `CORS_ORIGINS` com origens explícitas separadas por vírgula. O cliente precisa enviar cookies e CSRF. Curinga não é aceito.

As ferramentas administrativas preservam a funcionalidade original, inclusive SQL arbitrário para administrador confiável. Quando habilitadas, podem contornar regras de domínio, expor dados do banco ou apagar todo o conteúdo. Não são necessárias ao uso comum da API. Reset não repovoa tabelas nem cria novo administrador automaticamente.

## Banco legado e senhas

Não execute migração no banco original sem backup, conferência de formato e teste em cópia. A API não aceita senha legada em texto puro como alternativa ao hash. Antes de liberar tráfego ou criar novos usuários em uma base legada integralmente em texto puro, execute **na cópia configurada**:

```sh
.venv/bin/python -B -m flask --app app:create_app migrate-passwords --from-plaintext
```

A opção declara que todos os registros dessa base estão no formato legado. A migração é transacional e registra um marcador; uma repetição não reaplica hashes. Não use em bases mistas ou já com hashes sem o marcador. A validação da issue usou apenas dados sintéticos, sem migrar o `loja.db` existente. Emails duplicados continuam permitidos como no legado; o login procura a combinação de email e senha, sem descartar contas posteriores. Se as credenciais forem idênticas, permanece a primeira conta por ID.

## Estrutura MVC

```text
app.py               # composição e execução
config.py            # configuração por ambiente
database.py          # conexão, esquema e comandos explícitos
security.py          # sessão, titular/admin e CSRF
errors.py            # tradução central de erros
routes/              # mapa de métodos/caminhos e políticas
controllers/         # entrada HTTP e coordenação
models/              # persistência e regras por domínio
views/               # campos públicos do JSON
tests/               # contratos e regressões em banco temporário
tools/validate_http.py
```

O pedido confirma itens e estoque numa transação única, com rollback em erro. A listagem usa duas consultas de dados, independentemente da quantidade de pedidos/itens, mais a consulta de identidade no endpoint protegido. Descontos, representação monetária REAL e estados originais foram preservados. Cancelar um pedido continua sem repor estoque automaticamente, pois o original apenas imprimia uma notificação; essa regra não foi redesenhada.

## Verificação

```sh
.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s tests -v
.venv/bin/python -B tools/validate_http.py
```

São 41 testes com SQLite real, incluindo os 19 endpoints, autorização/CSRF, SQL, hashes, migração, rollback, concorrência, consulta em conjunto e limites numéricos. O utilitário HTTP sobe um subprocesso em porta efêmera de `127.0.0.1`, usa banco temporário, confere persistência e encerra o servidor. Pode exigir permissão para abrir porta local no sandbox.

Para repetir o HTTP original, extraia os quatro módulos da revisão `478f362d9de8969ec41905b9dd9c5077a478daf0` para uma pasta temporária e passe `--source /copia/original --legacy`. O utilitário nunca deve receber uma fonte não confiável.

Relatório, comparação manual, checklist e limites: [auditoria](../reports/audit-project-1.md). Evidências sem credenciais: [antes](../reports/evidence/project-1-http-before.json), [depois](../reports/evidence/project-1-http-after.json) e [resumo](../reports/evidence/project-1-validation.json). Os resultados não representam auditoria de produção, teste de carga ou validação dos outros projetos.
