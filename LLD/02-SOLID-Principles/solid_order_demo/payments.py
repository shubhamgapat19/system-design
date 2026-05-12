"""
OCP: add a new gateway by adding a class — CheckoutService stays unchanged.
LSP: any PaymentGateway must honor charge(order)->ChargeResult without surprising side effects.
"""

from __future__ import annotations

from decimal import Decimal

from .models import Order
from .protocols import ChargeResult


class StripeGateway:
    """Card payments via Stripe-shaped API."""

    def __init__(self, merchant_id: str) -> None:
        self._merchant_id = merchant_id

    def charge(self, order: Order) -> ChargeResult:
        ref = f"stripe:{self._merchant_id}:{order.order_id}"
        return ChargeResult(True, ref)


class PayPalGateway:
    """PayPal redirect / REST capture — different details, same contract."""

    def __init__(self, client_id: str) -> None:
        self._client_id = client_id

    def charge(self, order: Order) -> ChargeResult:
        ref = f"paypal:{self._client_id}:{order.order_id}"
        return ChargeResult(True, ref)


class WalletGateway:
    """Mobile wallet / closed-loop balance."""

    def __init__(self, balances: dict[str, Decimal]) -> None:
        self._balances = balances

    def charge(self, order: Order) -> ChargeResult:
        key = order.customer_email
        bal = self._balances.get(key, Decimal("0"))
        if bal < order.total:
            return ChargeResult(False, "insufficient_wallet_balance")
        self._balances[key] = bal - order.total
        ref = f"wallet:{order.order_id}"
        return ChargeResult(True, ref)
