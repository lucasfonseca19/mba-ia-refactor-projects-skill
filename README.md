# Refactor Arch · Entrega 3 do MBA

Skill de análise, auditoria e refatoração para MVC, desenvolvida com Codex e aplicada a três APIs fornecidas pelo curso. As análises manuais precederam a construção; cada auditoria foi apresentada para aprovação antes da refatoração.

[Análise Manual](#análise-manual) · [Construção da Skill](#construção-da-skill) · [Resultados](#resultados) · [Como Executar](#como-executar)

Este README documenta as análises, decisões, evidências e limitações do desafio de refatoração arquitetural do MBA.

**Situação em 03/11/2026:** três APIs refatoradas, com relatórios e evidências de validação.

**Revisão de qualidade concluída:** o relatório do Projeto 3 foi detalhado conforme o template, com reconstrução retrospectiva explicitada. A suíte integrada confirmou que o middleware já retornava 400 para lista JSON no login; o diagnóstico isolado anterior estava incorreto. Foram corrigidas lacunas numéricas reais do F-08, com regressões e 38 testes aprovados em cópia protegida. Evidências e limites estão no relatório e na issue 012.

## Análise Manual

Registro histórico das issues 004, 005 e 006, realizado antes da criação da skill. As propostas e os limites abaixo descrevem aquele momento; o estado após a refatoração está em [Resultados](#resultados). As contagens manuais são diferentes das contagens posteriores das auditorias.

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 · E-commerce Flask | 3 | 2 | 2 | 2 | 9 |
| 2 · LMS Express | 3 | 2 | 2 | 2 | 9 |
| 3 · Task Manager Flask | 2 | 1 | 3 | 2 | 8 |

### Projeto 1: `code-smells-project` (issue 004)

Análise estática realizada em 27/10/2026 nos quatro arquivos Python da aplicação: `app.py`, `controllers.py`, `models.py` e `database.py`. Stack identificada pelos imports e pela configuração: Python, Flask, flask-cors e SQLite. Domínio: loja com produtos, usuários, login, pedidos e relatório de vendas. Há uma divisão inicial por arquivos, mas também acesso direto ao banco nas rotas e no controller e uma conexão global compartilhada.

Foram selecionados nove problemas: três CRITICAL, dois HIGH, dois MEDIUM e dois LOW. As severidades seguem a escala do enunciado e refletem o impacto de cada ocorrência. Esta seleção atende ao mínimo exigido para o projeto 1 e não pretende esgotar a auditoria. Não houve execução HTTP, teste de exploração, medição de desempenho ou refatoração nesta análise. O boot verificado anteriormente na issue 003 não comprova o comportamento de todos os endpoints.

#### P1-01 · CRITICAL · SQL construído com entrada do usuário

- **Evidência:** [controllers.py, linhas 167–176](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/controllers.py#L167-L176) recebe email e senha da requisição e os encaminha a [models.py, linhas 105–111](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L105-L111), que concatena esses valores diretamente no SQL de login.
- **Relevância e severidade:** dados externos podem alterar a condição SQL usada na autenticação, permitindo contornar a comparação esperada de credenciais. Isso corresponde à categoria SQL Injection, classificada como CRITICAL no enunciado. A vulnerabilidade é sustentada pelo fluxo no código; uma exploração HTTP não foi executada.
- **Sinal reutilizável para a futura skill:** rastrear dados externos até consultas montadas por concatenação ou interpolação, verificando se a biblioteca separa parâmetros do comando. Não basta encontrar concatenação: é necessário confirmar a origem e o uso dos valores.
- **Direção de correção proposta:** usar consultas parametrizadas. Esta é uma recomendação, ainda sem implementação.

#### P1-02 · CRITICAL · Senhas em texto puro incluídas nas respostas

- **Evidência:** [models.py, linhas 122–129](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L122-L129) grava a senha recebida sem transformação; [linhas 72–103](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L72-L103) incluem `senha` nos dicionários de usuários. [controllers.py, linhas 128–144](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/controllers.py#L128-L144) envia esses dicionários em JSON, pelas rotas registradas em [app.py, linhas 18–19](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/app.py#L18-L19).
- **Relevância e severidade:** as respostas incluem credenciais legíveis. A exposição direta de dados sensíveis justifica CRITICAL. Armazenamento e serialização foram agrupados porque fazem parte da mesma exposição comprovada no código.
- **Sinal reutilizável para a futura skill:** acompanhar campos sensíveis entre entrada, persistência e saída; verificar se a resposta usa uma lista explícita de campos permitidos. O nome do campo sozinho é uma pista, não a comprovação.
- **Direção de correção proposta:** armazenar hashes adequados para senhas e excluir credenciais das respostas.

#### P1-03 · CRITICAL · Operações administrativas sem controle de acesso

- **Evidência:** [app.py, linhas 47–57](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/app.py#L47-L57) registra uma rota que apaga os dados das quatro tabelas; [linhas 59–78](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/app.py#L59-L78) recebe SQL no corpo da requisição e o executa. A leitura dos quatro arquivos não encontrou autenticação ou autorização aplicadas a essas rotas.
- **Relevância e severidade:** quem alcançar essas rotas da aplicação pode solicitar operações destrutivas e consultas arbitrárias sem comprovar privilégios. O controle direto dos dados justifica CRITICAL. Não foi verificada a existência de proteção externa de infraestrutura nem executado qualquer comando destrutivo.
- **Sinal reutilizável para a futura skill:** identificar operações privilegiadas e conferir proteção efetiva em rotas, decorators, middlewares ou hooks. Um caminho chamado `/admin` não comprova autorização.
- **Direção de correção proposta:** remover a execução arbitrária de SQL da API e restringir operações administrativas por mecanismos explícitos de autenticação e autorização.

#### P1-04 · HIGH · Roteamento e persistência misturados

- **Evidência:** [app.py, linhas 47–78](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/app.py#L47-L78) registra rotas, interpreta entrada HTTP, executa SQL, confirma alterações e monta respostas no mesmo módulo. Em outro ponto, [controllers.py, linhas 264–290](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/controllers.py#L264-L290) também executa consultas diretamente.
- **Relevância e severidade:** o acesso aos dados fica espalhado entre a entrada da aplicação, controllers e models. Isso dificulta substituir a persistência e testar o comportamento sem o banco. HIGH se refere à violação de responsabilidades; o risco de acesso administrativo já está registrado em P1-03, sem ser contado novamente como outro problema de segurança.
- **Sinal reutilizável para a futura skill:** verificar responsabilidades e dependências reais, como handlers HTTP que executam SQL e controlam transações, independentemente dos nomes de arquivos ou do framework.
- **Direção de correção proposta:** manter o registro de rotas na entrada e concentrar o acesso aos dados na camada apropriada da arquitetura MVC alvo.

#### P1-05 · HIGH · Conexão de banco em estado global mutável

- **Evidência:** [database.py, linhas 4–11](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/database.py#L4-L11) mantém `db_connection` global, inicializa uma conexão com `check_same_thread=False` e a devolve em [linha 86](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/database.py#L86). Models e controllers importam `get_db` para acessar essa mesma conexão.
- **Relevância e severidade:** operações e testes compartilham o estado da conexão e de suas transações, sem um ciclo de vida por operação ou requisição explícito. Essa dependência global dificulta isolamento e se enquadra no exemplo HIGH do enunciado. Não foi reproduzida uma falha concorrente; desabilitar a checagem de thread não comprova, por si só, corrupção de dados.
- **Sinal reutilizável para a futura skill:** localizar recursos mutáveis globais, seus consumidores e quem controla seu ciclo de vida; distinguir esses recursos de constantes ou configurações imutáveis.
- **Direção de correção proposta:** gerenciar conexão e transação com ciclo de vida explícito e permitir substituí-las em testes.

#### P1-06 · MEDIUM · Consultas adicionais dentro de loops (N+1)

- **Evidência:** [models.py, linhas 171–200](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L171-L200) faz uma consulta inicial de pedidos, outra por pedido para seus itens e outra por item para o nome do produto. O padrão se repete em [linhas 203–232](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L203-L232).
- **Relevância e severidade:** para P pedidos e I itens no total, o trecho executa `1 + P + I` consultas. Dez pedidos com cinco itens cada exigem 61 consultas nesse percurso. O número de acessos cresce com os resultados, um gargalo de performance classificado como MEDIUM no enunciado. Essa contagem deriva do código; não é uma medição de latência.
- **Sinal reutilizável para a futura skill:** procurar acessos à persistência dentro de loops, incluindo chamadas indiretas a models ou repositórios; confirmar que o acesso depende de cada elemento.
- **Direção de correção proposta:** buscar os dados relacionados em conjunto, usando joins ou consultas em lote conforme a tecnologia.

#### P1-07 · MEDIUM · Validação de produtos duplicada e divergente

- **Evidência:** [controllers.py, linhas 28–54](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/controllers.py#L28-L54) valida campos obrigatórios, preço, estoque, tamanho do nome e categoria na criação. [Linhas 72–90](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/controllers.py#L72-L90) repetem parte dessas verificações na atualização, mas omitem os limites de tamanho do nome e a lista de categorias.
- **Relevância e severidade:** um produto pode receber na atualização valores que seriam rejeitados na criação. A duplicação já produziu uma divergência verificável de regras, justificando MEDIUM. A conclusão vem dos caminhos no código, sem executar uma atualização.
- **Sinal reutilizável para a futura skill:** comparar regras de operações sobre a mesma entidade e procurar trechos repetidos que possam divergir, mesmo quando expressos com bibliotecas diferentes.
- **Direção de correção proposta:** compartilhar as regras de validade do produto e explicitar eventuais diferenças intencionais entre operações.

#### P1-08 · LOW · Limites e percentuais de negócio sem nomes

- **Evidência:** [models.py, linhas 256–262](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L256-L262) usa os limites `10000`, `5000`, `1000` e as taxas `0.1`, `0.05`, `0.02` diretamente no cálculo de desconto do relatório.
- **Relevância e severidade:** o código não nomeia a política que esses valores representam, dificultando sua leitura e revisão. É um problema de legibilidade classificado como LOW; esta análise não afirma que os valores estejam incorretos. Códigos HTTP e outros números convencionais não foram automaticamente tratados como problemas.
- **Sinal reutilizável para a futura skill:** identificar literais de negócio cujo significado não esteja expresso em constantes, configuração ou política nomeada, considerando o contexto.
- **Direção de correção proposta:** nomear os limites e taxas preservando o comportamento atual.

#### P1-09 · LOW · Nomes locais escondem o papel dos dados

- **Evidência:** [models.py, linhas 187–196](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L187-L196) usa `cursor2`, `cursor3` e `prod` para acessar itens do pedido e nomes de produtos. A mesma nomenclatura aparece em [linhas 219–228](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/code-smells-project/models.py#L219-L228).
- **Relevância e severidade:** a numeração dos cursores expressa a ordem de criação, mas não a finalidade; abreviações exigem consultar as instruções ao redor para entender o dado. É uma oportunidade localizada de clareza, portanto LOW, sem afirmar falha funcional.
- **Sinal reutilizável para a futura skill:** avaliar se os nomes distinguem os papéis de dados e recursos no contexto. Abreviações não devem ser condenadas automaticamente nem gerar achados em massa.
- **Direção de correção proposta:** usar nomes que expressem a finalidade, como `cursor_itens`, `cursor_produtos` e `produto`.

### Projeto 2: `ecommerce-api-legacy` (issue 005)

Análise histórica: referências de arquivos/linhas abaixo pertencem à revisão `769ee59bdf72c051197ba85d6ff14cd4b3997d6a`, anterior à refatoração. Consulte a fonte com `git show <revisão>:ecommerce-api-legacy/src/<arquivo>`. Resultado posterior: [auditoria da issue010](reports/audit-project-2.md).

Análise realizada em 27/10/2026 dos três arquivos JavaScript em `src/`, além de `package.json`, README e exemplos de requisições. Apesar do nome da pasta, o domínio observado é um LMS: usuários, cursos, matrículas, pagamentos e relatório financeiro. Stack: Node.js, Express e sqlite3, com banco SQLite em memória e checkout simulado. A classe `AppManager` concentra a aplicação.

Foram selecionados nove problemas: três CRITICAL, dois HIGH, dois MEDIUM e dois LOW. A análise é estática, com uma verificação isolada da função `badCrypto` usando entradas sintéticas. Não houve execução HTTP, contato com gateway, cobrança, alteração de dados ou refatoração. As vulnerabilidades de dependências mencionadas na issue 003 não foram automaticamente convertidas em achados: exigem avaliação própria de aplicabilidade.

#### P2-01 · CRITICAL · Classe concentra banco, rotas e regras de checkout

- **Evidência:** `AppManager.js, linhas 4–25` cria a conexão, define o esquema, insere dados e registra rotas; `linhas 28–78` mistura entrada HTTP, consultas, decisão de pagamento, matrícula, auditoria e resposta. A mesma classe também produz o relatório e exclui usuários.
- **Relevância e severidade:** responsabilidades de infraestrutura, persistência e fluxo de negócio ficam presas na mesma classe, dificultando testes e mudanças isoladas. A combinação corresponde ao exemplo de God Class classificado como CRITICAL no enunciado; o tamanho do arquivo sozinho não determinou a classificação.
- **Sinal reutilizável para a futura skill:** identificar módulos que acumulam roteamento, persistência e regras de domínios diferentes, rastreando dependências e efeitos reais.
- **Direção de correção proposta:** separar composição da aplicação, acesso a dados e coordenação do checkout conforme o MVC alvo.

#### P2-02 · CRITICAL · Dados de cartão e configuração de gateway enviados ao log

- **Evidência:** `AppManager.js, linhas 29–45` recebe `req.body.card` e imprime o valor completo junto de `config.paymentGatewayKey`, definido em `utils.js, linhas 1–7`.
- **Relevância e severidade:** conteúdo sensível enviado pelo cliente é copiado integralmente para uma saída de log. A exposição justifica CRITICAL. O checkout é simulado e não foi verificado se a chave de exemplo é válida ou secreta; a conclusão não depende de atribuir validade a esse literal.
- **Sinal reutilizável para a futura skill:** rastrear dados sensíveis até logs, mensagens de erro e respostas, inclusive por interpolação e funções auxiliares.
- **Direção de correção proposta:** excluir dados de cartão dos logs e aplicar redação de campos sensíveis e configuração externa quando apropriado.

#### P2-03 · CRITICAL · Relatório administrativo e exclusão de usuários sem autorização

- **Evidência:** `AppManager.js, linhas 80–83` registra o relatório financeiro e `linhas 131–136` registra a exclusão de usuários. `app.js, linhas 5–10` instala somente o parser JSON antes das rotas; a leitura dos três módulos não identificou autenticação ou autorização.
- **Relevância e severidade:** a aplicação permite consultar informações administrativas e remover usuários sem comprovar identidade ou permissão. Acesso a dados administrativos e operação destrutiva justificam CRITICAL. Proteções externas de infraestrutura não foram verificadas.
- **Sinal reutilizável para a futura skill:** conferir se operações privilegiadas têm proteção efetiva na cadeia de middlewares ou handlers, sem inferir proteção pelo nome da URL.
- **Direção de correção proposta:** definir os atores autorizados e aplicar autenticação e autorização antes das operações.

#### P2-04 · HIGH · Função de senha descarta quase toda a entrada

- **Evidência:** `utils.js, linhas 17–22` repete os dois primeiros caracteres de uma representação Base64 e retorna apenas dez caracteres. `AppManager.js, linhas 66–71` usa o resultado como senha persistida e adota uma senha padrão quando a entrada está ausente.
- **Relevância e severidade:** senhas diferentes podem produzir exatamente o mesmo valor por construção; não há proteção adequada da senha. Uma execução isolada confirmou a igualdade para duas entradas sintéticas diferentes, sem acessar o banco. HIGH reflete o impacto sobre a credencial armazenada; não foi alegado bypass de login, pois este projeto não implementa uma rota de login.
- **Sinal reutilizável para a futura skill:** inspecionar a transformação realmente aplicada a senhas, em vez de confiar em nomes como `hash` ou `crypto`; verificar truncamento, codificação reversível e valores padrão.
- **Direção de correção proposta:** exigir senha quando aplicável e usar uma função própria para armazenamento de senhas, com parâmetros e salt gerenciados por biblioteca apropriada.

#### P2-05 · HIGH · Checkout grava etapas relacionadas sem transação

- **Evidência:** `AppManager.js, linhas 50–63` insere matrícula, pagamento e auditoria em comandos separados, com saídas antecipadas em caso de erro. Não há início de transação, commit conjunto ou rollback no fluxo lido.
- **Relevância e severidade:** se o pagamento falhar após a matrícula, o retorno de erro não desfaz a matrícula já inserida. A integridade da operação central depende da sequência sem falhas, justificando HIGH. Não houve injeção de falha em execução.
- **Sinal reutilizável para a futura skill:** identificar múltiplas gravações que compõem uma única operação de negócio e conferir sua atomicidade e política de falha, sem presumir que callbacks ou `await` oferecem transação.
- **Direção de correção proposta:** definir a unidade transacional e reverter as gravações relacionadas quando uma etapa obrigatória falhar; decisões sobre auditoria devem ser explícitas.

#### P2-06 · MEDIUM · Consultas repetidas por curso e matrícula

- **Evidência:** `AppManager.js, linhas 83–106` busca cursos, consulta matrículas em `forEach` e faz duas buscas adicionais por matrícula, para usuário e pagamento.
- **Relevância e severidade:** o percurso em que as consultas têm sucesso executa `1 + C + 2E` consultas para C cursos e E matrículas. Esse crescimento com os resultados corresponde ao padrão N+1 e justifica MEDIUM; não foi medida latência.
- **Sinal reutilizável para a futura skill:** reconhecer acessos a dados dentro de iterações e callbacks, inclusive quando o formato do loop difere do observado em Python.
- **Direção de correção proposta:** carregar relações e agregações por joins ou consultas em lote, preservando o contrato do relatório.

#### P2-07 · MEDIUM · Erros de callbacks ignorados

- **Evidência:** `AppManager.js, linhas 92–93` acessa `enrollments.length` sem tratar `err`; `linhas 131–136` responde à exclusão sem verificar seu erro. O callback de auditoria em `linhas 57–60` também retorna sucesso sem conferir o resultado.
- **Relevância e severidade:** falhas podem gerar exceções secundárias ou respostas de sucesso incompatíveis com a operação. MEDIUM corresponde à inconsistência no tratamento de erros; não foi afirmado que houve uma falha de banco em execução.
- **Sinal reutilizável para a futura skill:** procurar erros recebidos e ignorados em callbacks, promessas ou exceções e relacioná-los ao status retornado ao cliente.
- **Direção de correção proposta:** estabelecer uma política consistente de propagação e resposta a erros, distinguindo etapas obrigatórias e opcionais.

#### P2-08 · LOW · Variáveis de checkout pouco expressivas

- **Evidência:** `AppManager.js, linhas 29–35` chama nome, email, senha, curso e cartão de `u`, `e`, `p`, `cid` e `cc`.
- **Relevância e severidade:** abreviações tornam a leitura de um fluxo já complexo dependente de voltar à extração do corpo HTTP. É uma melhoria de legibilidade, portanto LOW, sem alterar o contrato público dos campos recebidos.
- **Sinal reutilizável para a futura skill:** avaliar nomes locais pelo papel que precisam comunicar e pela extensão de seu uso, sem penalizar abreviações automaticamente.
- **Direção de correção proposta:** dar nomes explícitos às variáveis internas, preservando os nomes dos campos da API até uma decisão de compatibilidade.

#### P2-09 · LOW · Símbolo de receita sem uso

- **Evidência:** `utils.js, linha 10` declara `totalRevenue` e `linha 25` o exporta; `AppManager.js, linha 2` o importa. A busca nos três módulos não encontrou leitura ou atualização desse símbolo.
- **Relevância e severidade:** o símbolo sugere um estado de receita que a aplicação não utiliza, aumentando ruído e confundindo a origem dos valores do relatório. É código sem uso, classificado como LOW; não foi alegado erro no cálculo da receita por causa dele.
- **Sinal reutilizável para a futura skill:** confirmar referências de símbolos declarados, exportados e importados, considerando carregamento dinâmico e o escopo efetivamente analisado.
- **Direção de correção proposta:** remover declaração, exportação e importação após confirmar a ausência de consumidores externos.

### Projeto 3: `task-manager-api` (issue 006)

As referências abaixo apontam à revisão pública `478f362d9de8969ec41905b9dd9c5077a478daf0`, cujo código do Projeto 3 é idêntico ao da revisão local `99e2966` auditada antes da refatoração. Os arquivos atuais já foram alterados; consulte o [relatório posterior](reports/audit-project-3.md) para os resultados.

Análise estática realizada em 27/10/2026 dos quinze arquivos Python do projeto, incluindo seed e arquivos `__init__.py`, além de README e requisitos. Stack: Flask, Flask-SQLAlchemy e SQLite. O ambiente local foi consultado sem importar a aplicação: Python 3.13.7, Flask 3.0.0, Flask-SQLAlchemy 3.1.1 e SQLAlchemy 2.1.6. Domínio: tarefas, usuários, categorias e relatórios. Existem models, blueprints de rotas, um serviço de notificação e helpers; a leitura e a busca de referências não identificaram uso do serviço de notificação pelas rotas.

Foram selecionados oito problemas: dois CRITICAL, um HIGH, três MEDIUM e dois LOW. Não houve execução HTTP, envio de email, execução do seed ou refatoração nesta análise. A organização existente foi avaliada por responsabilidades e dependências, sem pressupor que deveria ser inteiramente substituída.

#### P3-01 · CRITICAL · Hashes de senha expostos nas respostas e proteção inadequada

- **Evidência:** [models/user.py, linhas 16–32](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/models/user.py#L16-L32) inclui `password` em `to_dict()` e usa MD5 direto, sem salt, para definir e verificar senhas. [routes/user_routes.py, linhas 27–40](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/user_routes.py#L27-L40) e [linhas 207–211](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/user_routes.py#L207-L211) enviam esse dicionário ao cliente.
- **Relevância e severidade:** a API expõe um verificador de senha inadequadamente protegido, facilitando tentativas offline sobre credenciais. A exposição de dados sensíveis justifica CRITICAL. Diferentemente do projeto 1, o valor exposto aqui é um hash, não a senha em texto puro. A [documentação do Python sobre armazenamento de senhas](https://docs.python.org/3.13/library/hashlib.html#key-derivation) explica a necessidade de funções próprias com salt e custo ajustável.
- **Sinal reutilizável para a futura skill:** rastrear campos sensíveis até a serialização e avaliar o mecanismo de armazenamento, distinguindo texto puro, codificação e derivação própria para senhas.
- **Direção de correção proposta:** excluir o verificador das respostas e planejar a migração do mecanismo de senha, considerando as credenciais já persistidas.

#### P3-02 · CRITICAL · Login fictício sem proteção efetiva das operações

- **Evidência:** [routes/user_routes.py, linhas 207–211](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/user_routes.py#L207-L211) devolve um token formado por texto fixo e ID; [linhas 119–125](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/user_routes.py#L119-L125) aceita alterações de papel e ativação e [linhas 134–148](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/user_routes.py#L134-L148) remove usuários e suas tarefas. A leitura da aplicação e das rotas não encontrou verificação de token ou permissão antes dessas operações.
- **Relevância e severidade:** o sucesso do login não cria uma barreira de acesso: as operações administrativas e destrutivas continuam disponíveis sem comprovação de identidade. Isso justifica CRITICAL. O campo `role` é alterável, mas não foi alegada a existência de uma autorização funcional que esse campo conseguiria contornar; o problema é justamente sua ausência.
- **Sinal reutilizável para a futura skill:** conferir a conexão entre emissão de credenciais, validação da identidade e autorização no ponto de uso; um endpoint de login ou um método `is_admin` isolado não comprova proteção.
- **Direção de correção proposta:** definir o contrato de autenticação e aplicar verificação de identidade e permissão nas operações protegidas, incluindo alterações de papel.

#### P3-03 · HIGH · Rotas acumulam regras, persistência e apresentação

- **Evidência:** [routes/task_routes.py, linhas 85–154](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L85-L154) lê HTTP, valida dados, consulta referências, constrói a entidade, confirma transação e formata resposta. [routes/report_routes.py, linhas 12–101](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/report_routes.py#L12-L101) concentra consultas, regras de atraso, cálculos e representação do relatório.
- **Relevância e severidade:** as regras ficam acopladas aos handlers HTTP e ao banco, apesar das pastas de camadas. HIGH reflete a dificuldade de testar e reutilizar o fluxo isoladamente. A existência de SQLAlchemy e blueprints é uma organização parcial real, que deve ser preservada onde fizer sentido.
- **Sinal reutilizável para a futura skill:** mapear o que os handlers fazem e quais responsabilidades podem ser testadas separadamente; não concluir conformidade MVC a partir da árvore de diretórios.
- **Direção de correção proposta:** separar roteamento, coordenação do fluxo, regras compartilhadas e acesso a dados dentro da arquitetura alvo, com migração incremental.

#### P3-04 · MEDIUM · Consultas por elemento nos relatórios

- **Evidência:** [routes/report_routes.py, linhas 53–68](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/report_routes.py#L53-L68) consulta tarefas uma vez para cada usuário; [linhas 157–165](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/report_routes.py#L157-L165) conta tarefas por categoria dentro de um loop.
- **Relevância e severidade:** a seção de produtividade exige uma consulta de usuários mais U consultas de tarefas; a listagem de categorias exige uma mais C contagens. O número de acessos cresce com os resultados, justificando MEDIUM. Não foi atribuída uma contagem fixa a todos os usos de `Query.get`, pois o cache da sessão pode influenciá-los.
- **Sinal reutilizável para a futura skill:** detectar consultas por elemento também em ORMs e distinguir consultas efetivas de acessos atendidos por cache ou carregamento antecipado.
- **Direção de correção proposta:** agregar ou carregar os dados relacionados em conjunto, mantendo os campos e as regras dos relatórios.

#### P3-05 · MEDIUM · Regra de atraso duplicada apesar de existir no model

- **Evidência:** [models/task.py, linhas 50–60](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/models/task.py#L50-L60) define `is_overdue`; [routes/task_routes.py, linhas 30–39](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L30-L39) e [linhas 71–80](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L71-L80), [routes/user_routes.py, linhas 171–180](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/user_routes.py#L171-L180) e [routes/report_routes.py, linhas 33–42](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/report_routes.py#L33-L42) repetem a regra em vez de chamá-la. A busca de referências não encontrou consumidores do método.
- **Relevância e severidade:** uma mudança no conceito de tarefa atrasada exige sincronizar várias cópias, favorecendo divergências futuras. Duplicação de regra justifica MEDIUM; não foi afirmado que todas as cópias já produzem resultados diferentes.
- **Sinal reutilizável para a futura skill:** comparar comportamento duplicado entre camadas e verificar se abstrações existentes são realmente utilizadas, em vez de criar novas por padrão.
- **Direção de correção proposta:** adotar um ponto de definição para a regra e reutilizá-lo, inclusive em consultas e relatórios quando aplicável.

#### P3-06 · MEDIUM · APIs deprecated e legacy presentes no ambiente utilizado

- **Evidência:** [models/task.py, linhas 15–16](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/models/task.py#L15-L16) usa `datetime.utcnow` como default e [routes/task_routes.py, linhas 30–32](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L30-L32) o chama em comparações. [Linhas 65–67](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L65-L67) usa `Task.query.get`. Os usos também aparecem em outros models, rotas e no seed.
- **Relevância e severidade:** `datetime.utcnow()` está deprecated desde Python 3.12, e `Query.get()` é um método legacy/deprecated desde SQLAlchemy 2.0; ambas as condições se aplicam às versões locais conferidas. MEDIUM reflete dívida de compatibilidade e padronização, sem afirmar que os métodos já foram removidos ou que impedem o boot. Fontes oficiais: [Python 3.13](https://docs.python.org/3.13/library/datetime.html#datetime.datetime.utcnow) e [SQLAlchemy 2.1](https://docs.sqlalchemy.org/en/21/orm/queryguide/query.html#sqlalchemy.orm.Query.get), consultadas em 27/10/2026.
- **Sinal reutilizável para a futura skill:** cruzar símbolo, biblioteca e versão detectada com documentação oficial; registrar o substituto e as condições da migração. Aparência antiga ou dependência desatualizada, isoladamente, não comprova uso deprecated.
- **Direção de correção proposta:** migrar consultas por chave para `db.session.get(Task, task_id)` e datas UTC para uma política consistente baseada em `datetime.now(UTC)`. A migração temporal exige revisar defaults, datas persistidas e datas de entrada: trocar uma chamada isolada pode misturar valores com e sem fuso e quebrar comparações. Não foi aprovada uma estratégia de migração nesta análise.

#### P3-07 · LOW · Limites de negócio usados sem as constantes existentes

- **Evidência:** [routes/task_routes.py, linhas 96–114](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L96-L114) usa diretamente limites de título, prioridade padrão e intervalo de prioridades. [utils/helpers.py, linhas 110–116](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/utils/helpers.py#L110-L116) já contém nomes para limites e valores padrão, mas as rotas não os importam.
- **Relevância e severidade:** números locais obrigam a reconstruir seu significado e deixam definições nomeadas sem uso. É um problema de clareza, LOW; não foi afirmado que os valores atuais estejam incorretos. A definição de quais valores pertencem à configuração ou ao domínio fica para a refatoração.
- **Sinal reutilizável para a futura skill:** reconhecer literais de domínio e procurar definições existentes antes de sugerir novas constantes; excluir números convencionais do protocolo da análise automática indiscriminada.
- **Direção de correção proposta:** nomear e reutilizar os limites aplicáveis, evitando criar uma segunda coleção de constantes equivalentes.

#### P3-08 · LOW · Imports sem uso nos módulos analisados

- **Evidência:** [routes/task_routes.py, linha 7](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/routes/task_routes.py#L7) importa `json`, `os`, `sys` e `time` sem referências no restante do módulo; [utils/helpers.py, linhas 3–7](https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill/blob/478f362d9de8969ec41905b9dd9c5077a478daf0/task-manager-api/utils/helpers.py#L3-L7) importa `os`, `json`, `sys`, `math` e `hashlib` sem uso no arquivo.
- **Relevância e severidade:** os imports adicionam ruído e sugerem dependências que o módulo não utiliza. É limpeza de legibilidade, LOW, sem alegar impacto relevante de performance.
- **Sinal reutilizável para a futura skill:** conferir imports e referências com análise apropriada à linguagem, preservando imports necessários por efeitos colaterais ou descoberta de módulos.
- **Direção de correção proposta:** remover somente os imports confirmados como dispensáveis; não aplicar remoção indiscriminada aos `__init__.py` que registram models.

### Relação com a futura skill

Cada achado separa **sinal observável, evidência, impacto, severidade e direção de correção**. Essa é a contribuição desta análise para a construção de uma skill agnóstica: manter critérios gerais e adaptar a maneira de reconhecê-los à stack detectada. Por exemplo, uma consulta dentro de um loop pode aparecer com `sqlite3` em Python ou com um cliente de banco em JavaScript; o problema é o comportamento, não o nome da biblioteca.

As três análises manuais estão documentadas. Seus sinais serviram de insumo para o desenho aprovado na issue 007 e para a construção registrada na issue 008. Os critérios mínimos foram atendidos separadamente em cada projeto e não substituem os requisitos próprios do catálogo e do playbook.

As evidências mostram três cuidados para o desenho: adaptar a detecção à linguagem e às bibliotecas, avaliar responsabilidades mesmo quando já existem camadas e confirmar depreciações para a versão utilizada. Não se deve assumir SQL Injection por qualquer interpolação: por exemplo, o uso de `Task.title.like(f'%{query}%')` em uma expressão do ORM exige verificar como a biblioteca vincula os parâmetros, em vez de equipará-lo à concatenação de SQL bruto do projeto 1. As análises não demonstram ainda que uma skill seja agnóstica; essa capacidade deverá ser validada por sua execução posterior nos três projetos.

## Construção da Skill

A implementação inicial está em [`code-smells-project/.agents/skills/refactor-arch/`](code-smells-project/.agents/skills/refactor-arch/SKILL.md), conforme a escolha de Codex e o desenho aprovado. A criação foi conferida com validação estrutural e exemplos isolados. As cópias foram usadas nos projetos 2 e 3 nas issues 010 e 011. As três pastas contêm os mesmos seis arquivos, incluindo a melhoria de isolamento de 03/11/2026.

### Organização e fluxo

| Arquivo | Função |
| --- | --- |
| [`SKILL.md`](code-smells-project/.agents/skills/refactor-arch/SKILL.md) | Coordenar análise, auditoria com pausa e refatoração validada; definir o limite de autorização. |
| [`project-analysis.md`](code-smells-project/.agents/skills/refactor-arch/references/project-analysis.md) | Descobrir stack, versões, arquitetura, interfaces e meios concretos de validação. |
| [`anti-patterns.md`](code-smells-project/.agents/skills/refactor-arch/references/anti-patterns.md) | Investigar padrões com sinais, severidade contextual e cuidados contra falsos positivos. |
| [`audit-report.md`](code-smells-project/.agents/skills/refactor-arch/references/audit-report.md) | Padronizar achados, evidências, impactos, proposta e plano de validação antes da aprovação. |
| [`mvc-guidelines.md`](code-smells-project/.agents/skills/refactor-arch/references/mvc-guidelines.md) | Definir responsabilidades MVC adaptáveis, configuração, erros e entrada da aplicação. |
| [`refactoring-playbook.md`](code-smells-project/.agents/skills/refactor-arch/references/refactoring-playbook.md) | Relacionar os padrões a transformações antes/depois e verificações observáveis. |

As cinco áreas em referências Markdown e as três fases são exigências do curso. A organização por assunto, os nomes dos arquivos e a ligação por IDs `AP-01` a `AP-12` / `T-01` a `T-12` são decisões de implementação. O coordenador indica quando consultar cada referência; o conhecimento detalhado fica no assunto correspondente.

### Catálogo e exemplos

Foram incluídos doze padrões: injeção em consultas; exposição de dados sensíveis; armazenamento inadequado de senhas; controle de acesso insuficiente; concentração de responsabilidades; estado global mutável; operações relacionadas sem consistência; N+1; regras/validações duplicadas; tratamento inadequado de erros; APIs deprecated; valores de domínio sem significado explícito.

A seleção cobre segurança, arquitetura, integridade, performance e manutenção nas quatro severidades. Cada mecanismo tem uma transformação com exemplo antes/depois e critérios de conferência. A quantidade ultrapassa o mínimo de oito porque separar mecanismos com correções diferentes torna a orientação mais clara. Não foi criada uma entrada por achado manual.

### Agnosticismo e decisões de execução

- O catálogo descreve mecanismos e fluxos, sem condições baseadas nos nomes dos três projetos. Os exemplos em Python e JavaScript são ilustrativos, e o agente deve investigar também problemas fora da lista. Isso é uma estratégia de desenho; funcionamento em outras tecnologias ainda não foi demonstrado.
- A estrutura MVC segue responsabilidades, aproveitando separações existentes. Serviços e outras camadas auxiliares exigem necessidade concreta; não há uma árvore de diretórios imposta a toda stack.
- A auditoria deve apresentar evidência com arquivo/linhas, impacto e correção. Um sinal isolado não comprova vulnerabilidade, N+1 ou depreciação; severidades precisam de justificativa.
- A Fase 2 apresenta o relatório na conversa e pausa antes de qualquer gravação, inclusive do próprio relatório. Somente após aprovação do escopo concreto podem ser preparados dados/testes e aplicadas mudanças. Assim, salvar evidências não contorna a pausa exigida.
- Correções que mudam resposta, autorização ou armazenamento devem explicitar o impacto e o resultado esperado antes da aprovação. Preservar funcionamento legítimo não exige preservar exposição de credenciais.
- Depreciações exigem biblioteca/versão e fonte oficial aplicável. A busca é agrupada por símbolo/versão; dúvidas ficam explícitas. As fontes dos exemplos estão no catálogo e no playbook.
- Boot, dados isolados e cenários dos endpoints são descobertos por projeto e planejados na auditoria. A execução verifica antes/depois e distingue falhas originais, regressões e itens não executados.

### Conferência e limites atuais

Na criação, passaram o validador de frontmatter, a resolução dos 21 links/âncoras internos, a análise sintática dos 24 blocos de código e verificações isoladas dos mecanismos das doze transformações, com dados sintéticos. Os exemplos de autorização e propagação de erros usaram substitutos das dependências; não representam teste integrado de uma aplicação.

As issues 009, 010 e 011 registram a aplicação das três fases, com pausa e aprovação humana posterior antes das refatorações. Os resultados estão consolidados abaixo. A conferência da issue 012 confirmou igualdade dos seis arquivos nas três cópias; não repetiu as suítes. Descoberta automática no T3 e funcionamento universal permanecem não demonstrados.

### Desafios e iteração após o incidente no Projeto 3

Em 30/10/2026, um teste definiu uma URI temporária, mas importou a aplicação original, que ignorava essa configuração. `drop_all/create_all` atingiu `task-manager-api/instance/tasks.db` e apagou os dados anteriores. A instrução de isolamento já existia; a execução falhou ao não comprovar o destino efetivo antes da escrita. Não foi encontrada cópia anterior nos locais consultados.

Após autorização, os exemplos foram recriados a partir do seed em cópia isolada e repostos: 3 usuários, 4 categorias e 10 tarefas, com integridade `ok`. Isso não é restauração exata dos dados perdidos, das datas ou de eventuais alterações anteriores. A cópia pós-incidente foi registrada em `/private/tmp/task-manager-011-after-incident.db`; esse arquivo temporário não integra a entrega nem é um backup durável.

Em 03/11/2026, foi autorizado reforçar a skill antes da retomada. `SKILL.md` e `references/project-analysis.md` passaram a exigir barreira antes de imports com efeitos, conferência da origem do código e do destino efetivo, interrupção quando não houver comprovação e nova avaliação quando as condições mudarem. A orientação inclui cenários negativos de configuração ignorada, origem inesperada e destino fora da fronteira.

As três cópias foram sincronizadas e validadas estruturalmente. A avaliação independente da orientação foi por leitura de cenário, sem execução comportamental independente e sem garantia técnica de obediência do agente. A validação posterior da API usou cópias sintéticas protegidas por `sandbox-exec`, com acesso ao projeto original e à rede externa bloqueado. Os testes usaram SQLite em memória e recusaram um banco sentinela em arquivo, mesmo com flag de teste forjada. O hash do banco local permaneceu igual durante essa Fase 3 e na leitura da issue 012; isso não desfaz o incidente anterior.

O relato completo e os limites estão no [relatório do Projeto 3](reports/audit-project-3.md).

## Resultados

### Auditorias e critérios mínimos

As contagens abaixo são dos diagnósticos anteriores às refatorações. Representam achados identificados, não problemas que necessariamente continuam presentes. As comparações com a análise manual não foram cegas: o material manual estava disponível.

| Projeto / relatório | Stack e domínio | CRITICAL | HIGH | MEDIUM | LOW | Total | Correspondências manuais |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [1](reports/audit-project-1.md) | Python/Flask · e-commerce | 4 | 3 | 4 | 2 | 13 | 9/9 |
| [2](reports/audit-project-2.md) | JavaScript/Express · LMS e checkout | 3 | 3 | 3 | 2 | 11 | 9/9 |
| [3](reports/audit-project-3.md) | Python/Flask · tarefas | 2 | 2 | 4 | 2 | 10 | 8/8 |

| Critério obrigatório do curso | Projeto 1 | Projeto 2 | Projeto 3 |
| --- | --- | --- | --- |
| Fase 1 detecta a stack corretamente | Atendido | Atendido | Atendido |
| Fase 2 encontra pelo menos 5 achados | 13 | 11 | 10 |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | 7 | 6 | 4 |
| Fase 3: boot e endpoints funcionam após refatoração | 19 métodos/caminhos | 3 métodos/caminhos | 22 métodos/caminhos |

O atendimento está delimitado aos cenários documentados. Todos os métodos/caminhos originais foram preservados, com correções de autorização, senha, validação e erros aprovadas. Os contratos de acesso atuais estão nos READMEs das APIs; uma requisição antiga sem credencial pode passar a retornar 401/403.

### Estrutura antes/depois

| Projeto | Antes | Depois |
| --- | --- | --- |
| 1 | 4 módulos: `app.py`, `controllers.py`, `models.py`, `database.py`; SQL também em handlers e conexão global | 19 módulos de produção: app factory, config, conexão por contexto, `routes/`, `controllers/`, `models/`, `views/`, segurança e erros centrais |
| 2 | 3 módulos; `AppManager` concentra esquema, seeds, rotas, SQL e regras; boot no import | 19 módulos de produção em `src/`: composição/entrada, config, banco, models, controllers, serviço de checkout, rotas, presenters, middleware e segurança |
| 3 | 15 módulos Python, incluindo seed e inicializadores; models e blueprints existentes, regras e consultas nas rotas | 24 módulos de produção: models e blueprints preservados, serviços de domínio/consultas, `middleware/`, config, tokens e utilitário UTC; import sem criação de tabelas |

Os blueprints do Projeto 3 continuam como adaptadores HTTP e os serviços coordenam operações e consultas. A representação permanece entre models e adaptadores. É uma adaptação das responsabilidades MVC ao Flask, sem exigir pastas chamadas `controllers` e `views` para comprovar o padrão. A árvore detalhada e os contratos estão nos [READMEs do Projeto 1](code-smells-project/README.md), [Projeto 2](ecommerce-api-legacy/README.md) e [Projeto 3](task-manager-api/README.md).

### Validação registrada e aplicações em execução

| Projeto | Suíte registrada | HTTP antes/depois | Evidências de boot e encerramento |
| --- | --- | --- | --- |
| 1 · 29/10 | 41 testes, zero falhas/erros | 19/19 operações em cada versão, com persistência por conexão independente | [Antes](reports/evidence/project-1-http-before.json), [depois](reports/evidence/project-1-http-after.json), [resumo](reports/evidence/project-1-validation.json) |
| 2 · 29/10 | 38 testes, zero falhas/skips | 9 cenários antes e 11 depois, cobrindo os 3 endpoints | [Antes](reports/evidence/project-2-http-before.json), [depois](reports/evidence/project-2-http-after.json), [processo real](reports/evidence/project-2-process-smoke.json), [log TAP](reports/evidence/project-2-tests.tap), [resumo](reports/evidence/project-2-validation.json) |
| 3 · 03/11 | 32 testes na issue 011; 38 na revisão da issue 012, em cópia protegida | 24 requisições em cada versão: 22 métodos/caminhos originais e 2 verificações extras | [Antes](reports/evidence/project-3-http-before.json), [depois](reports/evidence/project-3-http-after.json), [processo real](reports/evidence/project-3-process-smoke.json), [log de testes](reports/evidence/project-3-tests.log), [resumo histórico](reports/evidence/project-3-validation.json), [revisão atual](reports/evidence/project-3-quality-validation.json) |

Excertos dos registros estruturados de execução após refatoração, sem credenciais:

```text
Projeto 1 · project-1-http-after.json: "boot": "ok"; 19 operações registradas.
Projeto 2 · project-2-process-smoke.json: "boot": true; "reportStatus": 200;
            "checkoutStatus": 200; "exitCode": 0; "processClosed": true.
Projeto 3 · project-3-process-smoke.json: "status": 200; "health": "ok";
            "process_exit": "SIGTERM (encerrado após verificação)".
```

Os arquivos HTTP são logs estruturados de requisições reais em loopback. No Projeto 3, as sequências de status antes/depois são iguais; isso não demonstra igualdade integral das respostas. A suíte complementa essa evidência com casos de autenticação, permissões, persistência e datas. Os 32 testes e os registros de HTTP/boot do Projeto 3 pertencem à issue 011. Na primeira consolidação, a issue 012 só conferiu artefatos; na revisão posterior, executou a suíte integrada do Projeto 3 antes e depois da correção numérica, chegando a 38 testes. A suíte atual usa Flask test client, sem novo HTTP real; os logs históricos foram preservados.

### Checklist oficial por projeto

Cada célula marcada resume as evidências e os limites do respectivo relatório; não representa certificação de segurança ou cobertura exaustiva.

| Fase / item do enunciado | Projeto 1 | Projeto 2 | Projeto 3 |
| --- | --- | --- | --- |
| 1 · Linguagem detectada | [x] Python | [x] JavaScript | [x] Python |
| 1 · Framework detectado | [x] Flask | [x] Express | [x] Flask |
| 1 · Domínio descrito | [x] E-commerce | [x] LMS | [x] Task Manager |
| 1 · Arquivos analisados condizentes | [x] 4 originais | [x] 3 originais | [x] 15 originais |
| 2 · Relatório segue o template | [x] | [x] | [x] Detalhado na issue 012; reconstrução posterior identificada |
| 2 · Arquivo e linhas originais por achado | [x] | [x] | [x] |
| 2 · Ordem CRITICAL → LOW | [x] | [x] | [x] |
| 2 · Pelo menos 5 achados | [x] 13 | [x] 11 | [x] 10 |
| 2 · Investigação de APIs deprecated | [x] Nenhuma confirmada; cobertura parcial | [x] Nenhuma confirmada; cobertura parcial | [x] utcnow e Query.get |
| 2 · Pausa e aprovação antes de alterações | [x] issue 009 | [x] issue 010 | [x] issue 011 |
| 3 · Estrutura e responsabilidades MVC | [x] | [x] | [x] Adaptação com blueprints/serviços |
| 3 · Configuração extraída | [x] | [x] | [x] |
| 3 · Models abstraem dados | [x] | [x] | [x] Com consultas em serviços |
| 3 · Views/Routes separadas | [x] | [x] | [x] Serialização em models/adaptadores |
| 3 · Controllers concentram o fluxo | [x] | [x] Serviço transacional auxiliar | [x] Adaptadores HTTP e serviços |
| 3 · Tratamento de erros central | [x] | [x] | [x] |
| 3 · Entry point claro | [x] | [x] | [x] |
| 3 · Aplicação inicia sem erros | [x] Config válida e banco sintético | [x] Config válida e banco em memória | [x] Config válida em cópia isolada |
| 3 · Endpoints originais respondem | [x] 19 | [x] 3 | [x] 22 |

### Comportamento da skill e limites

A mesma skill usada em Flask no Projeto 1 foi copiada sem ajustes para Node/Express no Projeto 2. Ela orientou a detecção da God Class, a composição sem boot no import e o checkout transacional, sem transportar a estrutura Flask literalmente. No Projeto 3, identificou problemas apesar das pastas existentes e preservou separações úteis. O reforço posterior de isolamento foi sincronizado nas três cópias; os projetos 1 e 2 não tiveram nova execução integral da skill após esse reforço.

- **Projeto 1:** SQL administrativo foi preservado por decisão aprovada, atrás de admin, CSRF e opt-in. Continua permitindo SQL irrestrito ao administrador confiável. Nenhum banco real foi migrado/resetado. Migração de senhas exige base offline integralmente em texto puro; não há inferência para bases mistas.
- **Projeto 2:** SQLite é somente em memória; reinício perde os dados. Gateway é simulado, sem cobrança/email real. Senhas legadas exigiriam reset próprio; token administrativo compartilhado e fila local não constituem operação de produção. Carga, persistência e auditoria de vulnerabilidades transitivas ficaram fora do escopo.
- **Projeto 3:** F-08 foi ampliado e resolvido no escopo identificado de corpo, tipos, filtros e fronteiras numéricas, com testes RED→GREEN na issue 012; cobertura exaustiva não demonstrada. Contas MD5 sem novo login continuam legadas. SMTP real e migração de dados existentes não foram exercitados. UTC naive foi preservado para compatibilidade. Mesmos status HTTP não provam equivalência integral, e o incidente/recriação dos exemplos permanece parte do resultado.
- **Geral:** não há benchmark de latência, deploy ou prova de ausência de falhas. A redução de consultas mede quantidade de acessos, não tempo de resposta. Descoberta automática no T3 e comportamento em tecnologias além das duas stacks fornecidas não foram comprovados.

### Disponibilidade e rastreabilidade

O repositório contém as três APIs refatoradas, as três cópias da skill, os relatórios e as evidências descritas acima. As revisões de auditoria `769ee59` e `99e2966` identificam estados do histórico local de trabalho; os arquivos originais dos projetos 2 e 3 nessas revisões são idênticos aos da base pública `478f362`. A execução da baseline do Projeto 2 usa a base pública para permitir reprodução neste repositório.

## Como Executar

### Pré-requisitos e preparação

Git com o histórico das revisões auditadas; Codex CLI instalado, autenticado e configurado; Python e ambientes separados para cada API Flask; Node.js 22 ou superior e npm para a API Express. As execuções registraram Python 3.13.7 e Node 24.20.0/npm 11.19.0. Os manifests Python fixam dependências diretas, mas não todas as transitivas; uma instalação nova pode resolver versões diferentes das registradas nos relatórios.

Em uma cópia nova da entrega já publicada, instale as dependências a partir da raiz. Os comandos abaixo são instruções de reprodução; não foram executados na issue 012.

```sh
cd code-smells-project
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd ..
cd task-manager-api
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd ..
cd ecommerce-api-legacy
npm ci
cd ..
```

Use `python3` se ele corresponder ao runtime desejado. Mantenha as duas `.venv` separadas, pois os projetos usam versões distintas de Flask. Para a validação isolada do Projeto 3, o Python precisa continuar executável após a cópia e sem leitura do diretório pessoal, como explicado no README da API.

### Invocar a skill em cada projeto

Escolha um bloco por vez, partindo da raiz do repositório, e use uma sessão por projeto:

```sh
cd code-smells-project
codex '$refactor-arch Execute somente as Fases 1 e 2 neste projeto e aguarde minha aprovação.'
```

```sh
cd ecommerce-api-legacy
codex '$refactor-arch Execute somente as Fases 1 e 2 neste projeto e aguarde minha aprovação.'
```

```sh
cd task-manager-api
codex '$refactor-arch Execute somente as Fases 1 e 2 neste projeto e aguarde minha aprovação.'
```

As aspas simples preservam o `$` literal no shell. O path adotado é `.agents/skills/refactor-arch/`, adaptação ao Codex permitida pelo enunciado. A [documentação oficial de skills](https://learn.chatgpt.com/docs/build-skills), conferida em 03/11/2026, descreve esse diretório e a invocação explícita por `$` ou `/skills` no CLI/IDE. O comando e a documentação não comprovam a descoberta na instalação T3 usada nas sessões anteriores; esse limite permanece registrado. Se a skill não aparecer, confira o diretório atual e a leitura do `SKILL.md` local antes de prosseguir.

O checkout entregue já está refatorado: nova auditoria examina o código atual e não deve ser esperada a mesma quantidade de achados históricos. Para observar o estado anterior, consulte as revisões indicadas nos relatórios; qualquer execução do legado deve usar cópia descartável e isolamento comprovado.

A Fase 2 entrega o relatório na conversa e pausa. Revise achados, mudanças de contrato, destino do relatório e plano de validação. A Fase 3 só começa após resposta posterior de aprovação; ela também deve comprovar origem, barreira e destino efetivo antes de imports, boot ou testes com efeitos. Nova invocação não autoriza automaticamente seeds, migrações, push ou deploy.

### Iniciar as APIs e conferir o resultado

Siga os comandos de configuração e boot dos READMEs de cada API em um banco novo/descartável:

| Projeto | Configuração principal | Boot | Preparação e contratos |
| --- | --- | --- | --- |
| 1 | `DATABASE_PATH`, `SECRET_KEY`; cookie Secure ajustado apenas para HTTP local | `.venv/bin/python -B app.py` | [init-db, create-admin e contratos](code-smells-project/README.md) |
| 2 | `ADMIN_API_TOKEN`; demo opcional com `SEED_DEMO=1` e `DEMO_PASSWORD` | `npm start` | [Banco em memória, demo e contratos](ecommerce-api-legacy/README.md) |
| 3 | `TASK_SECRET_KEY` e `TASK_DATABASE_URI` apontando para banco descartável | `.venv/bin/python app.py` | [init-db, bootstrap-admin e contratos](task-manager-api/README.md) |

As APIs Flask usam a porta 5000 e devem ser iniciadas uma por vez; Node usa 3000. `GET /health` verifica prontidão das APIs Flask; no Node, o relatório financeiro com Bearer válido verifica o boot. Confira também criação, leitura, alteração/exclusão disponíveis e persistência, usando as permissões aprovadas. Encerre cada processo ao terminar. O seed do Projeto 3 apaga dados e não é necessário para iniciar a API.

Com dependências preparadas, estes são os comandos de validação documentados, cada um no diretório da respectiva API:

```sh
# Projeto 1: fixtures em bancos temporários; HTTP em porta efêmera.
.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s tests -v
.venv/bin/python -B tools/validate_http.py
```

```sh
# Projeto 2: SQLite em memória e HTTP local.
NPM_CONFIG_USERCONFIG=/dev/null npm test
```

```sh
# Projeto 3, macOS: cópia temporária e barreira externa antes dos testes.
tests/run_sandbox_macos.sh
```

No Projeto 3, não execute `unittest` diretamente no workspace original nem use `run_isolated.py` como substituto da barreira externa. O wrapper testa a contenção antes de importar a aplicação; se `sandbox-exec` não puder criar a barreira, a parte dependente deve parar. Em outro sistema operacional, é necessário preparar contenção equivalente; esse caminho não foi validado. Os logs HTTP e de boot da issue 011 estão versionados, mas sua geração não está automatizada pelo wrapper da suíte.

Os coletores opcionais de antes/depois do Projeto 2 estão no README da API; a baseline depende do histórico Git. Compare os resultados esperados nos relatórios, conferindo respostas, dados persistidos, cenários negativos e encerramento dos processos. Os números 41/38/32 são das execuções originais; a revisão posterior do Projeto 3 ampliou sua suíte para 38 testes. São evidências dos ambientes registrados, não uma promessa de resultado em qualquer ambiente.
