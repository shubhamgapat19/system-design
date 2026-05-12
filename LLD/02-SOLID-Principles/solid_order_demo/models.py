"""Domain models for the checkout example."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4


@dataclass(frozen=True)
class LineItem:
    sku: str
    name: str
    unit_price: Decimal
    quantity: int


@dataclass
class Order:
    """A customer's basket converted into an order awaiting payment."""

    customer_email: str
    items: list[LineItem]
    order_id: str = field(default_factory=lambda: str(uuid4()))
    paid: bool = False

    @property
    def total(self) -> Decimal:
        return sum((li.unit_price * li.quantity for li in self.items), Decimal("0"))
