"""SRP: invoice artifact creation only."""

from __future__ import annotations

from .models import Order


class SimpleInvoiceGenerator:
    def generate(self, order: Order) -> str:
        lines = "\n".join(f"  - {li.name} x{li.quantity} @ {li.unit_price}" for li in order.items)
        doc = f"INV-{order.order_id}\nTotal: {order.total}\n{lines}"
        print(f"[invoice]\n{doc}")
        return doc
