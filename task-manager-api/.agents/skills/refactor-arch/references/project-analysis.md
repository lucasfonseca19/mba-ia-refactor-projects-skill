# Análise de projeto

Use na Fase 1 e em retomadas que exijam conferir o estado auditado. Descubra a tecnologia a partir de evidências convergentes, sem importar ou iniciar a aplicação nesta fase.

## Delimitar e inventariar

- Localize a raiz do projeto recebido e suas instruções. Em monorepos, identifique aplicação, bibliotecas compartilhadas e integrações pertinentes; não inclua aplicações vizinhas por acidente.
- Confira o estado de versionamento e diferenças locais. Registre revisão, quando disponível, e mudanças locais que afetem a auditoria. Não restaure nem descarte trabalho existente.
- Liste os arquivos-alvo com ferramentas de busca disponíveis, como `rg --files`. Inclua arquivos ocultos relevantes explicitamente. Exclua da contagem de código próprio dependências instaladas/vendorizadas, ambientes virtuais, artefatos gerados e builds; leia manifestos, configurações e migrações separadamente quando relevantes.
- Informe quantos arquivos de código foram efetivamente lidos, quantos existem no escopo e exclusões. Uma busca por palavras não significa leitura completa de cada arquivo encontrado. Se a cobertura for parcial, diga onde e por quê.

## Reconhecer a stack

| Evidência | O que investigar |
| --- | --- |
| Manifestos e lockfiles | Linguagem, bibliotecas diretas/transitivas, restrições e versões resolvidas; por exemplo, `pyproject.toml`, `requirements.txt`, `package.json`, `go.mod`, `pom.xml`, `Gemfile`, arquivos de projeto .NET ou equivalentes. |
| Imports e inicialização | Framework realmente usado, montagem da aplicação, módulos registrados e código executável em imports. Uma dependência no manifesto pode não participar dos fluxos auditados. |
| Configuração de runtime | Versão exigida/declarada, ambiente existente e compatibilidade; inspecione metadados locais quando disponíveis. Não execute scripts do projeto para descobrir versões. |
| Banco e armazenamento | Drivers/ORM, esquema/modelos, migrações, conexões, transações, arquivos e integrações. Não abra uma conexão que possa criar ou alterar o banco. |
| Documentação e automação | Comandos de boot, testes, containers, variáveis necessárias e exemplos de requisições. Comando documentado é uma pista, não prova de execução bem-sucedida. |

Registre separadamente versões declaradas, resolvidas e instaladas, com suas fontes. Não instale ferramentas para completar o inventário antes da aprovação. Não imprima valores secretos ao inspecionar configuração.

## Mapear responsabilidades reais

Escolha fluxos de leitura, escrita e operação sensível e rastreie:

1. Entrada: rota, comando, evento ou equivalente e sua autenticação/validação.
2. Coordenação: quem escolhe e encadeia as operações.
3. Regra: onde são tomadas decisões do domínio.
4. Dados: quem consulta/persiste e delimita a transação.
5. Saída: serialização, View, status/erro e possíveis logs.

Anote dependências, estado compartilhado, efeitos de inicialização e chamadas externas. Diferencie organização nominal de separação real: uma pasta `controllers` pode conter SQL e regras, e um projeto sem essa pasta pode já separar responsabilidades adequadamente.

Se MVC não tiver aplicação clara ao tipo de software recebido, apresente a incompatibilidade e uma proposta fundamentada antes de reestruturar. Não simule Views/Routes vazias para tornar uma biblioteca ou um worker aparentemente conforme.

## Descobrir a validação sem executar preparação

Inventarie endpoints por método/caminho e localização do registro, incluindo prefixos e montagem dinâmica. Cruze rotas, especificações, testes e exemplos; marque lacunas. Para interfaces sem HTTP, identifique os contratos equivalentes.

Descubra comandos, configuração mínima, porta, banco de teste, seed/fixtures, testes existentes e dependências externas. Leia scripts antes de propô-los: até um teste ou import pode criar arquivos, semear banco ou enviar mensagens.

Concretize na auditoria:

- Diretório de execução, runtime e comando de boot, variáveis necessárias sem valores secretos e critério observável de prontidão.
- Ambiente temporário e dados sintéticos; forma de apontar aplicação e testes para ele, inclusive bancos inicializados por caminhos fixos ou no import.
- Mocks/adaptadores de teste ou sandbox para integrações; pendência explícita se não houver isolamento viável.
- Cenário principal para cada endpoint/interface, método, entrada, pré-condições, identidade/permissão, status e conteúdo esperados e efeito persistido. Inclua cenários negativos afetados pelas correções.
- Verificação antes/depois, distinguindo falhas originais e comportamentos que precisam mudar. Reutilize mecanismos adequados, sem impor biblioteca de testes universal.
- Como encerrar processos e limpar apenas artefatos temporários criados pela validação, mantendo evidências úteis e trabalho anterior.

## Comprovar o isolamento antes da execução

Use esta barreira na Fase 3 antes de importar, iniciar ou executar testes, seeds e outros comandos que possam gravar dados ou acessar integrações. Adapte a técnica à stack e ao ambiente, sem presumir que configurar uma variável redirecione a aplicação.

1. **Identifique efeitos antes de executar.** Leia o ponto de entrada, imports, configuração, resolução de módulos, caminhos relativos, scripts e fixtures. Relacione cada recurso potencialmente afetado ao processo e descubra se ele pode ser acessado já no import. Uma verificação dentro de um teste após o import não protege seus efeitos de inicialização.
2. **Imponha uma fronteira verificável antes de qualquer efeito.** Prefira um ambiente descartável com código e dados sintéticos, isolado dos dados reais e com acesso externo bloqueado ou substituído quando aplicável. Confira a origem real do código que será carregado, incluindo diretório, caminhos de busca, links simbólicos e arquivos copiados. Um diretório temporário ou uma variável de ambiente, sozinhos, não demonstram confinamento: confirme que a configuração é lida e que caminhos absolutos, mounts, credenciais e serviços não apontam para recursos reais. Se a aplicação ignora a configuração, use uma barreira externa verificável ou uma cópia com caminhos comprovadamente confinados; sem isso, pare.
3. **Comprove o destino efetivo sem criar o risco que pretende evitar.** Para recursos acessados no import, prove antes do import, pela resolução de código/configuração e pela fronteira imposta, que qualquer destino possível está isolado. Quando a aplicação permitir configuração antes da conexão, confira o destino efetivo nessa etapa, antes de iniciar transações ou executar operações destrutivas. Se for necessário observar uma conexão já iniciada, faça isso apenas dentro da fronteira externa previamente comprovada. Compare identificadores e caminhos normalizados sem revelar credenciais. Confirme cada recurso de escrita e integração relevante, não apenas o banco principal.
4. **Falhe fechado e registre evidências.** Faça verificações bloqueantes antes de apagar, semear, migrar ou alterar dados: origem do código, fronteira, destinos resolvidos e condição que impede acesso ao original. Exercite, quando possível de modo seguro, casos negativos em que a configuração é ignorada, a origem do código é inesperada ou o destino está fora do limite; a execução deve parar antes de efeitos fora do isolamento. Se a prova falhar ou estiver incompleta, não prossiga com a operação dependente; explique o bloqueio e proponha outra estratégia. Preserve dados e artefatos anteriores.
5. **Mantenha o isolamento durante toda a validação.** Verifique novamente após mudança de configuração, caminho, processo, ambiente ou comando que possa mudar a resolução. Use dados sintéticos, controle integrações, encerre processos e remova apenas artefatos temporários criados para a validação. Registre o que foi comprovado, o método e os limites; não apresente uma instrução textual como garantia absoluta.

## Resumo da Fase 1

Informe raiz/escopo, revisão e mudanças locais pertinentes, linguagem/runtime/framework/versões com fontes, dependências relevantes, domínio, persistência, arquitetura e fluxos mapeados. Inclua arquivos analisados, exclusões, interfaces inventariadas, meios de validação descobertos e incertezas. Separe fatos, inferências e pendências; não prometa cobertura universal a partir dessa leitura.
