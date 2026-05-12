"""SRP: outbound customer messaging only."""

from __future__ import annotations

from .models import Order


class EmailNotifier:
    def notify_payment_confirmed(self, order: Order) -> None:
        print(f"[email] -> {order.customer_email}: payment OK for {order.order_id}")
