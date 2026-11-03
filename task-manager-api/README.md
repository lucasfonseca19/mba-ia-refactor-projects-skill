# Task Manager API

API Flask de tarefas, usuários, categorias e relatórios, refatorada na issue 011. As rotas adaptam HTTP; os serviços concentram operações, validações e consultas; os models representam os dados e regras coesas. `middleware/` aplica a política de acesso.

## Executar

Requer Python e as dependências de `requirements.txt` em uma `.venv`. Configure um segredo próprio em `TASK_SECRET_KEY` antes de qualquer comando da aplicação. `TASK_DATABASE_URI` é opcional; sem ela, usa o SQLite `instance/tasks.db`. Em novo ambiente, inicialize as tabelas e inicie a API:

```bash
export TASK_SECRET_KEY='<segredo-local-aleatório>'
.venv/bin/flask --app app init-db
.venv/bin/python app.py
```

O servidor de desenvolvimento escuta em `127.0.0.1:5000`, com debug desativado. O import da aplicação não cria tabelas. Para obter o primeiro administrador em banco sem administradores, configure `TASK_ADMIN_NAME`, `TASK_ADMIN_EMAIL` e `TASK_ADMIN_PASSWORD` no ambiente e execute `.venv/bin/flask --app app bootstrap-admin`. O comando recusa a criação se já houver administrador. Não coloque segredos em arquivos versionados ou comandos compartilhados.

`seed.py` **apaga os usuários, tarefas e categorias existentes** antes de recriar exemplos. Use-o apenas em banco descartável, explicitamente configurado; ele não é necessário para iniciar a API.

## Autenticação e contratos

`POST /login` devolve um token assinado com duração de uma hora. Nas rotas protegidas, envie `Authorization: Bearer <token>`. Senhas não são retornadas; hashes MD5 antigos são atualizados após login bem-sucedido. Contas legadas que não fizerem login não são migradas automaticamente. Trocar a senha invalida tokens anteriores e exige novo login.

A raiz, `/health`, login e cadastro de usuários comuns são públicos. Um usuário autenticado acessa seu perfil e tarefas; `manager` pode consultar usuários, tarefas e relatórios; `admin` administra todos os recursos. Alterações de papel, ativação, exclusão de usuário e escrita em categorias exigem administrador. Contagens de categorias para usuários comuns abrangem apenas suas próprias tarefas. A alteração do próprio perfil por manager permanece permitida.

O serviço SMTP é opcional e não é chamado pelas rotas. Para uso explícito, configure `TASK_SMTP_HOST`, `TASK_SMTP_PORT`, `TASK_SMTP_USER` e `TASK_SMTP_PASSWORD`; não há credenciais padrão.

## Testes

No macOS, `tests/run_sandbox_macos.sh` cria uma cópia temporária do projeto e da `.venv`, nega acesso ao diretório original e à rede usando `sandbox-exec`, e executa os testes com SQLite em memória. Ele testa a barreira antes de iniciar a aplicação. Em ambientes que impeçam `sandbox-exec` ou cujo Python dependa de arquivos dentro do diretório pessoal, o comando deve falhar; prepare uma barreira equivalente antes de executar testes. Alguns ambientes gerenciados podem exigir autorização para criar a barreira.

```bash
tests/run_sandbox_macos.sh
```

`tests/run_isolated.py` é uma etapa interna que exige cópia sob diretório temporário e confirma SQLite em memória, mas **não cria uma barreira do sistema operacional por conta própria**. Não execute a suíte diretamente no projeto original. Os testes incluem tentativas negativas de usar um banco em arquivo, autenticação, permissões, contratos e persistência sintética.


## Revisão de validação da issue 012

A suíte foi ampliada de 32 para 38 testes. O middleware já recusa corpos JSON que não sejam objetos antes do login e das escritas. A revisão corrigiu referências, filtros e IDs de rota que excediam o intervalo aceito pelo SQLite e geravam erro interno: agora retornam 400 antes da consulta. Inteiros no limite suportado e filtros com zeros à esquerda continuam aceitos.

O F-08 está resolvido no escopo identificado e testado de corpos, tipos, filtros e fronteiras numéricas. Isso não afirma validação exaustiva de todas as entradas possíveis. [Relatório detalhado](../reports/audit-project-3.md) e [evidências atuais](../reports/evidence/project-3-quality-validation.json) separam esta execução dos registros de HTTP e boot da issue 011. O comando de teste continua sendo `tests/run_sandbox_macos.sh`.
