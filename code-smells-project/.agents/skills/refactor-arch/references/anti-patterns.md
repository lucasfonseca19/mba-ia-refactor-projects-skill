# Catálogo de anti-patterns

Use na Fase 2. Os sinais orientam investigação; nenhum resultado de busca comprova um achado sozinho. Rastreie fluxo, contexto e proteções antes de classificar. Amplie a investigação para mecanismos não listados, fundamentando-os com o mesmo padrão de evidência. Não limite a análise a tecnologias, entidades ou nomes dos exemplos.

## Escala de severidade

| Severidade | Critério |
| --- | --- |
| CRITICAL | Falha grave de segurança/arquitetura que impede funcionamento correto, expõe dados sensíveis ou viola completamente a separação de responsabilidades, como uma God Class que reúne infraestrutura, regras e entrada. |
| HIGH | Forte violação de MVC/SOLID que dificulta muito manutenção e testes, acoplamento/estado mutável inadequado ou falha relevante de integridade/proteção. |
| MEDIUM | Duplicação, padronização, validação ou gargalo moderado de performance. |
| LOW | Problema localizado de legibilidade, nomenclatura ou valores sem significado explícito. |

As severidades de referência abaixo pressupõem o impacto descrito. Ajustes exigem justificativa contextual; não rebaixe exposição grave como mera organização, nem eleve um arquivo grande automaticamente a CRITICAL. Evidência estática suficiente pode fundamentar o risco sem exploração; não alegue reprodução que não ocorreu.

## AP-01 · Injeção em consultas

- **Referência:** CRITICAL quando entrada não confiável pode alterar instruções ou condições executadas no banco.
- **Sinais:** concatenação/interpolação em SQL bruto; caminhos de busca, filtro ou autenticação que levam dados externos à execução de comandos.
- **Confirme:** origem controlável, composição do comando, execução e mecanismo de binding/escape do driver. Identificadores dinâmicos precisam de estratégia própria, como allowlist.
- **Evite falso positivo:** expressão de ORM ou placeholder com parâmetros separados não equivale a SQL bruto concatenado; confira a API usada.
- **Correção/verificação:** [T-01](refactoring-playbook.md#t-01); preservar entradas legítimas e tratar payload semelhante a comando como dado, sem acesso adicional.

## AP-02 · Exposição de dados sensíveis

- **Referência:** CRITICAL quando credenciais ou dados sensíveis alcançam uma saída indevida.
- **Sinais:** serialização integral de entidades, respostas com verificadores de senha, logs de corpos completos ou erros com configuração privada.
- **Confirme:** dado, necessidade de exposição, destino e quem pode acessá-lo; não imprima seu valor para comprovar o risco.
- **Evite falso positivo:** metadado público não é segredo por ter nome sugestivo; hash de senha continua sendo dado sensível. Não afirme validade de uma chave de exemplo sem evidência.
- **Correção/verificação:** [T-02](refactoring-playbook.md#t-02); projeção explícita de saída e logs mínimos, verificando ausência de campos sensíveis e presença dos campos legítimos.

## AP-03 · Armazenamento inadequado de senhas

- **Referência:** HIGH para proteção inadequada de credenciais; CRITICAL quando há exposição direta adicional comprovada. Relacione AP-02 sem duplicar o mesmo impacto.
- **Sinais:** texto puro, transformação reversível, hash rápido sem estratégia própria para senhas ou função caseira que descarta conteúdo.
- **Confirme:** caminho de gravação e verificação, algoritmo, parâmetros e estratégia de salt/custo. Diferencie checksum/token aleatório de senha de usuário.
- **Evite falso positivo:** o nome `hash` não demonstra proteção; o uso correto de um hasher reconhecido também não comprova a migração de registros antigos.
- **Correção/verificação:** [T-03](refactoring-playbook.md#t-03); hasher próprio da stack e migração/reset acordado. Verificar senha válida, inválida e registros legados conforme o plano.

## AP-04 · Controle de acesso ausente ou insuficiente

- **Referência:** CRITICAL em operações administrativas/destrutivas ou acesso indevido a dados sensíveis; classificar outros casos pelo impacto.
- **Sinais:** rota sensível sem autenticação/autorização, identidade/role aceito do corpo da requisição, acesso a recurso apenas por ID, login sem credencial verificável usada pelas operações.
- **Confirme:** cadeia de middlewares/decorators, identidade confiável, política por ação/recurso e proteções externas conhecidas. Registrar o que não foi verificado fora da aplicação.
- **Evite falso positivo:** endpoint público legítimo não precisa de proteção inventada. Autenticação bem-sucedida não comprova autorização sobre qualquer recurso.
- **Correção/verificação:** [T-04](refactoring-playbook.md#t-04); permitir acesso autorizado e negar ausência de identidade, permissão ou vínculo previstos.

## AP-05 · Concentração indevida de responsabilidades

- **Referência:** HIGH para handlers/Controllers fortemente acoplados a regras e persistência; CRITICAL para God Class com violação completa de responsabilidades conforme a escala.
- **Sinais:** mesma unidade registra entrada, gerencia banco, decide regras de vários fluxos e formata saídas; mudanças locais exigem alterar dependências sem relação.
- **Confirme:** responsabilidades reais e razões de mudança; rastreie dependências. Verifique também camadas já existentes e abstrações que merecem reaproveitamento.
- **Evite falso positivo:** tamanho, nome de pasta ou quantidade de métodos não bastam. Um módulo coeso pequeno não precisa de camadas de repasse.
- **Correção/verificação:** [T-05](refactoring-playbook.md#t-05) e [guidelines](mvc-guidelines.md); testar regra sem HTTP e manter fluxo integrado funcional.

## AP-06 · Estado global mutável compartilhado

- **Referência:** HIGH quando estado compartilhado cria dependências implícitas e dificulta isolamento de operações/testes.
- **Sinais:** conexão/transação global, dados de requisição armazenados em singleton ou coleção mutável sem ciclo de vida claro.
- **Confirme:** quem modifica, duração, concorrência, reset e limites transacionais. Procure o ciclo de vida nativo do framework antes de substituí-lo.
- **Evite falso positivo:** configuração imutável, pool gerenciado ou sessão com escopo correto não equivalem a uma conexão global inadequada. Não alegue corrida/corrupção sem demonstração.
- **Correção/verificação:** [T-06](refactoring-playbook.md#t-06); recurso por escopo adequado, fechamento garantido e isolamento entre operações.

## AP-07 · Operações relacionadas sem garantia de consistência

- **Referência:** HIGH quando falha parcial compromete a integridade do fluxo; graduar conforme consequência.
- **Sinais:** gravações dependentes com commits separados, sucesso parcial sem compensação, efeitos externos tratados como se uma transação local os revertesse.
- **Confirme:** invariante do negócio, fronteira transacional e comportamento em falhas intermediárias/retries. Considere transações existentes e atomicidade do armazenamento.
- **Evite falso positivo:** operações independentes não exigem transação conjunta. Uma transação SQL não desfaz email nem cobrança externa.
- **Correção/verificação:** [T-07](refactoring-playbook.md#t-07); transação local ou coordenação/compensação apropriada, com falha injetada apenas em ambiente isolado.

## AP-08 · Consultas por elemento (N+1)

- **Referência:** MEDIUM para crescimento moderado de acessos com a coleção retornada.
- **Sinais:** consultas dentro de loops, lazy loading repetido e contagens por entidade em relatórios/listagens.
- **Confirme:** chamadas efetivas ao armazenamento, relação entre cardinalidade e acessos, cache e paginação. Diferencie contagem estática estimada de medição executada.
- **Evite falso positivo:** iterar resultados em memória não é N+1. Método de ORM dentro de loop pode usar identity map; não presuma uma consulta por chamada.
- **Correção/verificação:** [T-08](refactoring-playbook.md#t-08); agregação/batch/eager loading apropriado, mantendo escopo, ordem, duplicidade e resultados vazios.

## AP-09 · Regras ou validações duplicadas e divergentes

- **Referência:** MEDIUM para duplicação de regra ou validação que favorece inconsistência.
- **Sinais:** mesma política em criação/edição, cálculo repetido em handlers ou constantes existentes ignoradas em cópias locais.
- **Confirme:** equivalência semântica e diferenças intencionais entre operações; ausência de uma validação pode exigir um achado mesmo sem cópia.
- **Evite falso positivo:** semelhança textual não significa mesma regra; PATCH pode permitir omissão de campos exigidos na criação.
- **Correção/verificação:** [T-09](refactoring-playbook.md#t-09); regra única reutilizável com adaptações de entrada explícitas; testar limites, omissões e valores inválidos.

## AP-10 · Tratamento inadequado de erros

- **Referência:** MEDIUM quando falha ignorada ou tradução inconsistente pode produzir erro secundário/sucesso indevido; elevar com impacto demonstrado.
- **Sinais:** callback ignora erro, `catch` vazio, resposta de sucesso após falha, detalhes internos devolvidos ao cliente.
- **Confirme:** propagação síncrona/assíncrona, contrato de erro do framework e caminhos de rollback/cleanup. Exposição sensível pode se relacionar a AP-02.
- **Evite falso positivo:** tratamento em middleware superior pode ser suficiente; não adicionar capturas que ocultem causa ou dupliquem respostas.
- **Correção/verificação:** [T-10](refactoring-playbook.md#t-10); tradução central e falha observável sem segredo nem falso sucesso.

## AP-11 · Uso de APIs deprecated

- **Referência:** MEDIUM para dívida confirmada de compatibilidade/padronização; ajustar conforme impacto e disponibilidade do substituto.
- **Sinais:** avisos locais disponíveis, símbolos citados em guias de migração e interfaces que a documentação oficial da versão marca como deprecated/legacy.
- **Confirme:** procedimento abaixo. Uma versão antiga ou sintaxe pouco familiar não confirma depreciação.
- **Evite falso positivo:** método homônimo de outra biblioteca/versão ou API legacy ainda suportada não autoriza afirmar remoção/falha de boot.
- **Correção/verificação:** [T-11](refactoring-playbook.md#t-11); substituição confirmada, com semântica, serialização, tipos e efeitos verificados.

### Confirmação eficiente de depreciações

1. Inventarie biblioteca, versão com fonte e usos no código próprio; não importe a aplicação para descobri-los. Agrupe candidatos por biblioteca/versão/símbolo.
2. Consulte documentação oficial local aplicável ou guias oficiais online da versão. Sem URL conhecida, pesquise no domínio oficial com as ferramentas disponíveis; não dependa de plugin/provedor específico.
3. Registre símbolo, condição de depreciação, versão desde quando aplicável, substituto, URL/seção e data. Leia somente as seções necessárias; reutilize a evidência documental do grupo durante a execução, verificando cada contexto de uso.
4. Confira mudanças semânticas, requisitos do substituto e migrações de dados/contrato. Não transforme a recomendação documental em troca textual indiscriminada.
5. Sem fonte/versão suficiente, registre candidato e pendência, sem contar como depreciação confirmada. Não faça consultas ilimitadas nem escreva cache antes da aprovação. Evidência de outra sessão/versão precisa ter a aplicabilidade conferida.

Exemplos de pistas, não uma lista de detecção fechada: [`datetime.utcnow()` em Python 3.13](https://docs.python.org/3.13/library/datetime.html#datetime.datetime.utcnow) e [`Query.get()` no SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.get). A primeira está deprecated desde Python 3.12; a segunda é legacy/deprecated desde SQLAlchemy 2.0. Os trechos oficiais foram consultados em 27/10/2026; confira a versão recebida em cada execução.

## AP-12 · Valores de domínio sem significado explícito

- **Referência:** LOW quando literais escondem o significado de políticas de negócio sem erro funcional comprovado.
- **Sinais:** limites, taxas e prazos repetidos sem nome ou com significado reconstruído a partir do contexto.
- **Confirme:** qual política o valor representa, unidade e origem; diferencie constante de domínio de parâmetro operacional.
- **Evite falso positivo:** números convencionais claros, como status HTTP, não são automaticamente magic numbers. Nomear um literal não autoriza alterar seu valor.
- **Correção/verificação:** [T-12](refactoring-playbook.md#t-12); nome com significado/unidade e resultados idênticos nos limites.
