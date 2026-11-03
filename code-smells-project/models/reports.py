"""Política original de desconto, inclusive seus limites estritos."""
import math
from database import get_db

DISCOUNT_BANDS = ((10000,0.10),(5000,0.05),(1000,0.02))


def sales_report():
    row = get_db().execute("SELECT COUNT(*) AS quantidade,COALESCE(SUM(total),0) AS faturamento,"
                           "COALESCE(SUM(status='pendente'),0) AS pendentes,"
                           "COALESCE(SUM(status='aprovado'),0) AS aprovados,"
                           "COALESCE(SUM(status='cancelado'),0) AS cancelados FROM pedidos").fetchone()
    revenue, count = row["faturamento"],row["quantidade"]
    if not math.isfinite(revenue):
        raise ValueError("Dados monetários inválidos no armazenamento")
    discount = next((revenue*rate for threshold,rate in DISCOUNT_BANDS if revenue > threshold),0)
    return {"total_pedidos":count,"faturamento_bruto":round(revenue,2),"desconto_aplicavel":round(discount,2),
            "faturamento_liquido":round(revenue-discount,2),"pedidos_pendentes":row["pendentes"],
            "pedidos_aprovados":row["aprovados"],"pedidos_cancelados":row["cancelados"],
            "ticket_medio":round(revenue/count,2) if count else 0}
