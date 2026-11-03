---
name: refactor-arch
description: Analisa e audita a arquitetura de projetos de software e conduz sua refatoração para MVC, adaptando-se à linguagem e ao framework. Use para auditorias arquiteturais ou refatorações para MVC, com relatório por severidade e aprovação antes de alterações.
---

# Refactor Arch

Conduza três fases sequenciais: análise, auditoria e refatoração validada. Adapte a detecção e a implementação à stack encontrada; nomes de pastas e exemplos não definem conformidade arquitetural. O catálogo é um ponto de partida, não uma lista fechada nem uma cota de achados.

## Limite de autorização

Até a aprovação do relatório da Fase 2, opere somente em leitura: não crie nem altere arquivos, incluindo relatório, cache, testes, configurações, dependências e lockfiles. Não execute boot, seed, migrações, instalações ou testes que possam escrever arquivos, alterar dados ou chamar serviços externos. Inspecione os mecanismos disponíveis para planejar sua execução posterior.

Apresente a auditoria na conversa e encerre o turno com um pedido explícito de aprovação do escopo concreto. Um pedido inicial como “refatore tudo” não substitui essa aprovação posterior. Se o usuário pedir só análise/auditoria, entregue-a e aguarde; não interprete a invocação da skill como autorização de refatoração.

Após aprovação, execute apenas o escopo aceito. Uma nova mudança relevante de contrato, permissão, dados ou dependências fora dele precisa ser apresentada para decisão antes da parte dependente. Não inclua deploy, push ou outras ações externas sem autorização correspondente.

## Fase 1 · Análise do projeto

Leia [análise de projeto](references/project-analysis.md). Delimite o projeto-alvo, leia suas orientações locais e registre o estado atual do trabalho, preservando mudanças existentes.

Identifique linguagem, runtime, framework e versões, dependências, persistência, domínio, pontos de entrada e arquitetura real. Rastreie fluxos representativos entre entrada, regra, dados e saída, inclusive em projetos parcialmente organizados.

Descubra os meios de boot e validação e inventarie endpoints/interfaces originais. Imprima um resumo com evidências, quantidade e escopo dos arquivos de código analisados, exclusões e lacunas. Não confunda versão declarada com instalada. Se o alvo estiver ambíguo, resolva a ambiguidade antes de auditá-lo.

## Fase 2 · Auditoria e proposta

Leia o [catálogo](references/anti-patterns.md) e o [template de relatório](references/audit-report.md). Consulte as [guidelines MVC](references/mvc-guidelines.md) para avaliar responsabilidades e o [playbook](references/refactoring-playbook.md) para fundamentar correções propostas.

- Investigue sinais no código-alvo e acompanhe os fluxos relevantes. Confirme contexto e falsos positivos; registre outros padrões encontrados, mesmo fora do catálogo.
- Para cada achado, forneça ID estável, severidade justificada, caminho relativo e linhas exatas na revisão auditada, evidência sem segredos, impacto, correção e verificação proposta. Não reproduza valores de credenciais. Separe evidência estática de falha reproduzida.
- Ordene por CRITICAL → HIGH → MEDIUM → LOW. Evite contar a mesma causa e impacto repetidamente; referencie achados relacionados. Não invente problemas para alcançar mínimos de uma entrega.
- Confirme depreciações por biblioteca, versão e fonte oficial conforme o catálogo. Sem confirmação, registre candidato/pendência e limite de cobertura.
- Explicite a estrutura MVC proposta, etapas, arquivos/áreas afetados e mudanças necessárias no comportamento público, com motivo e resultado esperado. Preserve endpoints originais e funcionalidades legítimas; resolva conflitos antes de propor remoções.
- Apresente um plano executável de validação antes/depois, com comandos descobertos, isolamento de dados e integrações, entradas, resultados esperados e cobertura dos endpoints. Declare o que está bloqueado e qual ação depende de resolver o bloqueio.

Produza o relatório completo na conversa seguindo o template. Peça aprovação da proposta e do plano de validação, incluindo eventuais mudanças de contrato e o destino do relatório. **Pare aqui. Não inicie a Fase 3 no mesmo turno sem uma resposta posterior de aprovação.** Em uma retomada, confira se o relatório aprovado ainda corresponde ao estado do projeto antes de aplicá-lo.

## Fase 3 · Refatoração e validação

Somente após aprovação, use as [guidelines MVC](references/mvc-guidelines.md) e as transformações pertinentes do [playbook](references/refactoring-playbook.md).

1. Registre o escopo aprovado. Salve o relatório no destino acordado, se houver, preservando a revisão e a numeração de linhas originais da auditoria.
2. Prepare e comprove o isolamento antes de executar qualquer import, boot, seed, teste ou comando com possíveis efeitos. Siga a barreira de isolamento em [análise de projeto](references/project-analysis.md#comprovar-o-isolamento-antes-da-execução). Uma variável definida ou o diretório de execução, isoladamente, não comprovam o destino efetivo. Se não for possível demonstrar o isolamento, pare a parte dependente. Só depois verifique o comportamento original com dados sintéticos; registre falhas pré-existentes. Não acione cobrança, envio real de mensagens ou outros efeitos externos sem autorização específica e condições de teste adequadas.
3. Refatore em incrementos coerentes. Aproveite separações existentes adequadas; mantenha regras/persistência fora de Controllers sobrecarregados. Extraia configuração, centralize erros e mantenha entrada clara. Implemente as correções aprovadas sem redesenhar funcionalidades não relacionadas.
4. Reaproveite verificações adequadas e acrescente as necessárias às correções. Repita o plano após as mudanças: boot, cenário principal de cada endpoint original, respostas, persistência, erros e permissões afetados. Uma resposta HTTP de sucesso isolada não comprova a operação.
5. Investigue falhas pelo erro observado. Se faltar isolamento, dependência ou definição essencial, pare a parte dependente e informe o bloqueio. Não transforme tentativas repetidas sem evidência em validação.
6. Reavalie os achados e caminhos alterados. Registre resolvidos, parciais, pendentes e não verificados, com evidências e riscos restantes; não declare “zero anti-patterns” sem sustentação.
7. Encerre os processos de teste iniciados e apresente estrutura antes/depois, mudanças de comportamento, comandos/resultados e limitações. Não declare validação completa se algum cenário necessário não tiver sido executado.

O resultado é a refatoração aprovada com evidência de funcionamento nos cenários executados. Tecnologia não testada e cobertura não realizada continuam não verificadas.
