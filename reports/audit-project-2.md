# Auditoria do Projeto 2 · issue 010

## Identificação e escopo original

- Projeto: `ecommerce-api-legacy/`, raiz do repositório MBA Entrega 3.
- Data: 29/10/2026. Revisão original: `769ee59bdf72c051197ba85d6ff14cd4b3997d6a`.
- Código próprio analisado: 3/3 arquivos JS, 180 linhas (`src/app.js`, `src/AppManager.js`, `src/utils.js`); lidos também manifesto, lockfile, README e api.http. Dependências internas, infraestrutura e outros projetos excluídos.
- Stack: JavaScript/CommonJS; Node disponível24.20.0, npm11.19.0 (sem engine original). Express declarado^4.18.2, resolvido/instalado4.22.1; sqlite3 declarado^5.1.6, resolvido/instalado5.1.7.
- Domínio: LMS, usuários, cursos, matrículas e pagamentos. SQLite em memória por conexão. Gateway simulado por prefixo de cartão; nenhuma chamada de rede ou envio de email nos módulos lidos.
- Arquitetura: AppManager concentra banco, seeds, rotas, regras e saídas. app.js inicializa tudo e escuta3000 ao ser carregado.
- Estado inicial: fontes versionadas limpas; somente seis arquivos da skill copiados com autorização. Cópia idêntica por SHA-256; skill não alterada nesta issue.

| Interface original | Origem original |
|---|---|
| POST /api/checkout | src/AppManager.js:28–78 |
| GET /api/admin/financial-report | src/AppManager.js:80–129 |
| DELETE /api/users/:id | src/AppManager.js:131–136 |

## Resumo original da Fase 2

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 3 |
| HIGH | 3 |
| MEDIUM | 3 |
| LOW | 2 |
| Total | 11 |

Os nove achados manuais P2-01 a09 foram confirmados, preservando suas severidades. P2-10 e11 são adicionais. A Fase2 foi apresentada na conversa e encerrada sem boot, relatório em disco ou alterações na API. A evidência inicial de todos os achados era estática; reproduções posteriores aparecem no complemento, sem reescrever esse diagnóstico.

## Achados na revisão original

### P2-01 · CRITICAL · God Class

- **Padrão:** AP-05 / T-05.
- **Localização:** `src/AppManager.js:4–25,28–136` (linhas originais, anteriores à refatoração).
- **Evidência:** Cria banco e esquema, registra rotas, executa SQL, decide checkout e produz respostas.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Acoplamento de infraestrutura, domínio e HTTP; CRITICAL segundo a escala do curso.
- **Correção e mudança observável propostas:** MVC com composição, Models, Controllers, rotas e apresentação; serviço para checkout.
- **Verificação proposta:** Mesmos três endpoints por HTTP e regras testáveis sem objetos HTTP.
- **Comparação manual:** Confirmado, mesma severidade.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-02 · CRITICAL · Cartão e configuração enviados ao log

- **Padrão:** AP-02 / T-02.
- **Localização:** `src/AppManager.js:33,45; utils.js:1–7` (linhas originais, anteriores à refatoração).
- **Evidência:** Cartão do corpo HTTP e configuração do gateway são interpolados no console. Valores omitidos.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Exposição de dado sensível. Validade da chave de exemplo não demonstrada.
- **Correção e mudança observável propostas:** Logs mínimos de evento e identificador, sem cartão/senha/token/chave.
- **Verificação proposta:** Ausência de valores sintéticos sensíveis nos logs e respostas.
- **Comparação manual:** Confirmado, mesma severidade.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-03 · CRITICAL · Controle de acesso insuficiente

- **Padrão:** AP-04 / T-04.
- **Localização:** `src/app.js:5–10; AppManager.js:40,66–74,80–83,131–135` (linhas originais, anteriores à refatoração).
- **Evidência:** Só há parser JSON; relatório/exclusão são públicos; checkout existente usa email sem verificar senha.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Operação administrativa/destrutiva e vínculo de usuário sem identidade confiável. Proteções externas desconhecidas.
- **Correção e mudança observável propostas:** Bearer administrativo externo nas operações privilegiadas; senha verificada no checkout existente.
- **Verificação proposta:** Admin válido funciona; ausente/inválido401; senha incorreta401 sem gravação.
- **Comparação manual:** Confirmado e ampliado com checkout por email.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-04 · HIGH · Proteção inadequada de senha

- **Padrão:** AP-03 / T-03.
- **Localização:** `src/utils.js:17–22; AppManager.js:18,68–69` (linhas originais, anteriores à refatoração).
- **Evidência:** Função repete só dois caracteres Base64; senha padrão e seed em texto puro.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Credenciais não protegidas; não há login original cujo bypass tenha sido alegado.
- **Correção e mudança observável propostas:** scrypt assíncrono, salt aleatório, formato versionado, senha obrigatória; legado rejeitado para reset explícito.
- **Verificação proposta:** Senhas diferentes não colidem, mesmo segredo tem salts diferentes, senha inválida/legada não autentica.
- **Comparação manual:** Confirmado e ampliado com seed.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-05 · HIGH · Checkout sem atomicidade

- **Padrão:** AP-07 / T-07.
- **Localização:** `src/AppManager.js:46–71` (linhas originais, anteriores à refatoração).
- **Evidência:** Usuário é criado antes da decisão de recusa; matrícula, pagamento e auditoria separados sem rollback.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Falhas deixam usuário/matrícula sem operação completa.
- **Correção e mudança observável propostas:** Transação local com rollback e fila para toda a conexão; cache após commit.
- **Verificação proposta:** Falhas SQLite em cada insert e recusa mantêm estado anterior; concorrência não mistura operações.
- **Comparação manual:** Confirmado e ampliado com usuário antecipado.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-10 · HIGH · Exclusão deixa vínculos órfãos

- **Padrão:** AP-07 / T-07.
- **Localização:** `src/AppManager.js:12–15,113,131–135` (linhas originais, anteriores à refatoração).
- **Evidência:** Remove usuário sem remover ou impedir referências de matrículas.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Histórico financeiro perde vínculo; operação distinta do checkout.
- **Correção e mudança observável propostas:** Restrição referencial; exclusão vinculada409, sem vínculo200, inexistente404.
- **Verificação proposta:** Conferir todos os registros após tentativa vinculada e remoção efetiva sem vínculo.
- **Comparação manual:** Adicional à seleção manual.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-06 · MEDIUM · Consultas por elemento

- **Padrão:** AP-08 / T-08.
- **Localização:** `src/AppManager.js:83–106` (linhas originais, anteriores à refatoração).
- **Evidência:** Uma consulta inicial, uma por curso e duas por matrícula: 1+C+2E.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Crescimento de acessos, sem latência medida na auditoria.
- **Correção e mudança observável propostas:** Consulta em conjunto, sem multiplicar pagamentos/receita; manter cursos vazios e campos.
- **Verificação proposta:** Comparar conteúdo e quantidade de consultas em cardinalidades diferentes.
- **Comparação manual:** Confirmado, mesma severidade.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-07 · MEDIUM · Erros ignorados ou mal traduzidos

- **Padrão:** AP-10 / T-10.
- **Localização:** `src/AppManager.js:38,57–60,92–93,104–106,133–135` (linhas originais, anteriores à refatoração).
- **Evidência:** Ignora err em callbacks; erro de banco pode virar404 ou falso sucesso.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Resposta incompatível com operação e exceção secundária.
- **Correção e mudança observável propostas:** Propagação explícita adequada a Express4; middleware central e erros de domínio distintos.
- **Verificação proposta:** Falha de consulta500 sem detalhes internos; curso ausente404; resposta única e recuperação.
- **Comparação manual:** Confirmado e ampliado.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-11 · MEDIUM · Validação de presença sem tipos

- **Padrão:** AP-09 / T-09.
- **Localização:** `src/AppManager.js:29–35,46,68` (linhas originais, anteriores à refatoração).
- **Evidência:** Truthy não garante texto; código chama startsWith e Buffer.from depois.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Entrada malformada pode causar exceção após início do fluxo.
- **Correção e mudança observável propostas:** Validação no limite HTTP de tipos, limites e ID positivo; campos originais preservados.
- **Verificação proposta:** Tipos inválidos400 sem gravação; ID ausente/zero/inseguro rejeitado.
- **Comparação manual:** Adicional à seleção manual.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-08 · LOW · Nomes internos pouco expressivos

- **Padrão:** Nomenclatura / transformação contextual.
- **Localização:** `src/AppManager.js:29–35` (linhas originais, anteriores à refatoração).
- **Evidência:** u, e, p, cid e cc exigem reconstruir significado durante callbacks.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Legibilidade localizada.
- **Correção e mudança observável propostas:** Nomes explícitos sem renomear usr/eml/pwd/c_id/card públicos.
- **Verificação proposta:** Fluxo válido continua aceitando mesmos campos públicos.
- **Comparação manual:** Confirmado, mesma severidade.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

### P2-09 · LOW · Receita global sem consumo

- **Padrão:** Código sem uso / remoção contextual.
- **Localização:** `src/utils.js:10,25; AppManager.js:2` (linhas originais, anteriores à refatoração).
- **Evidência:** totalRevenue declarado, exportado e importado, sem leitura/atualização nos três módulos.
- **Método e limite:** inspeção estática; falha ainda não reproduzida na Fase2.
- **Impacto e severidade:** Ruído; não se atribui erro no cálculo a esse símbolo.
- **Correção e mudança observável propostas:** Remover estado sem consumidor; cache útil passa a ser por instância.
- **Verificação proposta:** Revisão de referências e relatório preservado. Consumidores externos não identificados.
- **Comparação manual:** Confirmado, mesma severidade.
- **Dependências/incertezas:** dados e identidades reais não investigados; aplicar somente no ambiente isolado aprovado. Legado exige política explícita de reset, não conversão por heurística.

## APIs deprecated e cobertura documental

Nenhum uso deprecated confirmado no código próprio. Função caseira insegura não é API deprecated. Não converter a idade de Express4 ou as14 vulnerabilidades históricas de instalação em findings sem aplicabilidade demonstrada.

| Biblioteca/versão | Símbolos | Situação e fonte oficial consultada em29/10/2026 | Limite |
|---|---|---|---|
| Node24.20.0 | Buffer.from/string, toString/base64 | Documentados em https://nodejs.org/download/release/v24.20.0/docs/api/buffer.html | O problema é o algoritmo caseiro, não depreciação confirmada |
| sqlite3 5.1.7 | Database, run, get, all, serialize | https://github.com/TryGhost/node-sqlite3/wiki/API e /wiki/Control-Flow | Sequenciamento não é transação; não auditadas todas as dependências transitivas |
| Express4.22.1 | json, rotas, status/send/json | https://expressjs.com/en/4x/api/ | Cobertura documental parcial; não presume comportamento automático de Promises do Express5 |
| Node24.20.0 | crypto.scrypt (proposto) | https://nodejs.org/download/release/v24.20.0/docs/api/crypto.html | Usar salt aleatório, parâmetros e formato explícitos |

Context7 falhou por chave inválida; documentação oficial foi consultada por web. Não há prova de ausência universal de depreciações/vulnerabilidades. Nenhuma atualização de dependência foi proposta automaticamente.

## Proposta aprovada

Separar composição/entrada, configuração, banco/esquema, Models SQL, Controllers HTTP, rotas, apresentação, segurança, middleware de erros e serviço transacional de checkout. Não transferir toda a God Class para um Controller/Model. Ordem: baseline e regressões; MVC; acesso/senhas/logs; atomicidade/integridade; relatório/validação/erros; comparação e documentação.

Mudanças públicas aprovadas: token Bearer administrativo externo em ADMIN_API_TOKEN para relatório/exclusão (ausente/inválido401); senha obrigatória no checkout e verificação de email existente (incorreta401); entradas inválidas400; curso ausente/inativo404; falha interna500 sanitizada; exclusão vinculada409, ausente404, sem vínculo200. Checkout recusado400 sem resíduos. Preservar nomes usr/eml/pwd/c_id/card, resposta de sucesso msg/enrollment_id, campos do relatório, preços e simulador por prefixo4.

SQLite local não reverte cobrança/email: esta implementação só possui simulador. Não criar integrações reais, deploy, migração de dados reais ou push. Senhas legadas não podem ser recuperadas do verificador fraco; reset explícito fora da memória demo depende de política própria.

## Plano de validação aprovado

Original: npm start -> node src/app.js, porta fixa3000, seeds automáticos. Não iniciar esse arquivo para baseline; harness carrega AppManager/utils originais via git show+vm, cria o mesmo esquema com fixtures sintéticas e usa HTTP real em127.0.0.1/porta livre. Banco memory e conexão de inspeção pertencem à mesma instância; uma segunda conexão memory seria outro banco. Logs originais capturados só em memória e salvos apenas como flags sanitizadas.

Depois: factory sem boot ao importar, banco/adaptador simulados por instância, node --test tests/*.test.js, smoke de npm start/servidor, rollback com triggers SQLite reais e testes concorrentes. Verificar status, corpo, linhas/vínculos persistidos, ausência de segredos e número de consultas. Fechar servidores/conexões em finally; limpar somente artefatos temporários desta execução.

| Cenário | Original a observar | Depois esperado | Estado na aprovação |
|---|---|---|---|
| Checkout aprovado novo/existente |200 e gravações |200; hash/identidade, matrícula/pagamento/audit consistentes |Planejado|
| Checkout existente senha incorreta |senha ignorada |401, sem gravações |Planejado|
| Pagamento recusado |400; usuário antecipado |400, estado intacto |Planejado|
| Curso ausente/inativo |404 |404 sem gravações |Planejado|
| Entrada malformada |falha a reproduzir em isolamento |400 e processo disponível |Planejado|
| Falha em cada insert obrigatório |parcialidade/falso sucesso |500 com rollback e recuperação |Planejado|
| Concorrência |estado a registrar |transações isoladas, sem usuário duplicado |Planejado|
| Relatório |público; 1+C+2E consultas |admin; mesma receita/campos/vazios; acesso em conjunto |Planejado|
| Exclusão sem vínculo |200 |admin200 com remoção efetiva |Planejado|
| Exclusão vinculada |órfãos |409 e histórico preservado |Planejado|
| Exclusão ausente/inválida |sucesso genérico |404/400 |Planejado|
| Relatório/exclusão sem admin |permitidos |401 sem efeitos |Planejado|
| Falha de consulta/logs |erro mal traduzido/segredos |500 sanitizado/log mínimo |Planejado|

## Aprovação recebida

Após a apresentação do relatório, a proposta e o plano foram aprovados em resposta posterior. A aprovação cobre P2-01 a11, mudanças públicas, validação isolada e gravação deste relatório em reports/audit-project-2.md. Não se estende à issue011 nem a push.

## Complemento de execução

### Resultado observado

- Baseline executada após aprovação e antes das mudanças:9 cenários de HTTP real, três endpoints, SQLite em memória e fixture sintética. Relatório sem admin200, senha incorreta200, exclusão vinculada200 com órfãos, recusa criando usuário, falha no pagamento deixando matrícula e falha na auditoria respondendo200 foram reproduzidos. Valores secretos nunca salvos.
- Onze regressões inicialmente falharam como esperado:10 de API e1 de colisão/salt. Suite final38/38 passou, zero falhas/cancelamentos/skips. A correção de URI malformada também teve teste RED→GREEN.
- Coletor depois:11 cenários HTTP com status esperados, comparação de estado e encerramento. Relatório admin200, sem admin401; senha incorreta401; delete vinculado409; delete sem vínculo200 e ausente404; recusa/falhas mantêm estado anterior; logs sem cartão.
- Smoke em subprocesso real: boot com esquema/seed sintético pronto, relatório200/receita997, checkout200, delete vinculado409, logs sanitizados, SIGTERM/exit0 e processo encerrado.
- Consulta do relatório: teste antes cresceu7→31 SELECTs ao adicionar12 matrículas; depois manteve1→1 e receita Docker5964. Isso mede quantidade de chamadas, não latência nem plano interno do SQLite.
- Concorrência: checkout que falha não desfaz outro que confirma; mesmo email/senhas diferentes gera um usuário e200/401. Fila engloba leituras e escritas na mesma conexão; cache não é global.
- Modelos preservam valores/preços e projeção do relatório. Esquema novo em memória: referências restritas, email único e um pagamento por matrícula, coerentes com o fluxo. Não houve migração de dados reais.
- Revisão independente somente leitura: nenhum Critical/Important inicialmente; URIError400 transformado em500 foi apontado e reclassificado como correção necessária ao contrato de entradas inválidas. Reproduzido por HTTP, corrigido com mensagem fixa e suite38/38. Sem outros menores adiados.

### Antes/depois da estrutura e achados

Antes:3 arquivos próprios, AppManager e utils globais. Depois:19 módulos próprios (composição/entrada, config, banco, Models, Controllers, serviço, rotas, presenters, middleware e segurança); testes em pasta separada. app.js agora não abre servidor ao importar. npm start executa server.js. Demo precisa de opt-in e senha externa; boot sem demo cria esquema vazio. Isso torna explícita a preparação de dados aprovada.

| Achados | Estado nos cenários executados | Evidência |
|---|---|---|
| P2-01 |Resolvido no escopo|MVC com SQL nos Models e coordenação transacional em serviço; smoke integrado|
| P2-02 |Resolvido|logs/respostas sem valores sintéticos sensíveis|
| P2-03 |Resolvido|admin obrigatório; senha correta/incorreta;401 sem efeitos|
| P2-04 |Resolvido para novos dados/demo; legado real não migrado|scrypt/salt; formatos legados rejeitados|
| P2-05 |Resolvido|triggers em users/enrollments/payments/audit, rollback e concorrência|
| P2-10 |Resolvido|409 preservando registros; remoção sem vínculo; restrições referenciais|
| P2-06 |Resolvido quanto a consultas por elemento|relatório1 consulta em cardinalidades diferentes e conteúdo preservado|
| P2-07 |Resolvido nos caminhos exercitados|500 sanitizado, recuperação após falha, URI malformada400|
| P2-11 |Resolvido nos limites exercitados|tipos, nulos, ID, campos e ausência de gravações|
| P2-08 |Resolvido|nomes internos explícitos, campos públicos originais|
| P2-09 |Resolvido no escopo próprio|estado sem uso removido; relatório validado|

### Comandos e evidências

Diretório: ecommerce-api-legacy/. `node tests/baseline.js ../reports/evidence/project-2-http-before.json`; testes selecionados com BASELINE=1 para RED; `NPM_CONFIG_USERCONFIG=/dev/null npm test`; `node tests/after.js ../reports/evidence/project-2-http-after.json`; `node tests/process-smoke.js ../reports/evidence/project-2-process-smoke.json`; `git diff --check`.

O primeiro npm test emitiu aviso sobre configuração pessoal timeout e teve33/34: o teste tentava DROP TABLE courses, bloqueado corretamente por FK. A fixture foi ajustada para renomear a tabela, isolando falha de consulta sem violar FK. O coletor depois teve uma expectativa de ordem incorreta, corrigida antes de gravar evidência. Nenhuma dessas falhas foi omitida ou chamada de teste aprovado.

Arquivos: [antes](evidence/project-2-http-before.json), [depois](evidence/project-2-http-after.json), [smoke](evidence/project-2-process-smoke.json), [TAP](evidence/project-2-tests.tap), [resumo/hashes](evidence/project-2-validation.json). Base original e hashes no resumo permitem identificar as fontes verificadas. Processos e bancos de teste encerrados.

### Checklist oficial

- [x] Linguagem, framework, domínio e quantidade de arquivos detectados corretamente.
- [x] Relatório com template, linhas originais e achados ordenados; >=5, incluindo CRITICAL/HIGH;9/9 manuais.
- [x] Depreciações investigadas; nenhuma confirmada, cobertura parcial declarada.
- [x] Pausa após auditoria e aprovação posterior respeitadas; relatório só salvo depois.
- [x] Estrutura MVC, Models, Controllers, apresentação/rotas, configuração, erros e entrada distinguíveis.
- [x] Configuração operacional externa; removidos literais privados sem utilidade. Valores de domínio preservados.
- [x] Boot sem erro com configuração válida; três endpoints funcionando com mudanças aprovadas.
- [x] Evidências antes/depois, persistência e falhas registradas;38 testes e encerramento.

### Decisões e limites finais

- Branch própria no checkout pedido, sem novo worktree; custo: checkout fica na branch010. Nenhuma alteração inicial versionada foi sobrescrita.
- Demo somente por opt-in com senha externa; banco permanece memory. Custo: npm start sem demo não fornece cursos; é preciso habilitar a demonstração para usar api.http.
- Normalização de email/política de contas não redesenhadas: comparação exata preservada. Emails duplicados no novo esquema são impedidos para que a identidade seja unívoca; nenhum banco existente foi convertido.
- Reset de senhas legadas fica fora desta API sem login/reset: legado é rejeitado, não autenticado por algoritmo fraco. Custo: dados legados externos exigiriam processo próprio de reset.
- Pagamentos reais, idempotência e compensação externa não implementados: somente simulador sem rede. Custo: não usar como cobrança de produção.
- Persistência/migração, carga/DoS e política monetária além da existente não foram validadas. Token compartilhado não é gestão completa de usuários; scrypt usa parâmetros documentados no README, sem benchmark de carga. Banco/fila/cache em memória não constituem arquitetura de produção.
- Nenhuma alteração necessária na skill foi demonstrada: a mesma cópia orientou Node/Express, com findings fora do catálogo e sem transportar exemplos Flask. Generalização a outros projetos segue sem comprovação universal.
- Skill de execução exigiu uma revisão independente final; ela foi feita sem alterações no checkout. As demais atividades foram executadas nesta sessão.
- Sem push, deploy, cobrança/email real ou execução da issue011. Commit local da issue na branch refactor/issue-010-project-2; hash disponível no histórico que contém este relatório.
