# Issues locais

Este arquivo controla o trabalho e a retomada entre sessões. O enunciado oficial está em [ENUNCIADO.md](ENUNCIADO.md). As etapas abaixo organizam os requisitos; não representam aprovação das escolhas técnicas nem autorização para executar tudo de uma vez.

## Como usar

- Estados: `aberta`, `em andamento`, `aguardando decisão`, `bloqueada`, `concluída`.
- Manter os IDs estáveis e trabalhar uma etapa por vez.
- Antes de iniciar uma issue, explicar o objetivo e as decisões relevantes para Lucas.
- Registrar as escolhas de Lucas, seus motivos e as evidências no item correspondente.
- Encerrar uma issue apenas quando seus critérios estiverem atendidos. Registrar limitações reais.
- Ao terminar uma sessão, atualizar a seção de retomada e o item em andamento.
- Se o volume crescer, podemos decidir juntos migrar para um arquivo por issue.

## Retomada

Atualizado em: 27/10/2026.

- Pedido de Lucas: construir a entrega juntos, aprendendo as principais decisões ao longo do processo. Escolhas abertas devem ser apresentadas com sugestões; a decisão final é dele.
- Concluído: leitura do enunciado no Chrome autenticado e extração estruturada para `ENUNCIADO.md`.
- Controle inicial: este Markdown, sem dependências ou serviço externo. Formato ajustável conforme a preferência de Lucas.
- Estado do projeto: fork público criado e os três projetos originais disponíveis nesta mesma pasta local. Código das APIs preservado sem alterações.
- Fork e remote `origin`: `https://github.com/lucasfonseca19/mba-ia-refactor-projects-skill`.
- Base e remote `upstream`: `https://github.com/devfullcycle/mba-ia-refactor-projects-skill`.
- Repositório inicial preservado no remote `initial-origin`; seu commit inicial permanece na branch local `initial-project`. O stash identificado por `backup: local MBA documents before adopting fork history` preserva os documentos anteriores à migração.
- Revisão original adotada: `6d1ce6248c3e956801010a89d8bdaab48029bf30`.
- Ferramenta escolhida por Lucas: Codex. A convenção atual de skills ainda será conferida na documentação oficial.
- Próximo passo: concluir a verificação da convenção de skills do Codex (002) e preparar/verificar os ambientes das APIs (003), antes da análise manual guiada.
- Ainda não realizado: instalação de dependências, boot e validação inicial das APIs, criação da skill, análise manual, refatoração ou envio na plataforma.
- O README da base foi preservado com uma nota de acompanhamento. Há diferenças entre ele e a plataforma, especialmente na seção de ferramentas; `ENUNCIADO.md` registra o texto extraído da plataforma. Codex é aceito em ambos.

## 001 · Extrair e organizar o enunciado

**Estado:** concluída.

**Objetivo:** manter uma cópia local consultável de todos os requisitos.

**Critérios:**

- [x] Ler o desafio na aba autenticada indicada por Lucas.
- [x] Salvar o enunciado na raiz com fonte e data.
- [x] Preservar exemplos, checklists, referências e instrução de entrega.

**Evidência:** [ENUNCIADO.md](ENUNCIADO.md).

## 002 · Escolher a ferramenta-alvo da skill

**Estado:** em andamento.

**Objetivo:** decidir em qual ferramenta criar, invocar e testar `refactor-arch`.

**Contexto:** o curso aceita Claude Code, Gemini CLI, OpenAI Codex ou equivalente. O nome `refactor-arch`, o `SKILL.md` e as cinco áreas de referência são obrigatórios; diretório e invocação dependem da ferramenta.

**Sugestão inicial do assistente:** usar Codex para manter continuidade com o ambiente desta conversa. Alternativa: Claude Code para acompanhar os exemplos do curso. Esta é uma sugestão de fluxo, sem comparação de qualidade ou custo entre ferramentas.

**Critérios:**

- [x] Lucas escolher a ferramenta.
- [ ] Consultar a documentação oficial atual para confirmar diretório, formato e invocação.
- [x] Registrar a decisão e a justificativa aqui.

**Decisão de Lucas:** Codex, confirmado em 27/10/2026 após a sugestão de continuidade com o ambiente atual. Sem escolha de modelo ou configuração adicional neste momento.

## 003 · Preparar o repositório base e o ambiente

**Estado:** em andamento. **Depende de:** 002 para configurar a ferramenta.

**Objetivo:** atender ao requisito de fork e disponibilizar os três projetos preservando a referência original.

**Critérios:**

- [x] Verificar a relação do repositório atual com `devfullcycle/mba-ia-refactor-projects-skill`.
- [x] Apresentar a Lucas uma proposta para o fork e para o checkout atual e registrar sua escolha.
- [x] Disponibilizar os três projetos e registrar a revisão original usada como referência.
- [x] Ler instruções existentes e registrar os comandos declarados para cada API.
- [ ] Preparar os ambientes e verificar a execução inicial das APIs, registrando evidências e versões usadas.

**Verificação:** `gh repo view` confirmou que `lucasfonseca19/skill-auditoria-refatoracao` não é fork; ambos os repositórios usam `main`. O checkout atual tem um commit inicial e documentos locais ainda não commitados.

**Decisão de Lucas:** usar o nome original da base no fork, confirmado em 27/10/2026. Preservar o repositório inicial e reaproveitar a pasta local.

**Resultado verificado:** GitHub confirma `isFork: true`, visibilidade pública e parent `devfullcycle/mba-ia-refactor-projects-skill`. A branch local `main` acompanha `origin/main` e parte da revisão original registrada na retomada. Os três diretórios de APIs estão presentes e não foram modificados. Nossos documentos foram restaurados; o README da base foi preservado após uma nota inicial.

**Comandos declarados pelos READMEs da base (ainda não executados):**

- Projeto 1: Python; `pip install -r requirements.txt` e `python app.py` dentro de `code-smells-project/`. Flask 3.1.1 e flask-cors 5.0.1. Porta 5000; README informa criação automática do SQLite e seeds.
- Projeto 2: Node.js/npm; `npm install` e `npm start` dentro de `ecommerce-api-legacy/`. Express e sqlite3. Porta 3000; README informa SQLite em memória com seeds. Há exemplos em `api.http`.
- Projeto 3: Python; `pip install -r requirements.txt`, `python seed.py` e `python app.py` dentro de `task-manager-api/`. Flask 3.0.0, Flask-SQLAlchemy e outras dependências listadas no requirements. Porta 5000; README exige seed antes do primeiro boot.

**Cuidados para a próxima etapa:** usar ambientes virtuais separados para os projetos Python, pois fixam versões diferentes de Flask. Como os dois usam a porta 5000, executá-los em momentos distintos ou discutir mudança de porta antes. Os READMEs não fixam as versões de Python e Node; a compatibilidade ainda precisa ser verificada. Estas são observações de preparação, sem instalações ou mudanças de comportamento nesta etapa.

## 004 · Analisar manualmente code-smells-project

**Estado:** aberta. **Depende de:** 003.

**Objetivo:** estudar a API de E-commerce Python/Flask antes de criar a skill.

**Critérios:**

- [ ] Ler o código com Lucas e explicar os problemas encontrados.
- [ ] Documentar no README pelo menos 5 problemas: 1 CRITICAL ou HIGH, 2 MEDIUM e 2 LOW.
- [ ] Registrar evidência no código, classificação e justificativa de relevância.

## 005 · Analisar manualmente ecommerce-api-legacy

**Estado:** aberta. **Depende de:** 003.

**Objetivo:** estudar a LMS API Node.js/Express com checkout.

**Critérios:** mesmos mínimos da issue 004, aplicados a este projeto e documentados separadamente no README.

## 006 · Analisar manualmente task-manager-api

**Estado:** aberta. **Depende de:** 003.

**Objetivo:** estudar a API Python/Flask com organização parcial, distinguindo estrutura aparente de responsabilidades adequadas.

**Critérios:** mesmos mínimos da issue 004, aplicados a este projeto e documentados separadamente no README.

## 007 · Decidir o desenho da skill

**Estado:** aberta. **Depende de:** 002, 004, 005 e 006.

**Objetivo:** usar a análise manual como insumo e decidir com Lucas a organização da skill, o MVC alvo e a validação.

**Critérios:**

- [ ] Explicar alternativas e seus impactos antes de implementar.
- [ ] Registrar a organização escolhida para as três fases e as cinco áreas de conhecimento.
- [ ] Definir como preservar comportamento, tratar APIs obsoletas e validar boot e endpoints.
- [ ] Obter a decisão de Lucas sobre as escolhas abertas.

## 008 · Criar refactor-arch e referências

**Estado:** aberta. **Depende de:** 007.

**Critérios:**

- [ ] Criar `SKILL.md` no projeto 1 conforme a convenção da ferramenta escolhida.
- [ ] Implementar as três fases sequenciais, com pausa para aprovação ao final da auditoria e antes de alterar arquivos.
- [ ] Cobrir análise de projeto, catálogo, template de relatório, guidelines MVC e playbook.
- [ ] Incluir pelo menos 8 anti-patterns, cobrindo todas as severidades e detecção de APIs deprecated.
- [ ] Incluir pelo menos 8 transformações com exemplos antes/depois.
- [ ] Evitar regras acopladas aos nomes ou achados específicos de um único projeto.

## 009 · Executar e validar no projeto 1

**Estado:** aberta. **Depende de:** 008.

**Critérios:**

- [ ] Detectar corretamente a stack e encontrar pelo menos 5 problemas da análise manual, incluindo 1 CRITICAL ou HIGH.
- [ ] Salvar a auditoria em `reports/audit-project-1.md` na raiz.
- [ ] Revisar o relatório com Lucas e obter aprovação antes da refatoração.
- [ ] Executar a refatoração e preencher todo o checklist oficial do enunciado.
- [ ] Registrar evidências de boot e funcionamento dos endpoints originais, além da estrutura antes/depois.
- [ ] Commitar o resultado conforme exigido pela entrega.

## 010 · Executar e validar no projeto 2

**Estado:** aberta. **Depende de:** 009.

**Critérios:**

- [ ] Copiar a skill para o projeto 2 e executar as três fases em Node.js/Express.
- [ ] Detectar a stack corretamente e gerar no mínimo 5 findings, incluindo 1 CRITICAL ou HIGH.
- [ ] Salvar `reports/audit-project-2.md` na raiz.
- [ ] Revisar com Lucas e obter aprovação antes da refatoração.
- [ ] Preencher o checklist oficial e guardar evidências de boot, endpoints e estrutura antes/depois.
- [ ] Commitar o resultado.

## 011 · Executar e validar no projeto 3

**Estado:** aberta. **Depende de:** 010.

**Critérios:**

- [ ] Copiar a skill para o projeto 3, detectar Python/Flask e o domínio Task Manager.
- [ ] Gerar no mínimo 5 findings, incluindo 1 CRITICAL ou HIGH, mesmo com organização parcial.
- [ ] Salvar `reports/audit-project-3.md` na raiz.
- [ ] Revisar com Lucas e obter aprovação antes da refatoração.
- [ ] Preencher o checklist oficial e guardar evidências de boot, endpoints e estrutura antes/depois.
- [ ] Commitar o resultado.

## 012 · Consolidar documentação e revisar a entrega

**Estado:** aberta. **Depende de:** 009, 010 e 011.

**Critérios:**

- [ ] README com Análise Manual, Construção da Skill, Resultados e Como Executar.
- [ ] Registrar decisões, desafios, contagens por severidade e comportamento nas diferentes stacks.
- [ ] Confirmar os quatro critérios de aceite nos três projetos e a presença dos três relatórios.
- [ ] Confirmar skill e referências em cada projeto, código refatorado commitado e evidências de execução.
- [ ] Verificar o requisito de repositório público e fork da base.
- [ ] Entregar a Lucas a URL e o checklist final para revisão e envio na plataforma.

**Limite:** preparar a entrega não equivale a enviar o formulário do curso; o envio precisa ser solicitado por Lucas.
