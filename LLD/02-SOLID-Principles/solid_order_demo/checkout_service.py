"""
SRP: coordinates checkout steps only — does not implement storage, gateways, etc.
DIP: depends on OrderLookup, PaymentGateway, CustomerNotifier, InvoiceGenerator abstractions.
"""

from __future__ import annotations

from .models import Order
from .protocols import CustomerNotifier, InvoiceGenerator, OrderLookup, PaymentGateway


class CheckoutService:
    def __init__(
        self,
        orders: OrderLookup,
        payment: PaymentGateway,
        notifier: CustomerNotifier,
        invoices: InvoiceGenerator,
    ) -> None:
        self._orders = orders
        self._payment = payment
        self._notifier = notifier
        self._invoices = invoices

    def complete_checkout(self, order_id: str) -> tuple[bool, str]:
        order = self._orders.get_order(order_id)
        if order is None:
            return False, "order_not_found"
        if order.paid:
            return False, "already_paid"

        result = self._payment.charge(order)
        if not result.success:
            return False, result.reference

        order.paid = True
        self._invoices.generate(order)
        self._notifier.notify_payment_confirmed(order)
        return True, result.reference
