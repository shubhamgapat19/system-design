"""Run: python -m solid_order_demo (from 02-SOLID-Principles directory)."""

from decimal import Decimal

from solid_order_demo.checkout_service import CheckoutService
from solid_order_demo.invoices import SimpleInvoiceGenerator
from solid_order_demo.models import LineItem, Order
from solid_order_demo.notifications import EmailNotifier
from solid_order_demo.payments import PayPalGateway, StripeGateway, WalletGateway
from solid_order_demo.repositories import InMemoryOrderRepository


def main() -> None:
    repo = InMemoryOrderRepository()
    order = Order(
        customer_email="alex@example.com",
        items=[
            LineItem("SKU-1", "Desk lamp", Decimal("29.99"), 1),
            LineItem("SKU-2", "USB cable", Decimal("9.50"), 2),
        ],
    )
    repo.save(order)

    notifier = EmailNotifier()
    invoices = SimpleInvoiceGenerator()

    print("=== 1) Stripe - same CheckoutService, different gateway (OCP/DIP/LSP) ===")
    svc = CheckoutService(repo, StripeGateway("acct_live_xxx"), notifier, invoices)
    ok, ref = svc.complete_checkout(order.order_id)
    print(f"result: ok={ok}, ref={ref}\n")

    order2 = Order(
        customer_email="jamie@example.com",
        items=[LineItem("SKU-9", "Notebook", Decimal("12.00"), 1)],
    )
    repo.save(order2)

    print("=== 2) PayPal - swap gateway without editing CheckoutService (OCP/DIP) ===")
    svc_pp = CheckoutService(repo, PayPalGateway("paypal_client_xxx"), notifier, invoices)
    ok2, ref2 = svc_pp.complete_checkout(order2.order_id)
    print(f"result: ok={ok2}, ref={ref2}\n")

    balances = {"mo@example.com": Decimal("50.00")}
    order3 = Order(
        customer_email="mo@example.com",
        items=[LineItem("SKU-7", "Book", Decimal("40.00"), 1)],
    )
    repo.save(order3)

    print("=== 3) Wallet - substitutable gateway (LSP); ISP: CheckoutService does not know SMS/etc. ===")
    svc_w = CheckoutService(repo, WalletGateway(balances), notifier, invoices)
    ok3, ref3 = svc_w.complete_checkout(order3.order_id)
    print(f"result: ok={ok3}, ref={ref3}\n")

    print("=== 4) Wallet decline - still returns ChargeResult; no broken substitute (LSP contract) ===")
    broke = Order(
        customer_email="mo@example.com",
        items=[LineItem("SKU-99", "Monitor", Decimal("500.00"), 1)],
    )
    repo.save(broke)
    ok4, ref4 = svc_w.complete_checkout(broke.order_id)
    print(f"result: ok={ok4}, ref={ref4}")


if __name__ == "__main__":
    main()
