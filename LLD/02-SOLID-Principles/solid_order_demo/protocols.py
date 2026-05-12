"""
Abstractions for Dependency Inversion (DIP) and narrow interfaces (ISP).

ISP: clients depend only on small protocols (lookup vs pay vs notify vs invoice),
not one "mega storefront" interface.
"""

from __future__ import annotations

from typing import Protocol

from .models import Order


class ChargeResult:
    __slots__ = ("success", "reference")

    def __init__(self, success: bool, reference: str) -> None:
        self.success = success
        self.reference = reference


class OrderLookup(Protocol):
    """Whoever fulfills checkout needs to load orders — nothing else."""

    def get_order(self, order_id: str) -> Order | None: ...


class PaymentGateway(Protocol):
    """Charge money — implemented by Stripe, PayPal, wallets, etc."""

    def charge(self, order: Order) -> ChargeResult: ...


class CustomerNotifier(Protocol):
    """Tell the customer something happened — email/SMS/push are interchangeable."""

    def notify_payment_confirmed(self, order: Order) -> None: ...


class InvoiceGenerator(Protocol):
    """Produce proof of purchase — PDF/HTML/storage varies."""

    def generate(self, order: Order) -> str: ...
