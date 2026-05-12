# `solid_order_demo` sample run

Run from `LLD/02-SOLID-Principles`:

```bash
python -m solid_order_demo
```

Order IDs (UUIDs) change on each run; the structure below matches one successful execution.

---

## Captured output

```
=== 1) Stripe - same CheckoutService, different gateway (OCP/DIP/LSP) ===
[invoice]
INV-e400fa89-f274-4cdb-94e6-f50b5cd2aec2
Total: 48.99
  - Desk lamp x1 @ 29.99
  - USB cable x2 @ 9.50
[email] -> alex@example.com: payment OK for e400fa89-f274-4cdb-94e6-f50b5cd2aec2
result: ok=True, ref=stripe:acct_live_xxx:e400fa89-f274-4cdb-94e6-f50b5cd2aec2

=== 2) PayPal - swap gateway without editing CheckoutService (OCP/DIP) ===
[invoice]
INV-40eac336-abcd-4847-9847-263a8e5b1881
Total: 12.00
  - Notebook x1 @ 12.00
[email] -> jamie@example.com: payment OK for 40eac336-abcd-4847-9847-263a8e5b1881
result: ok=True, ref=paypal:paypal_client_xxx:40eac336-abcd-4847-9847-263a8e5b1881

=== 3) Wallet - substitutable gateway (LSP); ISP: CheckoutService does not know SMS/etc. ===
[invoice]
INV-2aa4d823-ef33-42f4-bae4-872245c10ce9
Total: 40.00
  - Book x1 @ 40.00
[email] -> mo@example.com: payment OK for 2aa4d823-ef33-42f4-bae4-872245c10ce9
result: ok=True, ref=wallet:2aa4d823-ef33-42f4-bae4-872245c10ce9

=== 4) Wallet decline - still returns ChargeResult; no broken substitute (LSP contract) ===
result: ok=False, ref=insufficient_wallet_balance
```

---

## What each block shows

### Section 1 — Stripe

- Payment succeeds through `StripeGateway`.
- **`[invoice]`** — `SimpleInvoiceGenerator` (single responsibility: invoice text only).
- **`[email]`** — `EmailNotifier` (single responsibility: customer notification only).
- **`result: ok=True, ref=stripe:…`** — charge succeeded; reference encodes provider and order id.

This illustrates **DIP**: `CheckoutService` talks to the `PaymentGateway` abstraction, not to Stripe’s SDK directly. **OCP**: you could add another gateway class without editing checkout logic. **LSP**: this gateway is interchangeable with others behind the same interface.

### Section 2 — PayPal

- Same `CheckoutService` pattern; only the injected gateway is `PayPalGateway`.
- Confirms **open/closed** and **dependency inversion**: new behavior via new class + wiring, not by modifying the orchestrator.

### Section 3 — Wallet

- `WalletGateway` deducts from an in-memory balance and still returns the same kind of outcome as card/PayPal from checkout’s point of view.
- **LSP**: callers do not special-case “wallet vs card”; they always call `charge(order)` and inspect `ChargeResult`.
- **ISP**: checkout depends on small protocols (`OrderLookup`, `PaymentGateway`, …); it is not forced to implement or know about unrelated capabilities (e.g. SMS).

### Section 4 — Wallet decline

- A second order for the same wallet customer exceeds remaining balance.
- **`ok=False`** with **`insufficient_wallet_balance`** — failure is expressed as data (`ChargeResult`), not as an uncaught exception that would break substitution expectations.
- Notice there is **no** invoice or email line: `CheckoutService` only confirms payment and triggers downstream steps after a successful charge (**single responsibility** flow control).

---

## SOLID quick map (this demo)

| Principle | What to notice in the output |
|-----------|------------------------------|
| **S** — Single responsibility | Invoice, email, repo, and payment classes each do one job; checkout only coordinates. |
| **O** — Open/closed | Sections 1–3 use different gateways without changing `CheckoutService`. |
| **L** — Liskov substitution | Every gateway is used the same way; wallet failure still honors the contract. |
| **I** — Interface segregation | Checkout depends on narrow protocols, not one oversized interface. |
| **D** — Dependency inversion | Checkout receives abstractions (protocols); concrete Stripe/PayPal/wallet are injected. |
