# Template de relatório de auditoria

Use na Fase 2. Preencha com evidências; campos entre chaves abaixo são marcadores do template, não resultados. Não preencha verificações futuras como executadas. Mostre o relatório na conversa antes da aprovação; só grave um arquivo na Fase 3, se aprovado, no destino acordado.

## Identificação e escopo

- Projeto/raiz: {alvo auditado}
- Data e revisão: {data, commit quando disponível e mudanças locais relevantes}
- Stack e versões: {declaradas/resolvidas/instaladas e fontes}
- Domínio e persistência: {responsabilidade da aplicação e armazenamento}
- Arquitetura atual: {fluxos e responsabilidades observados}
- Cobertura: {arquivos de código efetivamente analisados / total no escopo, exclusões e limites}
- Interfaces originais: {inventário ou tabela nesta seção, incluindo método/caminho e origem}

## Resumo

| Severidade | Quantidade |
| --- | --- |
| CRITICAL | {contagem} |
| HIGH | {contagem} |
| MEDIUM | {contagem} |
| LOW | {contagem} |

Total: {soma dos achados confirmados}. Candidatos sem confirmação ficam nas pendências e não inflam a contagem. Zero é um resultado válido quando sustentado; não fabrique achados para atender a uma cota.

## Achados

Ordene por severidade e, dentro dela, impacto. Repita este formato por achado, mantendo o ID entre revisões:

### {F-001} · {SEVERIDADE} · {título que descreve o mecanismo}

- **Padrão:** {AP-xx ou padrão adicional fundamentado; relacionados, se houver}
- **Localização:** {caminho relativo:linha inicial-linha final; locais adicionais necessários ao fluxo}
- **Evidência:** {trecho mínimo sem segredos e caminho entre origem, operação e efeito}
- **Método e limite:** {inspeção estática ou reprodução autorizada; o que não foi demonstrado}
- **Impacto e severidade:** {consequência contextual e motivo da classificação}
- **Correção proposta:** {transformação T-xx ou equivalente adaptado à stack}
- **Mudança observável:** {contrato/dados/permissão que muda, ou preservação esperada}
- **Verificação proposta:** {entrada, condição e resultado observável que confirmarão a correção}
- **Dependências/incertezas:** {pré-condições, dados a migrar ou pontos a decidir}

As linhas referem-se à revisão auditada, não à posição posterior à refatoração. Registre relações sem duplicar causa/impacto para aumentar o total.

## APIs deprecated e cobertura documental

| Biblioteca e versão/fonte | Símbolo e usos | Situação e substituto | Evidência oficial e data | Impactos e limites |
| --- | --- | --- | --- | --- |
| {biblioteca; versão resolvida/instalada} | {símbolo; caminhos/linhas} | {confirmado, candidato ou não aplicável; alternativa} | {URL/seção/data} | {semântica, compatibilidade e lacunas} |

Se não houver evidência suficiente ou acesso à fonte, diga isso. Ausência de candidatos encontrados não equivale a confirmação de que nenhuma API deprecated existe.

## Proposta de refatoração

- Estrutura antes/depois proposta e responsabilidades MVC; aproveitamento de abstrações existentes.
- Ordem de implementação e relação entre etapas e IDs dos achados.
- Áreas/arquivos afetados, configuração necessária e dependências a alterar, com justificativa.
- Mudanças de comportamento necessárias: atual → esperado, motivo, clientes/dados afetados e estratégia de migração quando pertinente.
- Exclusões de escopo e decisões ainda necessárias.

## Plano de validação antes/depois

Descreva diretório/comandos exatos de preparação, boot e verificação descobertos no projeto, ambiente e dados isolados, integrações substituídas/sandbox, critério de prontidão e encerramento dos processos. Dependências ainda não resolvidas devem ter estado bloqueado e ação necessária; não invente comandos nem valores secretos.

| Endpoint/interface | Pré-condição e entrada | Resultado original a observar | Resultado esperado após correção | Como verificar resposta e efeito | Estado |
| --- | --- | --- | --- | --- | --- |
| {método/caminho ou interface} | {dados sintéticos e identidade} | {contrato documentado/inferido; falhas a confirmar} | {preservado ou mudança aprovada} | {teste/requisição/consulta isolada} | {planejado ou bloqueado} |

Inclua cenário principal de **cada** endpoint original e casos de erro/permissão afetados. Separe cenário planejado de executado. Após aprovação, registre evidência antes/depois, persistência, falhas pré-existentes e regressões.

## Pendências e aprovação

- Achados candidatos e limites da auditoria: {itens e evidência que falta}.
- Bloqueios: {o que não pode ser executado e o que precisa ser resolvido}.
- Destino proposto do relatório, se necessário: {caminho acordável; não gravado ainda}.
- Escopo para aprovação: {correções por ID, mudanças de contrato, preparação/validação e arquivos de evidência}.

Finalize com um pedido explícito, por exemplo: **“Você aprova a Fase 3 com as correções, mudanças de comportamento e plano de validação acima?”** Encerre o turno e aguarde a resposta. Silêncio ou invocação inicial não são aprovação.

## Complemento após a Fase 3

Acrescente sem reescrever o diagnóstico original: aprovação recebida, estrutura implementada, mudanças de comportamento e configuração, comandos executados e resultados antes/depois, evidências por cenário, processos encerrados, estado de cada achado (resolvido/parcial/pendente/não verificado) e riscos restantes. Mantenha os IDs e a distinção entre plano e execução. Se o relatório for somente de auditoria, este complemento não é obrigatório.
