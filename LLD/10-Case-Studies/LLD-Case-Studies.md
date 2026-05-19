# LLD Case Studies — Real-World Systems Dissected

> How top Indian & global tech companies apply OOP, SOLID, Design Patterns, and architecture principles in production systems.

---

## Why Case Studies Before Practice?

```
Concepts (01-09) → Case Studies (see how pros do it) → Practice Problems (do it yourself)
```

You've learned the *what*. Case studies show you the *how* and *why* in real systems — so when you design your own, you make informed decisions, not guesses.

---

## Case Study 1: Razorpay Payment Gateway

### The System
India's largest payment gateway — processes ₹5+ lakh crore annually. Handles UPI, cards, netbanking, wallets, EMI — all through a single API.

### LLD Concepts Applied

#### 1. Strategy Pattern (Payment Methods)

The core challenge: 15+ payment methods, each with different flows, but the merchant API must stay the same.

```python
from abc import ABC, abstractmethod

# --- Strategy Interface ---
class PaymentStrategy(ABC):
    @abstractmethod
    def initiate(self, amount: int, metadata: dict) -> dict:
        pass
    
    @abstractmethod
    def verify(self, transaction_id: str) -> bool:
        pass
    
    @abstractmethod
    def refund(self, transaction_id: str, amount: int) -> dict:
        pass


# --- Concrete Strategies ---
class UPIPayment(PaymentStrategy):
    def initiate(self, amount: int, metadata: dict) -> dict:
        vpa = metadata["vpa"]  # user@paytm
        # Generate collect request via NPCI
        return {
            "transaction_id": "txn_upi_abc123",
            "type": "collect",
            "vpa": vpa,
            "status": "pending",
            "timeout_seconds": 300
        }
    
    def verify(self, transaction_id: str) -> bool:
        # Poll NPCI callback status
        return True
    
    def refund(self, transaction_id: str, amount: int) -> dict:
        # UPI refunds go directly to bank account
        return {"refund_id": "rfnd_upi_xyz", "status": "processed"}


class CardPayment(PaymentStrategy):
    def initiate(self, amount: int, metadata: dict) -> dict:
        card_token = metadata["card_token"]
        # Route to card network (Visa/Mastercard/RuPay)
        # Handle 3D Secure if required
        return {
            "transaction_id": "txn_card_def456",
            "type": "authorize",
            "requires_3ds": True,
            "redirect_url": "https://bank.com/3ds/verify"
        }
    
    def verify(self, transaction_id: str) -> bool:
        # Check with acquiring bank
        return True
    
    def refund(self, transaction_id: str, amount: int) -> dict:
        # Card refunds take 5-7 business days
        return {"refund_id": "rfnd_card_xyz", "status": "initiated", "eta_days": 7}


class NetbankingPayment(PaymentStrategy):
    def initiate(self, amount: int, metadata: dict) -> dict:
        bank_code = metadata["bank_code"]  # HDFC, ICICI, SBI...
        return {
            "transaction_id": "txn_nb_ghi789",
            "type": "redirect",
            "redirect_url": f"https://{bank_code}.com/netbanking/pay"
        }
    
    def verify(self, transaction_id: str) -> bool:
        return True
    
    def refund(self, transaction_id: str, amount: int) -> dict:
        return {"refund_id": "rfnd_nb_xyz", "status": "initiated", "eta_days": 10}


# --- Context (Payment Processor) ---
class PaymentProcessor:
    """Single interface for merchants — strategy chosen at runtime."""
    
    STRATEGIES = {
        "upi": UPIPayment,
        "card": CardPayment,
        "netbanking": NetbankingPayment,
    }
    
    def __init__(self, method: str):
        if method not in self.STRATEGIES:
            raise ValueError(f"Unsupported payment method: {method}")
        self._strategy: PaymentStrategy = self.STRATEGIES[method]()
    
    def process(self, amount: int, metadata: dict) -> dict:
        return self._strategy.initiate(amount, metadata)
    
    def verify_payment(self, transaction_id: str) -> bool:
        return self._strategy.verify(transaction_id)
    
    def process_refund(self, transaction_id: str, amount: int) -> dict:
        return self._strategy.refund(transaction_id, amount)


# --- Merchant Integration (clean & simple) ---
# Merchant doesn't care about internal routing
payment = PaymentProcessor(method="upi")
result = payment.process(amount=50000, metadata={"vpa": "customer@paytm"})
# {"transaction_id": "txn_upi_abc123", "status": "pending", ...}
```

#### 2. Observer Pattern (Webhook Notifications)

When payment status changes, multiple systems need to know:

```python
from abc import ABC, abstractmethod
from enum import Enum


class PaymentEvent(Enum):
    AUTHORIZED = "payment.authorized"
    CAPTURED = "payment.captured"
    FAILED = "payment.failed"
    REFUNDED = "payment.refunded"


class WebhookSubscriber(ABC):
    @abstractmethod
    def notify(self, event: PaymentEvent, payload: dict):
        pass


class MerchantWebhook(WebhookSubscriber):
    def __init__(self, url: str, secret: str):
        self.url = url
        self.secret = secret
    
    def notify(self, event: PaymentEvent, payload: dict):
        # POST to merchant's server with HMAC signature
        print(f"→ Webhook to {self.url}: {event.value}")


class InternalAnalytics(WebhookSubscriber):
    def notify(self, event: PaymentEvent, payload: dict):
        # Push to analytics pipeline
        print(f"→ Analytics: {event.value} for ₹{payload['amount']}")


class FraudDetection(WebhookSubscriber):
    def notify(self, event: PaymentEvent, payload: dict):
        # ML model checks for anomalies
        print(f"→ Fraud Check: {event.value} from {payload['ip']}")


class RiskDashboard(WebhookSubscriber):
    def notify(self, event: PaymentEvent, payload: dict):
        # Real-time dashboard update
        print(f"→ Dashboard: {event.value}")


# --- Event Bus ---
class PaymentEventBus:
    def __init__(self):
        self._subscribers: dict[PaymentEvent, list[WebhookSubscriber]] = {}
    
    def subscribe(self, event: PaymentEvent, subscriber: WebhookSubscriber):
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(subscriber)
    
    def publish(self, event: PaymentEvent, payload: dict):
        for subscriber in self._subscribers.get(event, []):
            subscriber.notify(event, payload)


# --- Setup ---
bus = PaymentEventBus()
bus.subscribe(PaymentEvent.CAPTURED, MerchantWebhook("https://shop.com/webhook", "secret123"))
bus.subscribe(PaymentEvent.CAPTURED, InternalAnalytics())
bus.subscribe(PaymentEvent.CAPTURED, FraudDetection())
bus.subscribe(PaymentEvent.FAILED, RiskDashboard())

# When payment succeeds:
bus.publish(PaymentEvent.CAPTURED, {"amount": 50000, "ip": "103.45.67.89"})
```

#### 3. SOLID in Action

| Principle | How Razorpay Applies It |
|-----------|------------------------|
| **SRP** | `PaymentProcessor` only orchestrates. `FraudDetection` only checks risk. `WebhookDispatcher` only sends notifications. |
| **OCP** | Adding Jio Pay = create `JioPayment(PaymentStrategy)`. Zero changes to `PaymentProcessor`. |
| **LSP** | Every strategy is substitutable — merchant code works identically regardless of method. |
| **ISP** | Merchants choose which webhooks to subscribe to. Don't want refund events? Don't subscribe. |
| **DIP** | `PaymentProcessor` depends on `PaymentStrategy` (abstraction), not `UPIPayment` (concrete). |

---

## Case Study 2: Zomato / Swiggy — Food Delivery

### The System
Real-time coordination between customers, restaurants, and delivery partners. Handles 2M+ orders/day with live tracking.

### LLD Concepts Applied

#### 1. State Pattern (Order Lifecycle)

An order goes through many states, each with different allowed transitions:

```python
from abc import ABC, abstractmethod
from datetime import datetime


class OrderState(ABC):
    @abstractmethod
    def confirm(self, order: "Order"):
        pass
    
    @abstractmethod
    def prepare(self, order: "Order"):
        pass
    
    @abstractmethod
    def pick_up(self, order: "Order"):
        pass
    
    @abstractmethod
    def deliver(self, order: "Order"):
        pass
    
    @abstractmethod
    def cancel(self, order: "Order"):
        pass


class PlacedState(OrderState):
    """Order just placed, waiting for restaurant confirmation."""
    
    def confirm(self, order: "Order"):
        order.restaurant_confirmed_at = datetime.now()
        order.set_state(ConfirmedState())
        print(f"✅ Order {order.id} confirmed by restaurant")
    
    def prepare(self, order):
        raise InvalidTransitionError("Cannot prepare before confirming")
    
    def pick_up(self, order):
        raise InvalidTransitionError("Cannot pick up before preparing")
    
    def deliver(self, order):
        raise InvalidTransitionError("Cannot deliver from placed state")
    
    def cancel(self, order: "Order"):
        order.set_state(CancelledState())
        order.refund_amount = order.total  # Full refund
        print(f"❌ Order {order.id} cancelled — full refund ₹{order.total}")


class ConfirmedState(OrderState):
    """Restaurant accepted, preparing food."""
    
    def confirm(self, order):
        raise InvalidTransitionError("Already confirmed")
    
    def prepare(self, order: "Order"):
        order.preparation_started_at = datetime.now()
        order.set_state(PreparingState())
        # Trigger: assign delivery partner
        print(f"👨‍🍳 Order {order.id} preparation started")
    
    def pick_up(self, order):
        raise InvalidTransitionError("Food not prepared yet")
    
    def deliver(self, order):
        raise InvalidTransitionError("Cannot deliver from confirmed state")
    
    def cancel(self, order: "Order"):
        order.set_state(CancelledState())
        order.refund_amount = order.total  # Full refund (food not started)
        print(f"❌ Order {order.id} cancelled — full refund")


class PreparingState(OrderState):
    """Food being prepared, delivery partner assigned."""
    
    def confirm(self, order):
        raise InvalidTransitionError("Already past confirmation")
    
    def prepare(self, order):
        raise InvalidTransitionError("Already preparing")
    
    def pick_up(self, order: "Order"):
        order.picked_up_at = datetime.now()
        order.set_state(OutForDeliveryState())
        print(f"🏍️ Order {order.id} picked up by {order.delivery_partner}")
    
    def deliver(self, order):
        raise InvalidTransitionError("Must pick up first")
    
    def cancel(self, order: "Order"):
        # Partial refund — restaurant already started cooking
        order.set_state(CancelledState())
        order.refund_amount = order.total * 0.5
        print(f"❌ Order {order.id} cancelled — 50% refund (food was being prepared)")


class OutForDeliveryState(OrderState):
    """Delivery partner has food, en route to customer."""
    
    def confirm(self, order):
        raise InvalidTransitionError("Order already out for delivery")
    
    def prepare(self, order):
        raise InvalidTransitionError("Order already out for delivery")
    
    def pick_up(self, order):
        raise InvalidTransitionError("Already picked up")
    
    def deliver(self, order: "Order"):
        order.delivered_at = datetime.now()
        order.set_state(DeliveredState())
        print(f"🎉 Order {order.id} delivered!")
    
    def cancel(self, order: "Order"):
        # Cannot cancel after pickup — too late
        raise InvalidTransitionError("Cannot cancel after pickup. Contact support.")


class DeliveredState(OrderState):
    def confirm(self, order): raise InvalidTransitionError("Order complete")
    def prepare(self, order): raise InvalidTransitionError("Order complete")
    def pick_up(self, order): raise InvalidTransitionError("Order complete")
    def deliver(self, order): raise InvalidTransitionError("Already delivered")
    def cancel(self, order): raise InvalidTransitionError("Cannot cancel delivered order")


class CancelledState(OrderState):
    def confirm(self, order): raise InvalidTransitionError("Order cancelled")
    def prepare(self, order): raise InvalidTransitionError("Order cancelled")
    def pick_up(self, order): raise InvalidTransitionError("Order cancelled")
    def deliver(self, order): raise InvalidTransitionError("Order cancelled")
    def cancel(self, order): raise InvalidTransitionError("Already cancelled")


class InvalidTransitionError(Exception):
    pass


# --- Order Entity ---
class Order:
    def __init__(self, order_id: str, items: list, total: int):
        self.id = order_id
        self.items = items
        self.total = total
        self.delivery_partner = None
        self.refund_amount = 0
        self._state: OrderState = PlacedState()
        
        # Timestamps
        self.placed_at = datetime.now()
        self.restaurant_confirmed_at = None
        self.preparation_started_at = None
        self.picked_up_at = None
        self.delivered_at = None
    
    def set_state(self, state: OrderState):
        self._state = state
    
    def confirm(self):
        self._state.confirm(self)
    
    def start_preparing(self):
        self._state.prepare(self)
    
    def pick_up(self):
        self._state.pick_up(self)
    
    def deliver(self):
        self._state.deliver(self)
    
    def cancel(self):
        self._state.cancel(self)


# --- Usage ---
order = Order("ORD_001", ["Butter Chicken", "Naan x2", "Dal Makhani"], total=650)

order.confirm()          # ✅ Order ORD_001 confirmed by restaurant
order.start_preparing()  # 👨‍🍳 Order ORD_001 preparation started
order.delivery_partner = "Rahul (DL-4532)"
order.pick_up()          # 🏍️ Order ORD_001 picked up by Rahul (DL-4532)
order.deliver()          # 🎉 Order ORD_001 delivered!

# Try invalid transition:
# order.cancel()  → InvalidTransitionError: Cannot cancel delivered order
```

#### 2. Decorator Pattern (Dynamic Pricing & Charges)

Order total is built up from base price + multiple dynamic charges:

```python
from abc import ABC, abstractmethod


class OrderBill(ABC):
    @abstractmethod
    def get_total(self) -> float:
        pass
    
    @abstractmethod
    def get_breakdown(self) -> list[dict]:
        pass


class BaseOrder(OrderBill):
    def __init__(self, items: list[dict]):
        self.items = items  # [{"name": "Biryani", "price": 350}, ...]
    
    def get_total(self) -> float:
        return sum(item["price"] for item in self.items)
    
    def get_breakdown(self) -> list[dict]:
        return [{"label": "Item Total", "amount": self.get_total()}]


class DeliveryFeeDecorator(OrderBill):
    def __init__(self, order: OrderBill, distance_km: float):
        self._order = order
        self.fee = self._calculate_fee(distance_km)
    
    def _calculate_fee(self, distance_km: float) -> float:
        if distance_km <= 3:
            return 20  # Flat ₹20 for nearby
        elif distance_km <= 7:
            return 20 + (distance_km - 3) * 7  # ₹7/km after 3km
        else:
            return 20 + 28 + (distance_km - 7) * 10  # ₹10/km after 7km
    
    def get_total(self) -> float:
        return self._order.get_total() + self.fee
    
    def get_breakdown(self) -> list[dict]:
        return self._order.get_breakdown() + [{"label": "Delivery Fee", "amount": self.fee}]


class SurgeDecorator(OrderBill):
    """Rain/peak hours surge pricing."""
    def __init__(self, order: OrderBill, surge_multiplier: float):
        self._order = order
        self.multiplier = surge_multiplier
    
    def get_total(self) -> float:
        base = self._order.get_total()
        surge_extra = base * (self.multiplier - 1)
        return base + surge_extra
    
    def get_breakdown(self) -> list[dict]:
        base = self._order.get_total()
        surge_extra = base * (self.multiplier - 1)
        return self._order.get_breakdown() + [
            {"label": f"Surge ({self.multiplier}x)", "amount": surge_extra}
        ]


class DiscountDecorator(OrderBill):
    """Coupon or promo discount."""
    def __init__(self, order: OrderBill, code: str, discount_pct: float, max_discount: float):
        self._order = order
        self.code = code
        self.discount = min(self._order.get_total() * discount_pct / 100, max_discount)
    
    def get_total(self) -> float:
        return self._order.get_total() - self.discount
    
    def get_breakdown(self) -> list[dict]:
        return self._order.get_breakdown() + [
            {"label": f"Discount ({self.code})", "amount": -self.discount}
        ]


class GSTDecorator(OrderBill):
    """5% GST on restaurant food delivery."""
    def __init__(self, order: OrderBill):
        self._order = order
    
    def get_total(self) -> float:
        return self._order.get_total() * 1.05
    
    def get_breakdown(self) -> list[dict]:
        gst = self._order.get_total() * 0.05
        return self._order.get_breakdown() + [{"label": "GST (5%)", "amount": gst}]


# --- Build final bill dynamically ---
order = BaseOrder([
    {"name": "Chicken Biryani", "price": 350},
    {"name": "Raita", "price": 50},
    {"name": "Gulab Jamun x2", "price": 80}
])

# Apply charges based on conditions
bill = order                                          # ₹480
bill = DeliveryFeeDecorator(bill, distance_km=5.2)   # + ₹35.4
bill = SurgeDecorator(bill, surge_multiplier=1.2)    # + 20% (it's raining)
bill = DiscountDecorator(bill, "FIRST50", 50, 100)   # - ₹100 (max cap)
bill = GSTDecorator(bill)                            # + 5%

print(f"Final: ₹{bill.get_total():.0f}")
for item in bill.get_breakdown():
    print(f"  {item['label']}: ₹{item['amount']:.0f}")
```

#### 3. Command Pattern (Order Actions / Undo)

Support operations like "restaurant rejects item → remove from order and adjust price":

```python
from abc import ABC, abstractmethod


class OrderCommand(ABC):
    @abstractmethod
    def execute(self):
        pass
    
    @abstractmethod
    def undo(self):
        pass


class AddItemCommand(OrderCommand):
    def __init__(self, order: dict, item: dict):
        self.order = order
        self.item = item
    
    def execute(self):
        self.order["items"].append(self.item)
        self.order["total"] += self.item["price"]
    
    def undo(self):
        self.order["items"].remove(self.item)
        self.order["total"] -= self.item["price"]


class ApplyCouponCommand(OrderCommand):
    def __init__(self, order: dict, discount: float):
        self.order = order
        self.discount = discount
    
    def execute(self):
        self.order["discount"] = self.discount
        self.order["total"] -= self.discount
    
    def undo(self):
        self.order["total"] += self.discount
        self.order["discount"] = 0


class OrderManager:
    def __init__(self):
        self._history: list[OrderCommand] = []
    
    def execute(self, command: OrderCommand):
        command.execute()
        self._history.append(command)
    
    def undo_last(self):
        if self._history:
            command = self._history.pop()
            command.undo()


# Restaurant says "Gulab Jamun out of stock" → undo that item
manager = OrderManager()
order = {"items": [], "total": 0, "discount": 0}

manager.execute(AddItemCommand(order, {"name": "Biryani", "price": 350}))
manager.execute(AddItemCommand(order, {"name": "Gulab Jamun", "price": 80}))
manager.execute(ApplyCouponCommand(order, discount=50))

print(order["total"])  # 380

# Restaurant: "Gulab Jamun not available"
manager.undo_last()  # Undo coupon first
manager.undo_last()  # Undo Gulab Jamun
print(order["total"])  # 350
```

---

## Case Study 3: Uber/Ola — Ride Sharing

### The System
Real-time matching of riders with drivers, dynamic pricing, route optimization, live tracking.

### LLD Concepts Applied

#### 1. Factory Pattern (Vehicle/Ride Types)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RideEstimate:
    ride_type: str
    base_fare: float
    per_km: float
    per_min: float
    surge: float
    estimated_fare: float
    eta_minutes: int


class RideFactory(ABC):
    @abstractmethod
    def create_ride(self, distance_km: float, duration_min: float, surge: float) -> RideEstimate:
        pass


class AutoRideFactory(RideFactory):
    """Auto-rickshaw — cheapest, short distances."""
    def create_ride(self, distance_km: float, duration_min: float, surge: float) -> RideEstimate:
        base = 25
        per_km = 12
        per_min = 1.5
        fare = (base + distance_km * per_km + duration_min * per_min) * surge
        return RideEstimate("Auto", base, per_km, per_min, surge, fare, eta_minutes=3)


class MiniRideFactory(RideFactory):
    """Hatchback — economical car."""
    def create_ride(self, distance_km: float, duration_min: float, surge: float) -> RideEstimate:
        base = 40
        per_km = 14
        per_min = 2
        fare = (base + distance_km * per_km + duration_min * per_min) * surge
        return RideEstimate("Mini", base, per_km, per_min, surge, fare, eta_minutes=5)


class SedanRideFactory(RideFactory):
    """Sedan — comfortable, AC guaranteed."""
    def create_ride(self, distance_km: float, duration_min: float, surge: float) -> RideEstimate:
        base = 70
        per_km = 18
        per_min = 2.5
        fare = (base + distance_km * per_km + duration_min * per_min) * surge
        return RideEstimate("Sedan", base, per_km, per_min, surge, fare, eta_minutes=7)


class PremiumRideFactory(RideFactory):
    """SUV/Luxury — top-tier."""
    def create_ride(self, distance_km: float, duration_min: float, surge: float) -> RideEstimate:
        base = 120
        per_km = 25
        per_min = 3.5
        fare = (base + distance_km * per_km + duration_min * per_min) * surge
        return RideEstimate("Premium", base, per_km, per_min, surge, fare, eta_minutes=10)


# --- Ride Estimator (shows all options to user) ---
class RideEstimator:
    FACTORIES = {
        "auto": AutoRideFactory(),
        "mini": MiniRideFactory(),
        "sedan": SedanRideFactory(),
        "premium": PremiumRideFactory(),
    }
    
    def get_estimates(self, distance_km: float, duration_min: float, surge: float) -> list[RideEstimate]:
        return [
            factory.create_ride(distance_km, duration_min, surge)
            for factory in self.FACTORIES.values()
        ]


# Pune: Hinjewadi to Shivajinagar (18km, 35min, 1.3x surge)
estimator = RideEstimator()
options = estimator.get_estimates(distance_km=18, duration_min=35, surge=1.3)

for opt in options:
    print(f"{opt.ride_type:10} → ₹{opt.estimated_fare:.0f} (ETA: {opt.eta_minutes} min)")
# Auto       → ₹380 (ETA: 3 min)
# Mini       → ₹434 (ETA: 5 min)
# Sedan      → ₹535 (ETA: 7 min)
# Premium    → ₹742 (ETA: 10 min)
```

#### 2. Observer Pattern (Live Ride Tracking)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Location:
    lat: float
    lng: float


class RideObserver(ABC):
    @abstractmethod
    def on_location_update(self, ride_id: str, location: Location):
        pass


class RiderApp(RideObserver):
    """Customer sees driver moving on map."""
    def on_location_update(self, ride_id: str, location: Location):
        print(f"📱 Rider: Driver at ({location.lat}, {location.lng})")


class DriverApp(RideObserver):
    """Driver sees route updates."""
    def on_location_update(self, ride_id: str, location: Location):
        print(f"🚗 Driver: Navigation updated")


class ETAService(RideObserver):
    """Recalculates ETA on every location ping."""
    def on_location_update(self, ride_id: str, location: Location):
        # Recalculate based on traffic + distance remaining
        print(f"⏱️ ETA recalculated for {ride_id}")


class SafetyService(RideObserver):
    """Detects if ride deviates from expected route."""
    def on_location_update(self, ride_id: str, location: Location):
        # Compare with expected route polygon
        print(f"🛡️ Safety check: route deviation analysis")


class LiveRide:
    def __init__(self, ride_id: str):
        self.ride_id = ride_id
        self._observers: list[RideObserver] = []
    
    def add_observer(self, observer: RideObserver):
        self._observers.append(observer)
    
    def update_location(self, location: Location):
        """Called every 3 seconds from driver's phone GPS."""
        for observer in self._observers:
            observer.on_location_update(self.ride_id, location)


# --- Setup for active ride ---
ride = LiveRide("RIDE_7890")
ride.add_observer(RiderApp())
ride.add_observer(DriverApp())
ride.add_observer(ETAService())
ride.add_observer(SafetyService())

# GPS ping from driver:
ride.update_location(Location(18.5204, 73.8567))  # Pune coords
```

#### 3. Concurrency — Driver Matching (Optimistic Locking)

The critical problem: 10 riders request simultaneously → same driver gets matched to multiple rides.

```python
import time
from dataclasses import dataclass, field


@dataclass
class Driver:
    id: str
    name: str
    is_available: bool = True
    version: int = 0  # Optimistic lock version


class DriverMatchingService:
    """
    Uses optimistic locking to prevent double-booking.
    Real Uber uses distributed locks (Redis) for this.
    """
    
    def __init__(self):
        self.drivers: dict[str, Driver] = {}
    
    def try_assign_driver(self, driver_id: str, ride_id: str) -> bool:
        """
        Atomic operation: assign driver only if still available.
        Returns True if assignment succeeded.
        """
        driver = self.drivers.get(driver_id)
        if not driver or not driver.is_available:
            return False
        
        # Optimistic lock check
        current_version = driver.version
        
        # Simulate: another thread might have grabbed this driver
        # In real DB: UPDATE drivers SET is_available=false, version=version+1 
        #             WHERE id=? AND version=? AND is_available=true
        
        if driver.version != current_version:
            return False  # Someone else got them
        
        # Claim the driver
        driver.is_available = False
        driver.version += 1
        print(f"✅ Driver {driver.name} assigned to {ride_id}")
        return True
    
    def find_nearest_available(self, rider_lat: float, rider_lng: float, radius_km: float = 5) -> list[str]:
        """
        In production: geospatial query on Redis/PostGIS.
        SELECT id FROM drivers 
        WHERE is_available = true 
        AND ST_DWithin(location, ST_Point(lng, lat), radius_meters)
        ORDER BY ST_Distance(location, ST_Point(lng, lat))
        LIMIT 10;
        """
        return [d.id for d in self.drivers.values() if d.is_available]
    
    def match_ride(self, ride_id: str, rider_lat: float, rider_lng: float) -> str | None:
        """Try nearest drivers until one accepts."""
        candidates = self.find_nearest_available(rider_lat, rider_lng)
        
        for driver_id in candidates:
            if self.try_assign_driver(driver_id, ride_id):
                return driver_id
        
        return None  # No available drivers — show "No cabs available"


# --- Usage ---
service = DriverMatchingService()
service.drivers = {
    "D1": Driver("D1", "Rajesh"),
    "D2": Driver("D2", "Amit"),
    "D3": Driver("D3", "Suresh"),
}

# Two riders request at same time near same area
result1 = service.match_ride("RIDE_001", 18.52, 73.85)  # Gets Rajesh
result2 = service.match_ride("RIDE_002", 18.52, 73.86)  # Gets Amit (Rajesh taken)
```

---

## Case Study 4: PhonePe / Google Pay — UPI System

### The System
UPI processes 10B+ transactions/month in India. Core challenge: ensure exactly-once processing across multiple banks.

### LLD Concepts Applied

#### 1. Template Method Pattern (Transaction Flow)

Every UPI transaction follows the same skeleton, but specifics vary:

```python
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class TxnStatus(Enum):
    INITIATED = "initiated"
    AUTHENTICATED = "authenticated"
    DEBITED = "debited"
    CREDITED = "credited"
    FAILED = "failed"


class UPITransaction(ABC):
    """Template Method: defines the skeleton of a UPI transaction."""
    
    def execute(self, sender_vpa: str, receiver_vpa: str, amount: float) -> dict:
        """
        The algorithm skeleton — subclasses customize specific steps.
        This order CANNOT change (regulated by NPCI).
        """
        txn_id = self._generate_txn_id()
        
        # Step 1: Validate
        if not self._validate(sender_vpa, receiver_vpa, amount):
            return {"txn_id": txn_id, "status": TxnStatus.FAILED, "reason": "Validation failed"}
        
        # Step 2: Authenticate (PIN/Biometric)
        if not self._authenticate(sender_vpa):
            return {"txn_id": txn_id, "status": TxnStatus.FAILED, "reason": "Auth failed"}
        
        # Step 3: Debit sender
        if not self._debit(sender_vpa, amount, txn_id):
            return {"txn_id": txn_id, "status": TxnStatus.FAILED, "reason": "Debit failed"}
        
        # Step 4: Credit receiver
        if not self._credit(receiver_vpa, amount, txn_id):
            # CRITICAL: Must reverse the debit!
            self._reverse_debit(sender_vpa, amount, txn_id)
            return {"txn_id": txn_id, "status": TxnStatus.FAILED, "reason": "Credit failed, reversed"}
        
        # Step 5: Notify
        self._notify_parties(sender_vpa, receiver_vpa, amount, txn_id)
        
        return {"txn_id": txn_id, "status": TxnStatus.CREDITED, "amount": amount}
    
    def _generate_txn_id(self) -> str:
        return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(self)}"
    
    def _validate(self, sender: str, receiver: str, amount: float) -> bool:
        if amount <= 0 or amount > 100000:  # UPI limit ₹1L
            return False
        if sender == receiver:
            return False
        return True
    
    # --- Abstract steps (subclasses implement) ---
    @abstractmethod
    def _authenticate(self, vpa: str) -> bool:
        pass
    
    @abstractmethod
    def _debit(self, vpa: str, amount: float, txn_id: str) -> bool:
        pass
    
    @abstractmethod
    def _credit(self, vpa: str, amount: float, txn_id: str) -> bool:
        pass
    
    @abstractmethod
    def _reverse_debit(self, vpa: str, amount: float, txn_id: str):
        pass
    
    @abstractmethod
    def _notify_parties(self, sender: str, receiver: str, amount: float, txn_id: str):
        pass


class P2PTransaction(UPITransaction):
    """Person to Person — simple transfer."""
    
    def _authenticate(self, vpa: str) -> bool:
        print(f"  🔐 UPI PIN verified for {vpa}")
        return True
    
    def _debit(self, vpa: str, amount: float, txn_id: str) -> bool:
        print(f"  💸 Debited ₹{amount} from {vpa}")
        return True
    
    def _credit(self, vpa: str, amount: float, txn_id: str) -> bool:
        print(f"  💰 Credited ₹{amount} to {vpa}")
        return True
    
    def _reverse_debit(self, vpa: str, amount: float, txn_id: str):
        print(f"  🔄 Reversed ₹{amount} to {vpa}")
    
    def _notify_parties(self, sender: str, receiver: str, amount: float, txn_id: str):
        print(f"  📱 SMS: {sender} sent ₹{amount} to {receiver}")


class MerchantTransaction(UPITransaction):
    """Person to Merchant — includes invoice, GST handling."""
    
    def _authenticate(self, vpa: str) -> bool:
        # Merchants may have UPI Autopay (no PIN for < ₹500)
        print(f"  🔐 Auto-debit authorized for {vpa} (mandate active)")
        return True
    
    def _debit(self, vpa: str, amount: float, txn_id: str) -> bool:
        print(f"  💸 Debited ₹{amount} from {vpa}")
        return True
    
    def _credit(self, vpa: str, amount: float, txn_id: str) -> bool:
        # Merchant settlement might be T+1
        print(f"  💰 ₹{amount} queued for settlement to {vpa} (T+1)")
        return True
    
    def _reverse_debit(self, vpa: str, amount: float, txn_id: str):
        print(f"  🔄 Reversed ₹{amount} to {vpa}")
    
    def _notify_parties(self, sender: str, receiver: str, amount: float, txn_id: str):
        print(f"  📱 Payment receipt generated for {sender}")
        print(f"  🏪 Merchant dashboard updated for {receiver}")


# --- Usage ---
p2p = P2PTransaction()
result = p2p.execute("rahul@paytm", "priya@okaxis", 500)

print()

merchant = MerchantTransaction()
result = merchant.execute("rahul@paytm", "swiggy@hdfcbank", 350)
```

#### 2. Idempotency (DRY/KISS in Critical Systems)

UPI's biggest challenge — network timeout doesn't mean payment failed:

```python
from datetime import datetime, timedelta


class IdempotencyStore:
    """
    Ensures same transaction request isn't processed twice.
    Real systems use Redis with TTL.
    """
    
    def __init__(self):
        self._store: dict[str, dict] = {}  # idempotency_key → result
    
    def get_or_process(self, idempotency_key: str, processor_fn) -> dict:
        """
        If we've seen this key before → return cached result.
        If new → process and cache.
        """
        if idempotency_key in self._store:
            cached = self._store[idempotency_key]
            cached["_cached"] = True
            print(f"  ⚡ Returning cached result for {idempotency_key}")
            return cached
        
        # First time — process it
        result = processor_fn()
        self._store[idempotency_key] = result
        result["_cached"] = False
        return result
    
    def cleanup_expired(self, ttl_hours: int = 24):
        """Remove entries older than TTL."""
        cutoff = datetime.now() - timedelta(hours=ttl_hours)
        self._store = {
            k: v for k, v in self._store.items()
            if v.get("_timestamp", datetime.now()) > cutoff
        }


# --- Usage ---
store = IdempotencyStore()

# User taps "Pay" → network timeout → user taps again
# Same idempotency key = same transaction, don't debit twice!

def process_payment():
    print("  💸 Processing ₹500 debit...")
    return {"status": "success", "amount": 500, "_timestamp": datetime.now()}

key = "USER_rahul_TXN_20250513_001"

result1 = store.get_or_process(key, process_payment)  # Actually processes
result2 = store.get_or_process(key, process_payment)  # Returns cached — no double debit!
```

---

## Case Study 5: Smart Freight (Your Startup!) — GPS Logistics

### The System
Truck fleet tracking, trip management, driver assignments, live GPS tracking for Indian logistics.

### LLD Concepts Applied Together

#### 1. Architecture Decisions (Clean Architecture + SOLID)

```typescript
// Your NestJS structure applying concepts learned:

// --- Domain Layer (innermost — no dependencies) ---
// src/domain/entities/trip.entity.ts
export class Trip {
  constructor(
    public readonly id: string,
    public status: TripStatus,
    public origin: Location,
    public destination: Location,
    public vehicleId: string,
    public driverId: string,
    public distanceKm: number,
    public estimatedCost: number,
  ) {}

  canStart(): boolean {
    return this.status === TripStatus.ASSIGNED;
  }

  canComplete(): boolean {
    return this.status === TripStatus.IN_TRANSIT;
  }

  start(): void {
    if (!this.canStart()) throw new InvalidTripStateError(this.status, 'start');
    this.status = TripStatus.IN_TRANSIT;
  }

  complete(actualDistance: number): void {
    if (!this.canComplete()) throw new InvalidTripStateError(this.status, 'complete');
    this.status = TripStatus.COMPLETED;
    this.distanceKm = actualDistance;
  }
}


// --- Application Layer (use cases — orchestrates domain) ---
// src/application/use-cases/start-trip.use-case.ts
export class StartTripUseCase {
  constructor(
    private tripRepo: ITripRepository,       // Interface (DIP)
    private gpsService: IGPSTrackingService,  // Interface (DIP)
    private notifier: INotificationService,   // Interface (DIP)
  ) {}

  async execute(tripId: string, driverId: string): Promise<TripDTO> {
    const trip = await this.tripRepo.findById(tripId);
    if (!trip) throw new TripNotFoundError(tripId);
    
    if (trip.driverId !== driverId) throw new UnauthorizedError();

    trip.start();  // Domain logic — validates state
    
    await this.tripRepo.save(trip);
    await this.gpsService.startTracking(trip.vehicleId);
    await this.notifier.send(trip.driverId, `Trip ${tripId} started`);
    
    return TripDTO.from(trip);
  }
}


// --- Infrastructure Layer (outer — implements interfaces) ---
// src/infrastructure/repositories/prisma-trip.repository.ts
export class PrismaTripRepository implements ITripRepository {
  constructor(private prisma: PrismaService) {}

  async findById(id: string): Promise<Trip | null> {
    const data = await this.prisma.trip.findUnique({ where: { id } });
    if (!data) return null;
    return this.toDomain(data);
  }

  async save(trip: Trip): Promise<void> {
    await this.prisma.trip.update({
      where: { id: trip.id },
      data: {
        status: trip.status,
        distanceKm: trip.distanceKm,
        updatedAt: new Date(),
      },
    });
  }
}


// --- Presentation Layer (NestJS Controller) ---
// src/presentation/controllers/trip.controller.ts
@Controller('trips')
export class TripController {
  constructor(private startTripUseCase: StartTripUseCase) {}

  @Post(':id/start')
  @UseGuards(AuthGuard, RoleGuard('driver'))
  async startTrip(
    @Param('id') tripId: string,
    @CurrentUser() user: AuthUser,
  ): Promise<ApiResponse<TripDTO>> {
    const trip = await this.startTripUseCase.execute(tripId, user.id);
    return { success: true, data: trip };
  }
}
```

#### 2. Observer Pattern (Live GPS Events)

```typescript
// src/domain/events/gps-event.handler.ts

// Multiple systems react to GPS pings from trucks:
interface GPSEventHandler {
  handle(event: GPSPingEvent): Promise<void>;
}

class LiveTrackingHandler implements GPSEventHandler {
  async handle(event: GPSPingEvent) {
    // Push to customer's WebSocket — "Your truck is here"
    await this.wsGateway.emit(event.tripId, {
      lat: event.lat,
      lng: event.lng,
      speed: event.speed,
      timestamp: event.timestamp,
    });
  }
}

class ETACalculator implements GPSEventHandler {
  async handle(event: GPSPingEvent) {
    // Recalculate ETA based on current position + traffic
    const eta = await this.mapsService.getETA(
      { lat: event.lat, lng: event.lng },
      event.destination,
    );
    await this.tripRepo.updateETA(event.tripId, eta);
  }
}

class GeofenceChecker implements GPSEventHandler {
  async handle(event: GPSPingEvent) {
    // Check if truck entered/exited warehouse zone
    const geofences = await this.geofenceRepo.findNear(event.lat, event.lng);
    for (const fence of geofences) {
      if (this.isInside(event, fence)) {
        await this.notifier.send(fence.ownerId, `Truck arrived at ${fence.name}`);
      }
    }
  }
}

class FuelMonitor implements GPSEventHandler {
  async handle(event: GPSPingEvent) {
    // Detect unusual stops (possible fuel theft)
    if (event.speed === 0 && !this.isAtKnownStop(event)) {
      await this.alertService.raiseAlert(event.vehicleId, 'UNEXPECTED_STOP');
    }
  }
}
```

#### 3. Strategy Pattern (Pricing Models)

```typescript
// Different clients have different pricing:

interface PricingStrategy {
  calculate(distanceKm: number, weightTons: number, vehicleType: string): number;
}

class PerKmPricing implements PricingStrategy {
  // Standard: ₹X per km
  calculate(distanceKm: number, weightTons: number, vehicleType: string): number {
    const rates = { 'mini-truck': 18, 'truck': 25, 'trailer': 35 };
    return distanceKm * (rates[vehicleType] || 25);
  }
}

class PerTonPricing implements PricingStrategy {
  // Bulk goods: ₹X per ton per km
  calculate(distanceKm: number, weightTons: number, vehicleType: string): number {
    const ratePerTonKm = 3.5;
    return distanceKm * weightTons * ratePerTonKm;
  }
}

class FixedRoutePricing implements PricingStrategy {
  // Contract clients: fixed price for known routes
  private routePrices = new Map([
    ['PUNE-MUMBAI', 8500],
    ['DELHI-JAIPUR', 12000],
    ['CHENNAI-BANGALORE', 15000],
  ]);

  calculate(distanceKm: number, weightTons: number, vehicleType: string): number {
    // Fixed price regardless of actual distance/weight
    return 0; // Looked up separately by route
  }
  
  getFixedPrice(routeKey: string): number {
    return this.routePrices.get(routeKey) || 0;
  }
}

// Client configuration determines which strategy:
class TripPricingService {
  async calculateFare(trip: Trip, client: Client): Promise<number> {
    const strategy = this.getStrategy(client.pricingModel);
    return strategy.calculate(trip.distanceKm, trip.weightTons, trip.vehicleType);
  }

  private getStrategy(model: string): PricingStrategy {
    switch (model) {
      case 'per_km': return new PerKmPricing();
      case 'per_ton': return new PerTonPricing();
      case 'fixed_route': return new FixedRoutePricing();
      default: return new PerKmPricing();
    }
  }
}
```

---

## Summary: Patterns × Real Systems

| Pattern | Razorpay | Zomato | Uber/Ola | PhonePe | Smart Freight |
|---------|----------|--------|----------|---------|---------------|
| **Strategy** | Payment methods | — | Vehicle types | — | Pricing models |
| **Observer** | Webhooks | Order tracking | Live GPS | — | GPS events |
| **State** | — | Order lifecycle | Ride states | Txn states | Trip lifecycle |
| **Factory** | — | — | Ride creation | — | Vehicle assignment |
| **Decorator** | — | Dynamic pricing | Surge pricing | — | Cost add-ons |
| **Command** | — | Order operations | — | — | Trip actions |
| **Template Method** | — | — | — | UPI flow | — |
| **SOLID** | ✅ All 5 | ✅ All 5 | ✅ All 5 | ✅ All 5 | ✅ All 5 |
| **Concurrency** | Idempotency | Order locks | Driver matching | Double-spend prevention | GPS dedup |
| **Clean Architecture** | Layered | Layered | Hexagonal | Layered | Clean + DDD |

---

## Key Interview Takeaways

### When interviewer asks "Design X", think:
1. **What are the states?** → State Pattern (Order, Ride, Transaction)
2. **What varies independently?** → Strategy Pattern (payment methods, pricing, vehicle types)
3. **Who needs to know when something changes?** → Observer Pattern (tracking, notifications)
4. **What's the step-by-step algorithm?** → Template Method (transaction flows)
5. **How do I prevent corruption?** → Concurrency (optimistic locks, idempotency)
6. **How do I add features without breaking things?** → OCP + Decorator

### The "Indian Tech" Angle
- UPI idempotency is a MUST-know for any fintech interview in India
- State machines for order/ride/trip lifecycle come up in every Swiggy/Zomato/Ola interview
- Surge pricing (Decorator) is a classic Uber interview question
- Multi-tenant pricing (Strategy) is common in B2B SaaS interviews

