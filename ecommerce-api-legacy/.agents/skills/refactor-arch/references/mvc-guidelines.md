# Guidelines de arquitetura MVC

Use na auditoria para avaliar responsabilidades e na refatoração para orientar a estrutura. A arquitetura alvo é MVC simples, adaptada às convenções da linguagem/framework e à organização adequada que já existir.

## Responsabilidades

| Parte | Responsabilidade e limite |
| --- | --- |
| Model | Dados, regras do domínio e persistência em módulos coesos. Regras reutilizáveis não dependem de request/response HTTP. Não concentrar toda a aplicação em um único Model. |
| Controller | Adaptar a interação e coordenar o fluxo: receber entrada, chamar operações do domínio e selecionar resposta/erro. Delegar SQL e regras de negócio; evitar handlers com toda a aplicação embutida. |
| View/apresentação | Representação entregue ao usuário/cliente: template, serializador ou projeção explícita de campos. Não expor o objeto persistido integralmente por conveniência. |
| Routes | Associar método/caminho às ações e compor middlewares conforme o framework. Rotas não são sinônimo de Views; “Views/Routes” é uma convenção de organização que não elimina a responsabilidade de apresentação. |
| Configuração | Ler e validar parâmetros de ambiente no limite da aplicação, sem segredos hardcoded ou defaults secretos. Separar configurações operacionais de constantes do domínio. |
| Tratamento de erros | Traduzir falhas em respostas consistentes no limite de entrada. Preservar causas úteis para diagnóstico, sem vazar segredos, stack traces ou detalhes internos ao cliente. |
| Entrada/composição | Construir e conectar dependências, registrar rotas e iniciar o runtime. Evitar consultas, seeds e operações de negócio implícitas ao importar módulos. |

A distribuição concreta da adaptação de entrada/saída pode variar por framework. Avalie quem faz o trabalho e suas dependências, não o nome do arquivo ou uma árvore universal de diretórios.

## Quando acrescentar uma camada

Serviços são úteis quando um fluxo precisa coordenar operações/transações/integrações ou ser reutilizado por entradas diferentes. Repositories, portas ou adapters podem ajudar quando isolam uma dependência concreta ou viabilizam testes relevantes. A quantidade de entidades ou o tamanho de um arquivo são pistas, não justificativas suficientes.

Evite criar camadas de simples repasse. Aproveite mecanismos nativos de sessão, injeção e ciclo de vida quando adequados; não substitua uma abstração saudável para uniformizar pastas.

## Contratos e correções

Preserve endpoints originais e funcionalidades legítimas. Uma movimentação interna deve preservar o comportamento observável; uma correção pode exigir mudança de resposta, entrada, status, autorização ou armazenamento.

Antes de implementá-la, explique na auditoria o comportamento atual, o risco, a mudança proposta, impactos sobre clientes/dados e o resultado esperado. Exemplos: retirar credenciais de respostas; proteger uma operação e validar também seu acesso autorizado; migrar senhas com estratégia de compatibilidade/reset aprovada. Apagar uma operação para eliminar o risco não satisfaz automaticamente a preservação exigida.

Não altere regras comerciais, valores de domínio ou semântica de dados por preferência arquitetural. Configuração extraída precisa manter o boot viável no ambiente de validação, com nomes de variáveis e requisitos documentados sem valores reais.

## Conferência da estrutura resultante

- Model, apresentação/roteamento e Controller têm responsabilidades distinguíveis e caminhos de dependência coerentes.
- Regras/persistência não ficaram apenas renomeadas dentro de um Controller ou God Model.
- Configuração é explícita, erros têm tradução central e a entrada conecta as partes.
- Sessões/conexões/recursos têm ciclo de vida e transações apropriados.
- Interfaces continuam acessíveis com os contratos preservados ou mudanças aprovadas.
- Testes podem exercitar regras sem exigir objetos HTTP, quando aplicável, e integrações são verificadas no limite adequado.

Uma árvore de diretórios sozinha não prova que estes critérios foram atendidos.
