"""Representações públicas: campos explícitos evitam vazar credenciais."""


def product(row):
    return {key:row[key] for key in ("id","nome","descricao","preco","estoque","categoria","ativo","criado_em")}


def user(row,login=False):
    keys = ("id","nome","email","tipo") if login else ("id","nome","email","tipo","criado_em")
    return {key:row[key] for key in keys}


def order(entry):
    row, items = entry
    result = {key:row[key] for key in ("id","usuario_id","status","total","criado_em")}
    result["itens"] = [{"produto_id":item["produto_id"],"produto_nome":item["produto_nome"] or "Desconhecido",
                        "quantidade":item["quantidade"],"preco_unitario":item["preco_unitario"]} for item in items]
    return result
