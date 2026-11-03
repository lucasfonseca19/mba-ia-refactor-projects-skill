# Auditoria arquitetural: Projeto 3

## Identificação e escopo

- Data: 30/10/2026. Revisão auditada: `99e2966ce7e8c562fafef5a971f441f4ac2c5c18`.
- Projeto: task-manager-api. Python 3.13.7, Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.6 instalado; SQLite.
- Domínio: usuários, tarefas, categorias e relatórios. Arquitetura parcialmente organizada em models, routes, services e helpers, com regras e persistência concentradas nas rotas.
- Escopo: 15 arquivos Python próprios, incluindo seed e inicializadores, e manifesto e README. Análise estática; banco existente e integrações excluídos.
- Interfaces: GET /, GET /health, POST /login, GET/POST /users, GET/PUT/DELETE /users/<id>, GET /users/<id>/tasks, GET/POST /tasks, GET/PUT/DELETE /tasks/<id>, GET /tasks/search, GET /tasks/stats, GET /reports/summary, GET /reports/user/<id>, GET/POST /categories, PUT/DELETE /categories/<id>.


### Inventário de interfaces com origem

Inventário reconstruído em leitura na revisão original; contagem: **22 métodos/caminhos**, sem contar HEAD/OPTIONS automáticos.

| Método | Caminho | Origem na revisão original |
| --- | --- | --- |
| GET | `/health` | `app.py:23-24` |
| GET | `/` | `app.py:27-28` |
| GET | `/users` | `routes/user_routes.py:11-25` |
| GET | `/users/<int:user_id>` | `routes/user_routes.py:28-40` |
| POST | `/users` | `routes/user_routes.py:43-90` |
| PUT | `/users/<int:user_id>` | `routes/user_routes.py:93-132` |
| DELETE | `/users/<int:user_id>` | `routes/user_routes.py:135-151` |
| GET | `/users/<int:user_id>/tasks` | `routes/user_routes.py:154-183` |
| POST | `/login` | `routes/user_routes.py:186-211` |
| GET | `/tasks` | `routes/task_routes.py:12-63` |
| GET | `/tasks/<int:task_id>` | `routes/task_routes.py:66-83` |
| POST | `/tasks` | `routes/task_routes.py:86-154` |
| PUT | `/tasks/<int:task_id>` | `routes/task_routes.py:157-223` |
| DELETE | `/tasks/<int:task_id>` | `routes/task_routes.py:226-238` |
| GET | `/tasks/search` | `routes/task_routes.py:241-271` |
| GET | `/tasks/stats` | `routes/task_routes.py:274-299` |
| GET | `/reports/summary` | `routes/report_routes.py:13-101` |
| GET | `/reports/user/<int:user_id>` | `routes/report_routes.py:104-155` |
| GET | `/categories` | `routes/report_routes.py:158-165` |
| POST | `/categories` | `routes/report_routes.py:168-188` |
| PUT | `/categories/<int:cat_id>` | `routes/report_routes.py:191-209` |
| DELETE | `/categories/<int:cat_id>` | `routes/report_routes.py:212-223` |

## Resumo

| Severidade | Quantidade |
| --- | ---: |
| CRITICAL | 2 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 2 |

Total: **10 achados**. Diagnóstico estático, sem reprodução anterior à aprovação. Oito achados manuais confirmados; F-04 e F-08 adicionais. A comparação não foi cega: a análise manual estava disponível.

## Achados

Os diagnósticos, IDs, severidades e locais abaixo pertencem à revisão original `99e2966`. Em 03/11/2026, na issue 012, sua apresentação foi expandida para os campos do template a partir do relatório resumido, da análise manual, do código original e das evidências versionadas. Essa expansão é um **detalhamento retrospectivo**, não uma transcrição da conversa original nem prova de que todos estes detalhes já constavam do plano antes da aprovação. Os testes citados são evidências posteriores.

### F-01 · CRITICAL · Verificadores de senha expostos e MD5

- **Padrão:** AP-02/AP-03.
- **Localização:** `models/user.py:16-32; routes/user_routes.py:27-40,42-86,185-211` (revisão original).
- **Evidência:** A projeção to_dict inclui o campo password e o model define/verifica MD5 direto, sem salt. Os handlers devolvem essa projeção ao cliente.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Exposição de verificador inadequadamente protegido permite tentativas offline sobre credenciais. CRITICAL corresponde à exposição de dados sensíveis na escala do curso.
- **Correção proposta:** Excluir o campo das respostas e adotar derivação própria para senhas; a proposta registrada prevê migrar MD5 após login válido.
- **Mudança observável:** Respostas deixam de incluir password. Login válido atualiza o verificador legado; contas sem login continuam no formato anterior.
- **Verificação proposta / rastreabilidade posterior:** test_legacy_login_migrates_hash_and_hides_password; test_password_change_revokes_existing_token.
- **Dependências/incertezas:** A migração depende da senha correta fornecida no login. Não houve conversão geral de contas nem migração do banco local.
- **Correspondência manual:** P3-01.

### F-02 · CRITICAL · Ausência de autenticação e autorização

- **Padrão:** AP-04.
- **Localização:** `routes/user_routes.py:92-148,185-211; app.py:15-20` (revisão original).
- **Evidência:** O login emite texto fixo com ID como token, mas não há verificação de identidade/papel antes das operações sensíveis.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Operações administrativas, exclusão e acesso a recursos ficam disponíveis sem comprovação de permissão. A ausência de barreira justifica CRITICAL; proteções externas não foram demonstradas.
- **Correção proposta:** Usar credencial verificável e aplicar as políticas de papel e titularidade aprovadas; preservar métodos/caminhos.
- **Mudança observável:** Rotas protegidas passam a exigir Bearer válido e podem retornar 401/403. A política implementada está descrita no README da API.
- **Verificação proposta / rastreabilidade posterior:** test_user_cannot_access_other_user_or_elevate_role; test_manager_can_read_but_not_write_administrative_data; test_head_respects_user_resource_permissions.
- **Dependências/incertezas:** A proposta original em disco resume as políticas como aprovadas na conversa. A descrição atual do código não reconstrói uma transcrição integral dessa conversa.
- **Correspondência manual:** P3-02.

### F-03 · HIGH · Responsabilidades concentradas nas rotas

- **Padrão:** AP-05.
- **Localização:** `routes/task_routes.py:85-154; routes/report_routes.py:12-101` (revisão original).
- **Evidência:** Handlers interpretam HTTP, validam entrada, consultam referências, calculam regras, fazem commit e formatam resposta. Há models e blueprints reais, mas a coordenação e a persistência permanecem concentradas nas rotas.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Acoplamento dificulta testar e reutilizar operações fora do handler. HIGH reflete a violação de responsabilidades, sem presumir que os arquivos devam ser integralmente substituídos.
- **Correção proposta:** Separar adaptação HTTP, coordenação, regras e consultas; aproveitar blueprints e models existentes.
- **Mudança observável:** Preservar contratos válidos e incorporar somente mudanças de segurança/validação aprovadas. Serviços passam a executar operações e consultas.
- **Verificação proposta / rastreabilidade posterior:** test_all_original_endpoints_and_persistence; test_task_domain_rejects_invalid_priority_without_http; inspeção de routes/, services/ e models/.
- **Dependências/incertezas:** O MVC foi adaptado: blueprints são adaptadores HTTP e serviços coordenam operações/consultas. Serialização continua em models e adaptadores; não se afirma separação absoluta por pastas.
- **Correspondência manual:** P3-03.

### F-04 · HIGH · Configuração sensível e debug

- **Padrão:** Configuração/AP-02.
- **Localização:** `app.py:11-15,33-34; services/notification_service.py:5-20` (revisão original).
- **Evidência:** O entry point configura segredo literal, debug e escuta em todas as interfaces. O serviço de notificação contém configuração e credenciais fixas; seus valores foram omitidos.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Configuração sensível no código e debug exposto ampliam risco operacional. HIGH considera que não foi identificado uso de SMTP pelas rotas nem comprovada a validade das credenciais.
- **Correção proposta:** Extrair configuração para ambiente, desabilitar debug por padrão e substituir qualquer integração externa por cenário sintético na validação.
- **Mudança observável:** TASK_SECRET_KEY passa a ser obrigatória; TASK_DATABASE_URI permite escolher destino. O boot de desenvolvimento usa loopback; SMTP não tem credenciais padrão.
- **Verificação proposta / rastreabilidade posterior:** test_configuration_uses_environment; test_import_does_not_create_database; test_smtp_credentials_are_not_hardcoded; registro de boot da issue 011.
- **Dependências/incertezas:** SMTP real não foi exercitado. O teste sem configuração só verifica a recusa de envio; não equivale a teste integrado de servidor SMTP.
- **Correspondência manual:** Adicional.

### F-05 · MEDIUM · Consultas por elemento

- **Padrão:** AP-08.
- **Localização:** `routes/report_routes.py:53-68,157-165; routes/user_routes.py:10-25` (revisão original).
- **Evidência:** O relatório consulta tarefas por usuário; categorias fazem contagens por elemento; a listagem de usuários acessa relação por usuário.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Quantidade de acessos cresce com os resultados. MEDIUM representa gargalo potencial confirmado por fluxo de consultas, sem benchmark de latência.
- **Correção proposta:** Agregar ou carregar dados em conjunto, mantendo campos, escopo de acesso e resultados vazios.
- **Mudança observável:** As projeções continuam disponíveis sem consultas adicionais por cada linha nos caminhos identificados.
- **Verificação proposta / rastreabilidade posterior:** test_category_and_user_lists_do_not_query_per_row; test_category_counts_are_scoped_for_regular_users; inspeção da agregação de produtividade em report_service.
- **Dependências/incertezas:** A contagem de consultas automatizada cobre listagens de categorias e usuários. O relatório de produtividade tem agregação inspecionada; não se afirma benchmark nem contagem exaustiva de todas as consultas.
- **Correspondência manual:** P3-04.

### F-06 · MEDIUM · Regra de atraso duplicada

- **Padrão:** AP-09.
- **Localização:** `models/task.py:50-60; routes/task_routes.py:30-39,71-80; routes/user_routes.py:171-180; routes/report_routes.py:33-42` (revisão original).
- **Evidência:** Existe Task.is_overdue, mas handlers repetem comparações de prazo e status em vez de reutilizar a regra.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Uma alteração de regra exige sincronizar várias cópias. MEDIUM refere-se à manutenção; divergência funcional entre todas as cópias não foi demonstrada.
- **Correção proposta:** Centralizar o conceito de atraso no model e reutilizá-lo nas listagens/relatórios.
- **Mudança observável:** Preservar exclusão de tarefas done/cancelled e tratamento de prazo ausente.
- **Verificação proposta / rastreabilidade posterior:** test_overdue_rule_avoids_deprecated_datetime; inspeção das chamadas a Task.is_overdue nos serviços.
- **Dependências/incertezas:** O teste específico existente verifica tarefa pendente atrasada e ausência de DeprecationWarning; cobertura completa de todas as fronteiras temporais não foi demonstrada.
- **Correspondência manual:** P3-05.

### F-07 · MEDIUM · APIs deprecated/legacy

- **Padrão:** AP-11.
- **Localização:** `models/task.py:15-16; routes/task_routes.py:30-32,65-67; demais usos registrados na análise manual` (revisão original).
- **Evidência:** datetime.utcnow aparece em defaults/comparações e Query.get em consultas por chave. As versões registradas foram Python 3.13.7 e SQLAlchemy 2.1.6.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Dívida de compatibilidade e padronização, sem alegar que as APIs tenham sido removidas ou impeçam o boot. MEDIUM corresponde ao uso obsoleto/legacy.
- **Correção proposta:** Adotar datetime.now(UTC) com conversão explícita compatível com dados existentes e Session.get para consultas por chave.
- **Mudança observável:** Preservar representação persistida UTC naive e formato das datas; substituir o mecanismo de obtenção do instante UTC.
- **Verificação proposta / rastreabilidade posterior:** test_overdue_rule_avoids_deprecated_datetime; test_detail_avoids_legacy_query_get; inspeção dos usos próprios.
- **Dependências/incertezas:** Fontes oficiais e datas da conferência original aparecem na tabela de depreciações. Não houve migração de dados temporais nem auditoria de todas as dependências transitivas.
- **Correspondência manual:** P3-06.

### F-08 · MEDIUM · Validação de tipos insuficiente

- **Padrão:** Validação de entrada.
- **Localização:** `routes/task_routes.py:110-114,257-264; routes/report_routes.py:190-202` (revisão original).
- **Evidência:** Comparações de prioridade e conversão int de filtros não validam previamente o tipo/formato. A atualização de categoria usa o corpo sem garantir objeto.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Entradas malformadas podem virar exceções internas em vez de erro de cliente. MEDIUM reflete validação ausente, sem atribuir a ela todos os possíveis problemas de entrada.
- **Correção proposta:** Validar corpo, tipos, limites e referências antes da persistência; retornar 400 sem alterações para entradas inválidas.
- **Mudança observável:** Entradas incorretas passam a retornar 400. Na revisão da issue 012, inteiros acima do intervalo aceito pelo SQLite também passam de 500 para 400 nos caminhos comprovados.
- **Verificação proposta / rastreabilidade posterior:** test_invalid_task_priority_is_a_client_error; test_invalid_search_filter_is_a_client_error; test_category_invalid_body_is_a_client_error; seis testes adicionais da issue 012 na seção de revisão.
- **Dependências/incertezas:** A Fase 3 da issue 011 registrou tratamento parcial. A revisão posterior amplia a cobertura e descreve um fechamento limitado ao mecanismo/casos identificados, sem afirmar validação universal. O diagnóstico isolado de falha HTTP no login foi retirado.
- **Correspondência manual:** Adicional.

### F-09 · LOW · Constantes de domínio não reutilizadas

- **Padrão:** AP-12.
- **Localização:** `routes/task_routes.py:96-114; utils/helpers.py:110-116` (revisão original).
- **Evidência:** Limites de título e prioridade são escritos diretamente, embora parte das constantes já exista nos helpers.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Ruído e risco de divergência entre definições; LOW representa clareza/manutenção. Os valores originais não foram declarados incorretos.
- **Correção proposta:** Reutilizar constantes existentes e preservar valores e operadores das regras.
- **Mudança observável:** Sem alteração intencional dos limites válidos de título e prioridade.
- **Verificação proposta / rastreabilidade posterior:** inspeção de imports de helpers nos serviços; test_invalid_priority_types_and_bounds_do_not_modify_tasks.
- **Dependências/incertezas:** O intervalo de prioridade ainda é expresso localmente como 1 a 5; a refatoração reutiliza constantes existentes onde aplicáveis, sem declarar eliminação universal de todos os literais.
- **Correspondência manual:** P3-07.

### F-10 · LOW · Imports não usados

- **Padrão:** Código sem uso.
- **Localização:** `routes/task_routes.py:7; utils/helpers.py:3-7` (revisão original).
- **Evidência:** Imports dos módulos identificados não têm consumidores no escopo dos arquivos analisados.
- **Método e limite:** inspeção estática na Fase 2, sem execução anterior à aprovação. Reproduções e testes posteriores são identificados no complemento.
- **Impacto e severidade:** Ruído de manutenção, LOW; não se atribui ganho mensurado de desempenho à remoção.
- **Correção proposta:** Remover somente os imports dispensáveis identificados e conferir o boot.
- **Mudança observável:** Nenhuma mudança pública esperada.
- **Verificação proposta / rastreabilidade posterior:** inspeção dos imports identificados; suíte integrada; registro de boot da issue 011.
- **Dependências/incertezas:** Não remover imports por efeitos de registro, como inicializadores de models. Não se afirma análise universal de código morto.
- **Correspondência manual:** P3-08.


## APIs deprecated e cobertura documental

As fontes foram conferidas originalmente em 30/10/2026, conforme o registro da auditoria. A tabela organiza essa evidência histórica; não representa nova consulta online nesta revisão.

| Biblioteca e versão registrada | Símbolo e usos | Situação e substituto | Evidência oficial | Impactos e limites |
| --- | --- | --- | --- | --- |
| Python 3.13.7 | datetime.utcnow em models, rotas e seed | Deprecated desde 3.12; datetime.now(UTC) | [Python 3.13](https://docs.python.org/3.13/library/datetime.html#datetime.datetime.utcnow) | Substituição exige compatibilidade de fuso. UTC naive persistido foi preservado explicitamente. |
| SQLAlchemy 2.1.6 instalado | Query.get nas rotas originais | Legacy desde 2.0; Session.get | [SQLAlchemy 2.1](https://docs.sqlalchemy.org/en/21/orm/queryguide/query.html#sqlalchemy.orm.Query.get) | Foram substituídos os usos próprios identificados. A suíte confere detalhe de tarefa com LegacyAPIWarning como erro. |

Não foi demonstrada ausência universal de depreciações; dependências transitivas e todos os caminhos de bibliotecas não foram auditados integralmente.

## Proposta aprovada

Em 30/10/2026, o responsável autorizou seguir após revisão da auditoria na conversa. Escopo: F-01 a F-10; configuração explícita; rotas/controllers/models/serviços e apresentação coesos; credencial verificável; políticas de acesso conforme relatório apresentado; migração de MD5 após login válido; primeiro admin por comando explícito; UTC compatível com dados existentes; validação em banco e ambiente sintéticos; salvar este relatório. Endpoints originais preservados com mudanças aprovadas de autenticação, autorização, erro e campo de senha.


### Estrutura, etapas e contratos consolidados posteriormente

Antes: `app.py`, `database.py`, `seed.py`, `models/`, `routes/`, `services/notification_service.py` e helpers, totalizando 15 módulos próprios. Depois da issue 011: 24 módulos de produção, com `config.py`, `middleware/access_control.py`, serviços de usuários, tarefas, categorias, relatórios e tokens, além de `utils/time_utils.py`. Blueprints e models foram aproveitados.

A sequência registrada foi auditoria e aprovação, preparação de baseline, interrupção por incidente, reposição autorizada de exemplos, reforço da skill, retomada em cópia protegida, refatoração e validação. A organização por etapas aqui descrita não substitui nem redata a aprovação original.

Contratos implementados: público em raiz/health/login/cadastro comum; identidade verificável para rotas protegidas; titularidade para usuário comum; leitura ampliada para manager; administração para admin. JSON deixa de expor password; credenciais expiradas, inválidas ou revogadas são recusadas. A tabela de permissões detalhada está no README da API e no middleware; esta seção descreve o resultado do código.

Configuração foi extraída sem adicionar dependências nesta revisão. `TASK_SECRET_KEY` é exigida; `TASK_DATABASE_URI` aponta o banco; primeiro admin é criado por comando explícito. Seed, migração do banco local, SMTP real, deploy e publicação não entram automaticamente no escopo autorizado.

## Validação planejada

Cópia isolada em /private/tmp, banco sintético, sem SMTP real, linha de base e comparação após alterações para os 22 métodos/caminhos. Verificar persistência, erros, autorização, propriedade, senhas legadas, datas e contagem de consultas; boot real e encerramento do processo. Nenhum banco real deve ser alterado. Situação e limitações serão acrescentadas após execução.


### Matriz de verificação consolidada na issue 012

O plano original em disco é o parágrafo acima. A matriz abaixo foi consolidada posteriormente a partir dos JSONs de 24 requisições antes/depois e dos testes versionados; não foi apresentada como se já existisse antes da aprovação. Os status originais são observados nos JSONs. Esses arquivos não preservam todos os corpos/payloads, portanto não permitem alegar equivalência integral das respostas nem reconstrução exata de todos os dados históricos.

O teste `test_all_original_endpoints_and_persistence` e os testes específicos citados complementam as verificações, com dados em memória. Estado de cada linha: **HTTP registrado na issue 011 e integração exercitada na suíte atual**; requisições atuais via Flask test client não são novo HTTP real.

| Endpoint/interface | Pré-condição e entrada | Status original registrado | Esperado/registrado depois | Como conferir resposta e efeito | Estado |
| --- | --- | --- | --- | --- | --- |
| `GET /health` | Público; banco configurado | 200 | 200 com mudanças aprovadas | Prontidão; boot real registrado separadamente | HTTP 011 + suíte atual |
| `GET /` | Público | 200 | 200 com mudanças aprovadas | Resposta de identificação; status integrado | HTTP 011 + suíte atual |
| `GET /users` | Admin autenticado depois | 200 | 200 com mudanças aprovadas | Status e listagem com contagem de consultas | HTTP 011 + suíte atual |
| `GET /users/<int:user_id>` | Usuário existente; titular/admin depois | 200 | 200 com mudanças aprovadas | Status e política titular/outro usuário | HTTP 011 + suíte atual |
| `POST /users` | Nome/email/senha sintéticos válidos | 201 | 201 com mudanças aprovadas | ID retornado; senha omitida; gravação usada pelos cenários seguintes | HTTP 011 + suíte atual |
| `PUT /users/<int:user_id>` | Usuário criado no cenário; admin depois | 200 | 200 com mudanças aprovadas | Status; política de papel/ativação em testes separados | HTTP 011 + suíte atual |
| `DELETE /users/<int:user_id>` | Usuário sintético descartável; admin depois | 200 | 200 com mudanças aprovadas | Remoção conferida no banco da suíte | HTTP 011 + suíte atual |
| `GET /users/<int:user_id>/tasks` | Usuário e tarefa da fixture; titular/admin depois | 200 | 200 com mudanças aprovadas | Status; escopo de tarefas na suíte | HTTP 011 + suíte atual |
| `POST /login` | Email/senha sintéticos válidos | 200 | 200 com mudanças aprovadas | Token e ausência de password; migração legada na suíte | HTTP 011 + suíte atual |
| `GET /tasks` | Tarefas sintéticas; identidade depois | 200 | 200 com mudanças aprovadas | Listagem e escopo de titularidade | HTTP 011 + suíte atual |
| `GET /tasks/<int:task_id>` | Tarefa existente; titular/admin depois | 200 | 200 com mudanças aprovadas | Detalhe; cenário extra 404 após excluir | HTTP 011 + suíte atual |
| `POST /tasks` | Título, usuário/categoria sintéticos; permissão depois | 201 | 201 com mudanças aprovadas | ID criado; tarefa consultada e alterada na sequência | HTTP 011 + suíte atual |
| `PUT /tasks/<int:task_id>` | Tarefa criada no cenário; permissão depois | 200 | 200 com mudanças aprovadas | Título atualizado conferido no banco da suíte | HTTP 011 + suíte atual |
| `DELETE /tasks/<int:task_id>` | Tarefa descartável; permissão depois | 200 | 200 com mudanças aprovadas | Ausência conferida em consulta e GET extra 404 | HTTP 011 + suíte atual |
| `GET /tasks/search` | Busca textual sobre fixture; identidade depois | 200 | 200 com mudanças aprovadas | Status; entradas inválidas e escopo em testes separados | HTTP 011 + suíte atual |
| `GET /tasks/stats` | Fixture conhecida; identidade depois | 200 | 200 com mudanças aprovadas | Status; total restrito ao usuário no teste de escopo | HTTP 011 + suíte atual |
| `GET /reports/summary` | Admin/manager depois | 200 | 200 com mudanças aprovadas | Status; permissão manager e bloqueio de usuário comum | HTTP 011 + suíte atual |
| `GET /reports/user/<int:user_id>` | Usuário existente; titular/manager/admin depois | 200 | 200 com mudanças aprovadas | Status; rota sem usuário retorna 404 | HTTP 011 + suíte atual |
| `GET /categories` | Categorias sintéticas; identidade depois | 200 | 200 com mudanças aprovadas | Status; contagens restritas e consulta em conjunto | HTTP 011 + suíte atual |
| `POST /categories` | Nome de categoria; admin depois | 201 | 201 com mudanças aprovadas | ID retornado usado em tarefa e alteração | HTTP 011 + suíte atual |
| `PUT /categories/<int:cat_id>` | Categoria criada; admin depois | 200 | 200 com mudanças aprovadas | Status; descrição nullable e corpo inválido em testes separados | HTTP 011 + suíte atual |
| `DELETE /categories/<int:cat_id>` | Categoria descartável sem tarefa; admin depois | 200 | 200 com mudanças aprovadas | Status; exclusão após tarefa, na sequência registrada | HTTP 011 + suíte atual |

Casos negativos atuais incluem ausência/adulteração/revogação de token, titularidade e papéis, corpo JSON que não seja objeto, tipos de prioridade e campos, filtros inválidos e limites numéricos. Verificações de banco em arquivo são recusadas pelo executor; a contenção é criada antes de importar a aplicação. O novo fechamento F-08 está no complemento da issue 012.

### Pendências e aprovação

A aprovação da Fase 3 foi recebida em 30/10/2026 conforme os registros existentes; a revisão atual foi autorizada posteriormente, após o diagnóstico da validação. O destino aprovado permanece `reports/audit-project-3.md`. Não se solicita uma nova aprovação fictícia para uma fase já executada.

O incidente e a recuperação não exata permanecem limites relevantes. Sem SMTP real, migração geral de dados/senhas, produção ou comprovação universal de segurança. A publicação e o envio ao curso dependem de solicitação expressa. O reforço da skill teve validação estrutural e por leitura de cenário, sem prova de obediência universal do agente.

## Interrupção e incidente de validação

Após aprovação, o teste de segurança foi executado incorretamente contra o banco local original: a aplicação ignorou a URI temporária e o teste apagou as tabelas antes de criar dados sintéticos. O banco anterior foi perdido; estado posterior preservado em `/private/tmp/task-manager-011-after-incident.db`. Nenhuma refatoração foi realizada. Não há evidência de backup anterior nos locais consultados. Linha de base isolada respondeu 22 métodos/caminhos, sem validação completa dos efeitos. Fase 3 interrompida; nenhum achado foi verificado como corrigido.

## Fase 3 · resultado e validação · 03/11/2026

Após aprovação de o responsável, a API foi refatorada com blueprints como adaptação HTTP, serviços para tarefas, usuários, categorias, relatórios e tokens, models e middleware de autorização. Configuração exige `TASK_SECRET_KEY`; banco é configurável por `TASK_DATABASE_URI`. Import não cria tabelas; `init-db` e o boot explícito inicializam a estrutura. Primeiro admin é criado por comando explícito.

As respostas não incluem verificador de senha; hashes MD5 são atualizados após login válido. A credencial assinada expira em uma hora e é vinculada ao verificador atual via HMAC, sem expô-lo, para impedir uso após troca de senha ou substituição de conta com o mesmo ID. Apenas usuários autorizados acessam recursos; HEAD segue a política GET. As contagens de categorias para usuário comum são restritas às suas tarefas. Credenciais SMTP fixas foram removidas; SMTP real não foi exercitado.

Resultado dos achados: F-01 e F-02 resolvidos nos cenários testados; contas legadas sem novo login seguem com MD5 e não foram migradas. F-03 melhorado com separação de operações e consultas em serviços; serialização permanece em models e adaptadores HTTP, solução MVC adaptada ao Flask. F-04 resolvido no código examinado; SMTP real não validado. F-05 resolvido para listagens e relatório identificados, com teste de contagem de consultas; latência não medida. F-06 centralizado no model. F-07 substituído nos usos próprios encontrados; dados e formatos de data existentes preservados na estratégia UTC naive. F-08 parcialmente tratado nas entradas e casos testados, sem afirmar validação exaustiva de todos os tipos. F-09 constantes existentes reutilizadas. F-10 imports identificados removidos.

**Evidência:** 32 testes passaram em cópia temporária protegida por `sandbox-exec`, com banco SQLite em memória e caso negativo que recusou banco sentinela em arquivo. HTTP real: 24 requisições antes e depois, incluindo os 22 métodos/caminhos originais e duas verificações extras de persistência/exclusão; mesmas sequências de status, sem afirmar igualdade integral de respostas. Boot real `python app.py` respondeu ao health e processo foi encerrado. HTTP usou banco sintético em cópia isolada; rede externa bloqueada. [Resumo](evidence/project-3-validation.json), [antes](evidence/project-3-http-before.json), [depois](evidence/project-3-http-after.json), [testes](evidence/project-3-tests.log), [boot](evidence/project-3-process-smoke.json).

Após o incidente já relatado, os exemplos foram recriados mediante autorização; não são restauração exata dos dados perdidos. O hash do banco local foi igual antes e depois da Fase 3. A validação não executou seed, migração de senhas ou SMTP no banco local; não comprova comportamento de outras stacks ou ausência de falhas. Revisão independente por leitura apontou problemas de acesso e isolamento de teste, corrigidos e cobertos por regressões; não é uma garantia de segurança.

### Checklist oficial na conclusão da issue 011

- [x] Fase 1: linguagem, framework, domínio e contagem de arquivos identificados.
- [x] Fase 2: achados ordenados com evidências, pelo menos cinco achados e depreciações; pausa e aprovação.
- [x] Fase 3: responsabilidades MVC adaptadas, configuração e tratamento central de erros, models e rotas, boot e endpoints verificados no ambiente isolado.
- [ ] F-08: cobertura exaustiva de todas as entradas não demonstrada; validação específica permanece parcial.


## Complemento da revisão de qualidade · issue 012 · 03/11/2026

### Correção do diagnóstico de login

A revisão anterior extraiu a função login e a chamou com request sintético, contornando o middleware. O trecho realmente lança AttributeError se receber lista, mas isso não demonstrava uma falha HTTP da API: `require_identity` já rejeita JSON não objeto em POST/PUT antes do handler. O teste `test_invalid_json_body_and_password_types_are_client_errors` já cobria o caso e passou na suíte de 32 testes executada nesta revisão. Não foi necessário alterar o login.

O novo `test_write_body_containers_are_rejected_including_public_login` conferiu listas, string, número, booleano e null em sete operações POST/PUT, com 400 e sem alterações nas quantidades de usuários/tarefas. O resultado é integrado via Flask test client; não foi inferido apenas de um trecho isolado.

### F-08: lacuna demonstrada e correção

A revisão de F-08 encontrou inteiros acima do intervalo aceito pelo banco, distintos do diagnóstico incorreto do login. As três regressões novas falharam antes da correção, somando 24 falhas de asserção 500 != 400: referências user_id/category_id em criação/edição de tarefas, filtros priority/user_id e IDs nas rotas de recursos.

A correção aplica `MAX_DATABASE_INTEGER = 9223372036854775807` antes das consultas, mantém autenticação antes da validação de IDs de rota e limita conversão dos filtros decimais. Valores com zeros à esquerda continuam aceitos. O maior inteiro suportado continua chegando às consultas (404 para recurso ausente, 200 com coleção vazia para filtro sem resultados); não foi convertido em erro de tipo.

Testes acrescentados:

- `test_task_references_outside_database_integer_range_return_400_without_writes`.
- `test_search_filters_outside_database_integer_range_return_400`.
- `test_resource_ids_outside_database_integer_range_return_400`.
- `test_database_integer_upper_bound_and_leading_zeros_remain_supported`.
- `test_invalid_priority_types_and_bounds_do_not_modify_tasks`.
- `test_write_body_containers_are_rejected_including_public_login`.

**Estado atual de F-08:** resolvido no escopo dos mecanismos identificados de corpo/tipos/filtros e das fronteiras numéricas exercitadas, incluindo rejeição e ausência de efeitos nos casos testados. Isso substitui a classificação parcial para esse escopo; não equivale a cobertura exaustiva de todas as entradas possíveis, todos os limites de tamanho ou todos os mecanismos de validação da API.

### Comandos e resultados atuais

Comando executado a partir da raiz: `task-manager-api/tests/run_sandbox_macos.sh`, com saída redirecionada para logs separados. A primeira tentativa sob o sandbox do agente falhou em `sandbox_apply: Operation not permitted` antes de importar a API. A execução recebeu permissão técnica para criar o sandbox-exec externo; a barreira continuou bloqueando o workspace original, diretório pessoal e rede, com escrita limitada à cópia temporária.

| Etapa | Resultado | Evidência |
| --- | --- | --- |
| Baseline atual antes de alterações | 32 testes, OK; login em lista já recusado | [Log baseline](evidence/project-3-quality-baseline.log) |
| Regressões antes da correção | 35 testes; 24 falhas de asserção em subtestes, todas 500 != 400 | [Log RED](evidence/project-3-quality-red.log) |
| Suíte após correção e ampliação de fronteiras | 38 testes, OK | [Log GREEN](evidence/project-3-quality-green.log) |

[Resumo, hashes e limites desta revisão](evidence/project-3-quality-validation.json). O hash do banco local antes/depois continuou `c5e5246deddcff8a33646a2311bb344ecdecdc627e488fdc5ffca1a39fc93b1f`; nenhum seed ou migração local foi executado. A suíte integrou os 22 métodos/caminhos pelo test client e encerrou suas cópias/bancos. As evidências históricas de 24 requisições HTTP e boot real da issue 011 foram preservadas; não são novas execuções HTTP após este ajuste.

### Checklist após a revisão da issue 012

- [x] Campos dos achados, origens das interfaces, depreciações e matriz de validação organizados conforme o template.
- [x] Expansão retrospectiva explicitada, sem inventar aprovação ou resultados históricos.
- [x] Diagnóstico incorreto de falha HTTP do login corrigido; fluxo integrado confirmado.
- [x] Lacuna numérica do F-08 reproduzida e corrigida com regressões RED→GREEN e suíte completa.
- [x] Corpo, prioridade, filtros, referências e fronteiras válidas conferidos nos casos descritos.
- [x] Banco local preservado e execução contida antes de qualquer import da API.
- [ ] Publicação e envio ao curso: continuam pendentes de solicitação expressa.
