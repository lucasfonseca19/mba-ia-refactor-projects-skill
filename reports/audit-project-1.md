# Auditoria do Projeto 1 · issue 009

## Identificação e escopo

- Data: 29/10/2026. Base: `478f362d9de8969ec41905b9dd9c5077a478daf0`.
- Raiz: `code-smells-project/`. Python 3.13.7 (runtime conferido), Flask 3.1.1/flask-cors 5.0.1 declarados e metadados instalados; Werkzeug 3.1.9 instalado. SQLite, versão vinculada ainda não consultada na auditoria.
- Domínio: API de e-commerce. Quatro tabelas: produtos,usuarios,pedidos,itens_pedido.
- Cobertura:4/4 arquivos Python próprios, 780 linhas físicas; manifestos/README/configuração lidos separadamente. Excluídos ambientes, dependências, banco, artefatos e aplicações vizinhas.
- Arquitetura: app → Controllers → Models → banco, com SQL direto em app/health; conexão global e inicialização/seed implícitos. Separação parcial real.
- Alterações documentais anteriores e skill não rastreada preservadas; fontes Python e requirements sem diferenças na retomada.
- Skill explicitamente invocada nesta sessão.

## Resumo

| Severidade | Quantidade |
| --- | --- |
| CRITICAL |4|
| HIGH |3|
| MEDIUM |4|
| LOW |2|
| Total |13|

## Achados originais

As linhas abaixo são da base auditada, anteriores à refatoração. Método: inspeção estática, sem boot, abertura do banco, exploração, concorrência ou medição de latência nas Fases 1/2. As verificações são propostas nesse ponto do relatório.

### F-001 · CRITICAL · Injeção em consultas

- **Padrão:** AP-01.
- **Localização:** `controllers.py:167–176; models.py:105–111,43–61,122–129,285–299`.
- **Evidência:** Entradas externas de login/cadastro/busca são concatenadas em SQL executado. IDs convertidos pela rota não constituem prova equivalente de injeção.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Pode alterar condições de autenticação e consultas.
- **Correção proposta:** T-01: binding de todos os valores externos.
- **Mudança observável:** Preservar consultas legítimas; SQL recebido como valor é literal.
- **Verificação proposta:** Login válido/inválido, payload SQL, cadastro com apóstrofo e busca sem ampliação.
- **Correspondência manual:** P1-01.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-002 · CRITICAL · Senhas em texto puro e respostas

- **Padrão:** AP-02/AP-03.
- **Localização:** `models.py:72–103,122–129; controllers.py:128–144`.
- **Evidência:** Senha é gravada sem transformação e incluída no JSON de usuários.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Exposição direta de credenciais; agrupada para não duplicar o mesmo impacto.
- **Correção proposta:** T-02/T-03: projeção pública e scrypt, migração explícita em cópia.
- **Mudança observável:** Retirar senha/hash; login verifica hash; dados legados exigem migração.
- **Verificação proposta:** Senha correta/incorreta, salts diferentes, ausência de credenciais e migração idempotente.
- **Correspondência manual:** P1-02.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-003 · CRITICAL · Operações privilegiadas sem controle de acesso

- **Padrão:** AP-04.
- **Localização:** `app.py:47–78; controllers.py:167–186`.
- **Evidência:** Reset apaga quatro tabelas; query executa SQL externo; login não estabelece identidade usada pelas rotas.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Acesso privilegiado sem comprovação de identidade/permissão; proteção externa não verificada.
- **Correção proposta:** T-04: sessão, titular/admin, CSRF e ferramentas administrativas desabilitadas por padrão.
- **Mudança observável:** 401 sem identidade, 403 sem permissão; manter acesso autorizado e os 19 endpoints.
- **Verificação proposta:** Matriz de permissões, titular/outro usuário, admin autorizado e ausência de escrita nos bloqueios.
- **Correspondência manual:** P1-03.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-010 · CRITICAL · Chave e configuração expostas no health check

- **Padrão:** AP-02/configuração.
- **Localização:** `controllers.py:276–290; app.py:7–8,88`.
- **Evidência:** Resposta inclui secret_key, db_path e debug; o literal da chave coincide com a configuração. Valor omitido neste relatório.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Exposição de chave configurada. Não foi demonstrada falsificação de sessão; a versão original não a usa como autenticação.
- **Correção proposta:** Retirar campos sensíveis, configurar chave externamente, debug desligado por padrão.
- **Mudança observável:** Health público sem configuração privada.
- **Verificação proposta:** Resposta sem campos privados e configuração obrigatória validada.
- **Correspondência manual:** adicional.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-004 · HIGH · Persistência nas rotas e no Controller

- **Padrão:** AP-05.
- **Localização:** `app.py:47–78; controllers.py:264–290`.
- **Evidência:** Handlers HTTP executam SQL, commit e serialização fora dos Models.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Acoplamento dificulta substituir persistência e testar. Existe separação parcial, sem classificar tamanho como God Class.
- **Correção proposta:** T-05: Models coesos, Controllers coordenando, rotas e projeções separadas.
- **Mudança observável:** Movimentação interna preserva contratos salvo correções aprovadas.
- **Verificação proposta:** Cenários integrados e revisão de dependências sem SQL nos Controllers.
- **Correspondência manual:** P1-04.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-005 · HIGH · Conexão global mutável

- **Padrão:** AP-06.
- **Localização:** `database.py:4–11,86`.
- **Evidência:** get_db retorna conexão global com check_same_thread=False; não há fechamento por requisição.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Estado transacional compartilhado e isolamento difícil; corrida/corrupção não reproduzidas.
- **Correção proposta:** T-06: conexão por requisição, fechamento no teardown.
- **Mudança observável:** Configurar caminho e inicializar banco explicitamente.
- **Verificação proposta:** Conexões distintas, fechamento em sucesso/erro e persistência por conexão independente.
- **Correspondência manual:** P1-05.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-011 · HIGH · Transação pendente após erro intermediário

- **Padrão:** AP-07.
- **Localização:** `models.py:148–168; controllers.py:218–220`.
- **Evidência:** Escritas de pedido/itens/estoque precedem commit final; captura de erro não reverte conexão compartilhada.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Outro commit pode confirmar alterações pendentes. Há commit final único, não commits entre cada etapa.
- **Correção proposta:** T-07: transação com rollback integral e baixa condicionada de estoque.
- **Mudança observável:** Erro não persiste pedido parcial.
- **Verificação proposta:** Trigger de falha, consulta independente e commit posterior sem ressuscitar pedido.
- **Correspondência manual:** adicional.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-006 · MEDIUM · Consultas por elemento

- **Padrão:** AP-08.
- **Localização:** `models.py:171–200,203–232`.
- **Evidência:** Uma consulta inicial, uma por pedido e uma por item: 1+P+I; exemplo 10 pedidos/50 itens =61.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Acessos crescem com resultados; sem medição de latência.
- **Correção proposta:** T-08: carregar pedidos e itens/produtos em conjunto.
- **Mudança observável:** Preservar campos, pedidos vazios e Desconhecido para produto removido.
- **Verificação proposta:** Contagem SQL com cardinalidades diferentes e equivalência de conteúdo.
- **Correspondência manual:** P1-06.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-007 · MEDIUM · Validação duplicada/divergente de produtos

- **Padrão:** AP-09.
- **Localização:** `controllers.py:28–54,72–90`.
- **Evidência:** Atualização omite tamanho do nome e categorias validadas na criação.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Atualização aceita dados recusados na criação.
- **Correção proposta:** T-09: regra de validade compartilhada.
- **Mudança observável:** PUT inválido passa a retornar 400; campos obrigatórios continuam exigidos.
- **Verificação proposta:** Nomes 1/2/200/201, categorias, negativos e tipos inválidos em POST/PUT.
- **Correspondência manual:** P1-07.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-012 · MEDIUM · Quantidade e demanda agregada sem validação

- **Padrão:** AP-09.
- **Localização:** `controllers.py:195–203; models.py:139–165`.
- **Evidência:** Não exige inteiro positivo; valida estoque por linha sem somar produtos repetidos.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Quantidade negativa pode aumentar estoque; duplicatas podem excedê-lo.
- **Correção proposta:** Validar estrutura/tipos/positividade, somar demanda e baixar na transação.
- **Mudança observável:** Entrada inválida retorna 400 sem escrita.
- **Verificação proposta:** Zero/negativo/fração/bool, linhas repetidas 6+6 com estoque10 e concorrência.
- **Correspondência manual:** adicional.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-013 · MEDIUM · Erros internos expostos e falso sucesso

- **Padrão:** AP-10.
- **Localização:** `controllers.py:118–126,237–255; models.py:275–283`.
- **Evidência:** str(e) chega ao cliente; update retorna True mesmo sem linha afetada.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Filtro inválido vira erro interno e pedido inexistente pode receber sucesso.
- **Correção proposta:** T-10: tradução central, validação e conferência da atualização.
- **Mudança observável:** 400 para entrada inválida,404 ausente,500 genérico.
- **Verificação proposta:** JSON/filtro inválidos, status de recurso ausente e falha de banco sem detalhes.
- **Correspondência manual:** adicional.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-008 · LOW · Política de desconto sem nomes

- **Padrão:** AP-12.
- **Localização:** `models.py:256–262`.
- **Evidência:** Limites 10000/5000/1000 e taxas0.1/0.05/0.02 aparecem diretamente.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Dificulta leitura; valores não foram considerados incorretos.
- **Correção proposta:** T-12: constantes de domínio nomeadas.
- **Mudança observável:** Preservar operadores >, taxas e arredondamento.
- **Verificação proposta:** Abaixo/no/acima de cada faixa.
- **Correspondência manual:** P1-08.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

### F-009 · LOW · Nomes locais pouco informativos

- **Padrão:** nomenclatura adicional.
- **Localização:** `models.py:187–196,219–228`.
- **Evidência:** cursor2,cursor3,prod descrevem ordem/abreviação, não finalidade.
- **Método e limite:** inspeção estática; cenário não reproduzido na auditoria.
- **Impacto/severidade:** Clareza localizada; sem falha funcional atribuída.
- **Correção proposta:** Nomear por domínio ou eliminar ao corrigir N+1.
- **Mudança observável:** Nenhuma mudança pública.
- **Verificação proposta:** Revisão de nomes e equivalência das listagens.
- **Correspondência manual:** P1-09.
- **Dependências:** aprovação das alterações públicas e validação isolada; nenhuma migração real autorizada por inferência.

## Comparação com análise manual

F-001 a F-009 correspondem respectivamente a P1-01 a P1-09 no README, com as mesmas severidades:9/9, incluindo 3 CRITICAL e 2 HIGH. Os achados F-010 a F-013 são adicionais. A comparação não foi cega, pois o README estava disponível. A seleção manual não pretendia ser exaustiva.

Diferença de proposta: o README sugeria retirar SQL administrativo; decisões posteriores exigem preservar endpoints legítimos. Proposta aprovada: preservar `/admin/query`, exigir administrador e habilitação explícita, desabilitada por padrão. Quando habilitada, continua oferecendo SQL arbitrário a um administrador confiável e pode contornar invariantes da aplicação. Não equivale a endpoint público seguro para SQL irrestrito.

## APIs deprecated e documentação

Nenhum uso deprecated confirmado. Python/sqlite3: não encontrados usos dos conversores deprecated habilitados, sqlite3.version ou argumentos opcionais posicionais incompatíveis. TIMESTAMP no esquema sozinho não ativa conversores. Flask/flask-cors: nenhum candidato observado; consulta de changelog online falhou, cobertura documental não exaustiva. Werkzeug não era chamado diretamente.

Fontes consultadas em 29/10/2026:
- https://docs.python.org/3.13/library/sqlite3.html (binding,transações,depreciações; página da série3.13, patch documental posterior ao runtime).
- https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security (scrypt e verificação).

Ausência de candidato não prova ausência universal de APIs deprecated. Debug e SQL concatenado são problemas, mas não depreciações.

## Proposta de refatoração aprovada

Antes: app.py,controllers.py,models.py,database.py.
Depois: app factory/config/database/security/errors; routes/,controllers/,models/,views/ e tests/. Models por domínio, transação de pedido, conexão por requisição; sem ORM ou camadas de repasse desnecessárias.

Ordem: snapshot/baseline; infraestrutura/configuração; MVC; SQL/senhas/acesso; integridade/validação/erros; N+1/clareza; verificação/revisão/registros/commit.

Contratos: catálogo/cadastro/login públicos; escrita de produtos, listagens gerais, relatórios, status e administração só para admin. Titular/admin acessa usuário e pedidos individuais; cliente cria pedido só para si. Sessão assinada por cookie, token CSRF para escrita autenticada. Login mantém dados e acrescenta token CSRF. Senha/hash removidos das respostas. Ferramentas administrativas desabilitadas por padrão. Chave externa nova; debug desligado. Dados iniciais explícitos sem credenciais fixas. Migração explícita/idempotente de texto puro para hash testada só em cópia. Erros400/404/500 conforme a proposta.

Configuração prevista: DATABASE_PATH,SECRET_KEY,DEBUG,ADMIN_TOOLS_ENABLED. No boot sem config obrigatória, falhar claramente. Nenhum banco existente migrado ou resetado implicitamente. Preservar funcionalidades legítimas, métodos/caminhos e política monetária.

## Plano de validação antes/depois

Usar .venv existente sem instalação. Snapshot somente dos quatro módulos e requirements em diretório temporário; não copiar loja.db. Preparar fixtures sintéticas em banco descartável. Original inicia com `.venv/bin/python -B -m flask --app app run --host 127.0.0.1 --port 5001 --no-debugger --no-reload` a partir da cópia (caminho absoluto do interpretador). Depois, app factory configurada com banco temporário; teste HTTP real por subprocesso e teste integrado com unittest/Flask test client. Conferir porta ou usar porta efêmera, sem reloader. Prontidão: GET / e health respondem. Encerrar processos em finally. As notificações originais são print, sem integração externa real encontrada.

### Inventário e cenários (planejados na auditoria)

| Método/caminho | Entrada/pré-condição | Original a observar | Esperado depois / persistência |
| --- | --- | --- | --- |
|GET /|público|200 índice|preservar|
|GET /health|banco disponível|200 com configuração|200 sem segredos, banco acessível|
|GET /produtos|2 produtos|200 coleção|dados preservados|
|GET /produtos/busca|q/categoria/faixa|200 filtrado|resultado legítimo igual, SQL como valor|
|GET /produtos/<id>|produto existente|200|preservar; ausente404|
|POST /produtos|corpo válido|201 público|admin201 e registro|
|PUT /produtos/<id>|produto/corpo completo|200 público|admin200 e atualização; inválido400|
|DELETE /produtos/<id>|descartável|200 público|admin200 e exclusão|
|GET /usuarios|3 usuários|200 com senha|admin200 sem senha/hash|
|GET /usuarios/<id>|titular existente|200 com senha|titular/admin200 sem senha/hash|
|POST /usuarios|nome/email/senha|201|201, hash, papel cliente|
|POST /login|credenciais sintéticas|200/401|200 sessão+CSRF ou401|
|POST /pedidos|usuário/item/estoque|201|titular/admin201,total/itens/estoque|
|GET /pedidos|pedido criado|200|admin200, conteúdo|
|GET /pedidos/usuario/<id>|usuário com/sem pedido|200|titular/admin200, escopo|
|PUT /pedidos/<id>/status|status válido|200 inclusive ausente|admin200 persistido; ausente404|
|GET /relatorios/vendas|pedidos conhecidos|200|admin200, cálculos iguais|
|POST /admin/query|SQL controlado|200 público|admin+habilitação200, leitura/escrita|
|POST /admin/reset-db|último cenário descartável|200 exclusão|admin+habilitação200,4 tabelas vazias|

Casos negativos:401/403 com efeito inexistente; CSRF ausente/incorreto; injeção/apóstrofos; hash/migração; nomes1/2/200/201,categoria,tipos; quantidades0/negativa/fração/bool e duplicadas; falha SQL intermediária e commit posterior; dois pedidos concorrentes; contagem de SQL; vazio/produto removido; faixas de desconto; JSON/filtro inválido; erro interno genérico. Conferir persistência em conexão independente. Separar falhas originais, correções e regressões.

## Aprovação e limites

Auditoria entregue na conversa sem escrita e seguida de aprovação humana em turno posterior. Aprovação cobre F-001 a F-013, contratos acima, preparação/validação, este relatório, registros e commit da issue 009. Não inclui push,deploy,projetos 2/3 ou migração de banco real. Relatório salvo somente após a aprovação.

## Complemento após a Fase 3

### Execução e decisões

Aprovação de o responsável recebida em turno posterior à auditoria, antes de qualquer escrita. Implementação em `refactor/issue-009-project-1`, sem instalação, push ou alteração nas outras APIs. A estrutura nova está em `code-smells-project/README.md`: 19 módulos Python de produção (incluindo __init__), dois arquivos de teste e um utilitário HTTP. Os módulos únicos controllers.py e models.py foram substituídos por pacotes por domínio.

- App factory sem abertura/seed no import; configuração e erros centrais; conexão por contexto com fechamento garantido.
- Consultas de negócio parametrizadas, senhas scrypt, projeções explícitas e health sem segredos. SQL administrativo é uma exceção deliberada: operação privilegiada opt-in.
- Sessão assinada/CSRF, autorização por papel atual e titular; cadastro ignora role externa. Origin estrangeira é recusada, CORS exige origens explícitas. Cookies HttpOnly/SameSite Lax e Secure por padrão; testes HTTP locais desativam somente Secure.
- Pedido com BEGIN IMMEDIATE, demanda por produto agregada e baixa condicionada; falha reverte pedido/itens/estoque. Linhas repetidas legítimas continuam representadas separadamente.
- Model de listagem usa duas consultas, inclusive coleção vazia. Com autenticação, o endpoint faz adicionalmente uma consulta de identidade; não alegamos duas consultas totais no HTTP.
- Políticas de desconto, representação REAL, estados e ausência de reposição automática ao cancelar preservadas. Migração explícita é transacional/idempotente; nenhum banco real foi migrado.
- Emails duplicados preservados: login examina as credenciais das contas em ordem por ID, como o fluxo anterior; não impusemos unicidade. Valores monetários/resultados devem ser finitos; preços aceitos são vinculados como REAL, inclusive inteiros JSON maiores que o binding inteiro de SQLite.

### Comandos, resultados e evidências

- Snapshot original SHA-256: [resumo JSON](evidence/project-1-validation.json). Cópia temporária em `/private/tmp/refactor-009-273cjnx7/before`; não integra o entregável.
- Baseline: `PROJECT_SOURCE=/private/tmp/refactor-009-273cjnx7/before .venv/bin/python -B -m unittest discover -s tests -v`, na versão inicial dos testes: 23 métodos, 49 falhas de assertions/subtestes e 1 erro de banco bloqueado. A matriz principal dos 19 endpoints passou. Erro de lock era da transação original pendente ao remover trigger por outra conexão, não evidência de regressão nova.
- Teste de rollback refinado no original: 1 teste falhou, comprovando que cadastro posterior confirmava pedido parcial. No refatorado, o mesmo cenário passou e deixou zero pedidos/itens.
- `.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s tests -v`: 41 testes aprovados, zero falhas/erros/ResourceWarnings.
- `.venv/bin/python -B tools/validate_http.py --source /private/tmp/refactor-009-273cjnx7/before --legacy --output /private/tmp/refactor-009-273cjnx7/http-before.json`: boot e 19/19 operações, com respostas/efeitos conferidos. [Evidência original](evidence/project-1-http-before.json).
- `.venv/bin/python -B tools/validate_http.py --output /private/tmp/refactor-009-273cjnx7/http-after.json`: boot e 19/19 operações após correção, com identidade/CSRF válidos e persistência independente. [Evidência refatorada](evidence/project-1-http-after.json).
- HTTP executado em loopback/porta efêmera com permissão técnica do sandbox. Subprocessos terminados e coletados em finally; bancos removidos. Não acionados serviços externos.
- SQL trace: exatamente2 SELECTs do Model para0/1/10 pedidos, 0/5/50 itens, com/sem filtro de usuário. Original:1+P+I; exemplo10/50=61. Não houve benchmark de latência.
- SQLite vinculado ao runtime:3.53.4. Sem dependências instaladas ou lockfile alterado.
- Revisão independente encontrou três problemas introduzidos/de fronteira (emails duplicados, resultado infinito e binding de inteiro grande); cada um ganhou teste visto falhar antes da correção. Revisão também levou ao fechamento explícito das conexões dos testes. O revisor não conseguiu abrir servidor por restrição do seu sandbox; os testes HTTP foram executados pelo agente principal.
- Context7 indisponível por credencial da integração; fontes oficiais de Flask 3.1 consultadas pela web: [conexão e ciclo de vida](https://flask.palletsprojects.com/en/stable/tutorial/database/), [sessão/cookies/CSRF](https://flask.palletsprojects.com/en/stable/web-security/). Consulta em 29/10/2026. Não copiado o esquema destrutivo do tutorial.

### Matriz executada

Todos os 19 cenários principais da tabela original foram executados antes/depois por HTTP real e no teste integrado, com os status planejados. IDs gerados variaram por AUTOINCREMENT; as verificações usam o ID retornado e não exigem o mesmo contador. As mudanças de contrato foram conferidas separadamente na suíte:

| Cenário | Resultado depois |
| --- | --- |
| Sem identidade / cliente em operação administrativa ou de outro titular |401/403, sem escrita; titular e admin autorizados funcionam|
| CSRF ausente, incorreto, de outra sessão, não ASCII; cookie adulterado |403 ou401 conforme identidade, sem exclusão|
| Papel alterado ou usuário excluído depois do login |Privilégio reavaliado no banco,403/401|
| Login injetado, senha inválida, apóstrofo legítimo, busca com SQL literal |Login indevido401; nome legítimo201; busca não amplia resultados|
| Hashes e serialização |Hashes verificáveis/salts distintos; senha/hash ausentes nas projeções|
| Migração declarada, repetição e registro inválido |Converte corretamente; repetição0; registro inválido reverte tudo|
| POST/PUT: nome1/2/200/201, categoria, preços/estoques e campos obrigatórios |Mesma regra; inválidos400, válidos persistidos|
| Quantidades inválidas/linhas repetidas/estoque insuficiente |400 sem escrita; duplicatas válidas preservam linhas,total e estoque|
| Falha após primeira escrita + commit posterior |500 seguro, rollback integral, nenhum pedido ressuscitado|
| Dois pedidos concorrentes de6 com estoque10 |Um201,um400; estoque4 e um pedido|
| Pedidos vazios/produto removido |Coleção vazia preservada; nome Desconhecido mantido|
| Limites monetários e desconto |Faixas estritas preservadas; resultado infinito recusado sem escrita; armazenamento inválido não gera Infinity/NaN|
| JSON/filtro inválido, status ausente, erro interno |400/404/500 conforme contrato, sem detalhes internos|
| Ferramentas administrativas |Negadas quando desabilitadas; leitura/escrita/reset funcionam para admin habilitado|
| Configuração/CLI/ciclo de conexão |Config obrigatória; init sem seed; admin com hash; conexão fecha em sucesso/erro|

### Estado dos achados

| Achado | Estado no escopo validado | Evidência principal |
| --- | --- | --- |
|F-001|resolvido|Binding em Models, testes SQL/apóstrofo/login|
|F-002|resolvido|Projeções, hash, salts e migração sintética|
|F-003|resolvido quanto à ausência de controle|Permissões/CSRF; SQL privilegiado preservado opt-in|
|F-004|resolvido|Models por domínio, Controllers sem SQL e fluxo integrado|
|F-005|resolvido|Conexão por contexto e testes de fechamento|
|F-010|resolvido|Health sem campos sensíveis, config externa|
|F-011|resolvido|Trigger de falha e commit posterior sem pedido parcial|
|F-006|resolvido|Duas consultas no Model, cardinalidades conferidas|
|F-007|resolvido|Mesmas regras POST/PUT e casos de fronteira|
|F-012|resolvido|Validação, soma de demanda e teste concorrente|
|F-013|resolvido|Tradução central, entrada inválida400 e recurso ausente404|
|F-008|resolvido|Faixas nomeadas e testes abaixo/no/acima|
|F-009|resolvido|Cursores numerados eliminados pela consulta em conjunto|

### Checklist oficial de validação

Fase 1:
- [x] Linguagem detectada corretamente.
- [x] Framework detectado corretamente.
- [x] Domínio descrito corretamente.
- [x] Número de arquivos analisados condizente:4 originais.

Fase 2:
- [x] Relatório conforme template, com escopo/achados/proposta/plano/limites.
- [x] Cada finding com arquivo e linhas originais.
- [x] Ordenação CRITICAL→HIGH→MEDIUM→LOW.
- [x] Mínimo de 5 findings; 9 correspondências manuais.
- [x] Detecção de deprecated incluída:nenhum uso confirmado, limites declarados.
- [x] Pausa e aprovação posterior antes de qualquer escrita.

Fase 3:
- [x] Diretórios e responsabilidades MVC.
- [x] Configuração extraída, sem segredo fixo.
- [x] Models abstraem dados e regras.
- [x] Rotas e representação separadas.
- [x] Controllers coordenam o fluxo.
- [x] Erros centralizados.
- [x] Entry point claro.
- [x] Boot verificado.
- [x] Os19 endpoints originais respondem corretamente nos cenários executados.

### Limites restantes

Resultados delimitados aos cenários descritos; não declaramos zero anti-patterns universalmente. Sem teste de carga, deploy, infraestrutura externa ou migração real. A ferramenta SQL habilitada continua tendo poder administrativo irrestrito e pode contornar invariantes; a política aprovada exige admin confiável, CSRF e opt-in. Migração exige base offline integralmente plaintext; bases mistas não são inferidas automaticamente. Emails duplicados e ausência de reposição automática no cancelamento permanecem contratos legados. Na conclusão desta auditoria, não havia prova de agnosticismo em outra stack ou execução dos projetos 2/3.

Os detalhes de validação e suas limitações estão registrados neste relatório.
