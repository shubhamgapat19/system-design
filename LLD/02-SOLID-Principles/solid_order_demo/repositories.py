"""SRP: persistence only — reasons to change are storage/schema, not payments or email."""

from __future__ import annotations

from .models import Order


class InMemoryOrderRepository:
    """Toy store; production might swap for SQL without touching checkout logic (DIP)."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.order_id] = order

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)
