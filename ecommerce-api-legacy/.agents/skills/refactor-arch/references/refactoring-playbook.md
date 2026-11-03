# Playbook de refatoração

Use na Fase 2 para propor correções e na Fase 3 aprovada para executá-las. Cada transformação se liga ao AP de mesmo número no [catálogo](anti-patterns.md). Os exemplos antes/depois demonstram mecanismos e não são arquivos prontos nem modelos obrigatórios para todas as stacks. Adapte tipos, APIs, contratos e estrutura à aplicação recebida.

Os blocos “Antes” contêm falhas intencionais: não os execute contra aplicações/dados reais. Interfaces auxiliares são descritas em cada transformação. Confirme versões e semântica antes de usar bibliotecas. Toda mudança observável e migração necessária deve integrar a proposta aprovada.

## T-01

**Substituir composição insegura de consultas por binding de parâmetros.** AP-01. Exemplo Python/SQLite: `db` é uma conexão existente; `email` é entrada externa.

Antes:

```python
def find_account(db, email):
    sql = f"SELECT id FROM accounts WHERE email = '{email}'"
    return db.execute(sql).fetchall()
```

Depois:

```python
def find_account(db, email):
    return db.execute(
        "SELECT id FROM accounts WHERE email = ?", (email,)
    ).fetchall()
```

Use o binding do driver/ORM real; placeholders não protegem nomes de coluna/tabela. Para ordenação/identificadores dinâmicos, valide contra opções permitidas. **Verifique:** busca legítima preservada e entrada semelhante a SQL tratada como texto, sem ampliar o conjunto retornado.

## T-02

**Definir a representação pública e reduzir dados sensíveis nas saídas.** AP-02. Exemplo JavaScript: `account` é um registro com campos públicos e privados.

Antes:

```javascript
function presentAccount(account) {
  return { ...account };
}
```

Depois:

```javascript
function presentAccount(account) {
  return { id: account.id, displayName: account.displayName };
}
```

Determine os campos públicos legítimos pelo contrato recebido; os dois campos do exemplo não são uma lista universal. Aplique a mesma seleção consciente a logs/erros, registrando evento e identificadores necessários sem corpos completos. **Verifique:** campos legítimos mantidos e senha/hash/token/cartão ausentes nas saídas afetadas; a mudança de contrato deve estar aprovada.

## T-03

**Trocar proteção inadequada por hasher próprio para senhas.** AP-03. Exemplo Python: `password` é uma senha nova; persistência/verificação são responsabilidades do fluxo real.

Antes:

```python
def encode_password(password):
    return password

def matches_password(stored, candidate):
    return stored == candidate
```

Depois, em ambiente com Werkzeug compatível:

```python
from werkzeug.security import check_password_hash, generate_password_hash

def encode_password(password):
    return generate_password_hash(password, method="scrypt")

def matches_password(stored, candidate):
    return check_password_hash(stored, candidate)
```

Prefira recurso adequado já disponível na stack. A API ilustrada é suportada pelo Werkzeug 3.1; não adicionar essa dependência a outra stack por causa do exemplo. Não comparar hashes regenerados, nem persistir senha em texto puro junto do hash. **Migração:** identificar formato antigo e planejar conversão segura/reset ou atualização após verificação legítima, sem reinterpretar hashes como senhas. Aprovar impactos sobre login/dados. **Verifique:** senha válida/ inválida, salt distinto para a mesma senha e caminho dos registros antigos; confira limites/recursos do hasher no ambiente real.

## T-04

**Aplicar autenticação e política de autorização por recurso.** AP-04. Exemplo JavaScript assíncrono: `actor` é identidade já verificada pelo mecanismo confiável da aplicação; nunca vem diretamente do corpo HTTP. `documents.findById(id)` e `documents.remove(id)` são operações do armazenamento, e a função retorna status para tradução pelo Controller.

Antes:

```javascript
async function removeDocument(actor, id, documents) {
  await documents.remove(id);
  return 204;
}
```

Depois:

```javascript
async function removeDocument(actor, id, documents) {
  if (!actor) return 401;
  const document = await documents.findById(id);
  if (!document) return 404;
  if (document.ownerId !== actor.id) return 403;
  await documents.remove(id);
  return 204;
}
```

O exemplo supõe política aprovada de exclusão pelo proprietário e identificadores normalizados. Adapte política, privilégios administrativos, status e prevenção de vazamento de existência ao projeto. Preserve a funcionalidade autorizada; não crie um mecanismo fictício de login para aparentar proteção. Avalie atomicidade da checagem/exclusão caso o vínculo possa mudar concorrentemente. **Verifique:** sem identidade, outro proprietário, recurso ausente e proprietário autorizado, incluindo o efeito no armazenamento.

## T-05

**Separar regra, persistência, coordenação e apresentação.** AP-05. Exemplo Python: `lines` contém itens previamente validados com preço e quantidade; `db` é conexão e `request_data` representa a entrada adaptada pelo limite HTTP.

Antes:

```python
def create_order(request_data, db):
    total = sum(line["price"] * line["quantity"] for line in request_data["lines"])
    cursor = db.execute("INSERT INTO orders(total) VALUES (?)", (total,))
    return {"id": cursor.lastrowid, "total": total}
```

Depois, em módulos coesos da camada Model e do Controller:

```python
def calculate_total(lines):
    return sum(line["price"] * line["quantity"] for line in lines)

class OrderModel:
    def __init__(self, db):
        self.db = db

    def create(self, lines):
        total = calculate_total(lines)
        cursor = self.db.execute("INSERT INTO orders(total) VALUES (?)", (total,))
        return {"id": cursor.lastrowid, "total": total}

def create_order(request_data, orders):
    order = orders.create(request_data["lines"])
    return {"id": order["id"], "total": order["total"]}
```

A composição fornece `OrderModel(db)` ao Controller; a rota o associa à entrada e traduz a saída conforme o framework. A transação pertence ao fluxo definido, não a um commit oculto por método. A regra funciona sem HTTP/banco. Este exemplo não determina política monetária nem armazenamento completo de itens. Adapte representação monetária existente sem introduzir mudança de precisão não aprovada. **Verifique:** cálculo isolado e cenário integrado de criação/resposta/persistência; evite transformar o Model em outra God Class.

## T-06

**Dar ciclo de vida explícito aos recursos mutáveis.** AP-06. Exemplo Python/SQLite: a conexão anterior é compartilhada; a versão posterior permite conexão dedicada a cada escopo. Em frameworks com sessão/pool gerenciado, prefira integrar esse mecanismo.

Antes:

```python
import sqlite3

shared_connection = sqlite3.connect("app.db", check_same_thread=False)

def load_records():
    return shared_connection.execute("SELECT id FROM records").fetchall()
```

Depois, em Python 3.12+:

```python
import sqlite3
from contextlib import closing

def load_records(database_path):
    with closing(sqlite3.connect(database_path, autocommit=False)) as db:
        return db.execute("SELECT id FROM records").fetchall()
```

`closing` garante fechamento; este exemplo só lê e não faz commit. Escritas precisam da política transacional apropriada. Não abra conexão por método se uma operação requer compartilhar uma transação. **Verifique:** operações/testes não compartilham dados temporários indevidos; conexão fecha também em erro. Configuração recebe o caminho do ambiente isolado, sem copiar o caminho literal anterior.

## T-07

**Proteger invariantes de gravações relacionadas.** AP-07. Exemplo Python/SQLite: duas contas existem e uma transferência deve ocorrer integralmente. `db` é conexão dedicada com `autocommit=False`, sem transação de um chamador a preservar.

Antes:

```python
def transfer(db, source_id, target_id, amount):
    db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, source_id))
    db.commit()
    db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, target_id))
    db.commit()
```

Depois:

```python
def transfer(db, source_id, target_id, amount):
    if amount <= 0:
        raise ValueError("O valor deve ser positivo")
    with db:
        debit = db.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?",
            (amount, source_id, amount),
        )
        if debit.rowcount != 1:
            raise ValueError("Origem ausente ou saldo insuficiente")
        credit = db.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, target_id),
        )
        if credit.rowcount != 1:
            raise ValueError("Destino ausente")
```

O contexto da conexão confirma ou desfaz a transação; não fecha a conexão. Use unidades monetárias inteiras neste exemplo. No projeto, respeite precisão, isolamento e transação existente. Efeito externo não é revertido pelo banco: proponha sandbox, idempotência e compensação/outbox quando o fluxo exigir, sem prometer atomicidade distribuída. **Verifique:** sucesso, saldo insuficiente e falha após débito, com saldos originais preservados após rollback.

## T-08

**Substituir consultas repetidas por acesso em conjunto.** AP-08. Exemplo Python/SQLite: relatório de quantidade de itens por coleção, sem paginação neste recorte.

Antes:

```python
def collection_sizes(db):
    result = []
    for (collection_id,) in db.execute("SELECT id FROM collections ORDER BY id").fetchall():
        count = db.execute(
            "SELECT COUNT(*) FROM entries WHERE collection_id = ?", (collection_id,)
        ).fetchone()[0]
        result.append((collection_id, count))
    return result
```

Depois:

```python
def collection_sizes(db):
    return db.execute(
        "SELECT c.id, COUNT(e.id) FROM collections c "
        "LEFT JOIN entries e ON e.collection_id = c.id "
        "GROUP BY c.id ORDER BY c.id"
    ).fetchall()
```

Para ORMs, avalie agregação, batch ou eager loading que preservem filtros/autorização/paginação. `COUNT(e.id)` mantém zero para coleção vazia; `COUNT(*)` mudaria esse resultado no LEFT JOIN. **Verifique:** coleções vazias e com vários itens, ordenação e número de consultas com cardinalidades diferentes. Não chamar redução estimada de medição de latência.

## T-09

**Centralizar a regra compartilhada com entrada explícita por operação.** AP-09. Exemplo JavaScript: preço numérico finito e positivo é a política suposta; `catalog` fornece `create(data)` e `update(id, data)`.

Antes:

```javascript
function createItem(input, catalog) {
  if (!Number.isFinite(input.price) || input.price <= 0) throw new Error("Preço inválido");
  return catalog.create(input);
}

function updateItem(id, input, catalog) {
  return catalog.update(id, input);
}
```

Depois:

```javascript
function validatePrice(price) {
  if (!Number.isFinite(price) || price <= 0) throw new Error("Preço inválido");
}

function createItem(input, catalog) {
  validatePrice(input.price);
  return catalog.create(input);
}

function updateItem(id, input, catalog) {
  if (Object.prototype.hasOwnProperty.call(input, "price")) validatePrice(input.price);
  return catalog.update(id, input);
}
```

O exemplo preserva omissão em atualização parcial e valida valor enviado, inclusive `null`, sem aceitar coerção acidental de string. Adapte a política real e a tradução central do erro. **Verifique:** criação sem preço, zero/negativo/não finito, atualização válida, inválida e sem o campo; o armazenamento não deve ser chamado após rejeição.

## T-10

**Propagar falhas e traduzi-las no limite da aplicação.** AP-10. Exemplo JavaScript/Express: `records.list(callback)` segue a convenção `(error, rows)` e `app` já existe.

Antes:

```javascript
app.get("/records", (req, res) => {
  records.list((error, rows) => {
    res.json(rows);
  });
});
```

Depois, compatível com encaminhamento explícito em Express 4/5:

```javascript
app.get("/records", (req, res, next) => {
  records.list((error, rows) => {
    if (error) return next(error);
    return res.json(rows);
  });
});

app.use((error, req, res, next) => {
  if (res.headersSent) return next(error);
  return res.status(500).json({ error: "Falha interna" });
});
```

Registre o middleware após rotas. No projeto, preserve erros de domínio/cliente com status aprovados e acrescente diagnóstico interno com dados mínimos e correlação, sem segredos. Falhas assíncronas exigem mecanismo adequado à versão; não presuma propagação automática de qualquer Promise em versões anteriores. **Verifique:** sucesso, erro do armazenamento, resposta sem detalhes internos e ausência de resposta dupla/falso sucesso.

## T-11

**Migrar API deprecated com conferência semântica.** AP-11. Exemplo Python 3.12+: `datetime.utcnow()` produz data sem timezone, apesar de representar UTC.

Antes:

```python
from datetime import datetime

def current_instant():
    return datetime.utcnow()
```

Depois, quando o contrato aprovado admite datetime consciente de timezone:

```python
from datetime import datetime, timezone

def current_instant():
    return datetime.now(timezone.utc)
```

Confirme versão e fonte oficial antes de propor a mudança. O retorno muda de naive para aware; alinhe comparações, persistência e serialização. Não substituir globalmente sem essa análise. Se o armazenamento exige UTC naive, defina conversão explícita nesse limite, com justificativa e testes. Outro exemplo de pista é `Query.get()` → `Session.get()` em SQLAlchemy 2.x; confira sessão/modelo e ausência do registro em cada uso. **Verifique:** tipo/UTC, comparações e contratos temporais; só considere resolvida a migração dos caminhos efetivamente conferidos.

## T-12

**Nomear valores de domínio sem mudar a política.** AP-12. Exemplo Python: valores monetários em centavos e uma política existente de gratuidade do frete a partir de um limite.

Antes:

```python
def shipping_cost(total_cents):
    return 0 if total_cents >= 20000 else 1500
```

Depois:

```python
FREE_SHIPPING_THRESHOLD_CENTS = 20000
STANDARD_SHIPPING_COST_CENTS = 1500

def shipping_cost(total_cents):
    if total_cents >= FREE_SHIPPING_THRESHOLD_CENTS:
        return 0
    return STANDARD_SHIPPING_COST_CENTS
```

Este recorte apenas nomeia a política de frete existente. Não acrescente validação ou ajuste de valores por preferência. Constantes do domínio podem ficar junto da regra coesa; parâmetros operacionais configuráveis pertencem à configuração.

Para configuração sensível, extraia leitura/validação para módulo próprio, conecte-o na entrada e injete o necessário. Nunca use segredo hardcoded como fallback; documente os nomes requeridos e prepare valores sintéticos para o ambiente de validação aprovado. **Verifique:** valores abaixo/no/acima do limite com resultados idênticos; boot e erro claro para configuração obrigatória ausente, sem imprimir valores privados.

## Fontes dos exemplos dependentes de API

Consultadas em 27/10/2026; aplicabilidade deve ser conferida para o projeto recebido:

- [Python 3.13, binding de valores](https://docs.python.org/3.13/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries) e [controle de transações](https://docs.python.org/3.13/library/sqlite3.html#transaction-control).
- [Werkzeug 3.1, funções de segurança](https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security).
- [Express, tratamento de erros](https://expressjs.com/en/guide/error-handling/).
- [Python 3.13, `datetime.utcnow`](https://docs.python.org/3.13/library/datetime.html#datetime.datetime.utcnow) e [SQLAlchemy 2.0, `Query.get`](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html#sqlalchemy.orm.Query.get).
