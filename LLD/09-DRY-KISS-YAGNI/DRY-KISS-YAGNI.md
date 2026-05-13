# DRY, KISS, YAGNI — Code-Level Design Principles

These three principles are the **daily habits** of good developers. They're not about architecture or patterns — they're about the decisions you make on every single line of code.

---

## At a Glance

| Principle | Full Form | One-liner |
|-----------|-----------|-----------|
| **DRY** | Don't Repeat Yourself | Every piece of knowledge should have one, single representation |
| **KISS** | Keep It Simple, Stupid | The simplest solution that works is the best solution |
| **YAGNI** | You Ain't Gonna Need It | Don't build it until you actually need it |

--

- **DRY (Don't Repeat Yourself):** Every piece of knowledge or logic must have a single, unambiguous, authoritative representation within a system — duplicated code means duplicated bugs.
- **KISS (Keep It Simple, Stupid):** Systems work best when they are kept simple; unnecessary complexity should be avoided in design and implementation.
- **YAGNI (You Ain't Gonna Need It):** Don't implement functionality until it's actually needed — premature features add maintenance burden without delivering value.
- **WET (Write Everything Twice):** The anti-pattern of DRY — code that's duplicated across multiple locations, making changes error-prone.
- **Premature Abstraction:** Creating abstractions (interfaces, base classes, utilities) before there's evidence of reuse — often worse than duplication.
- **Accidental Complexity:** Complexity introduced by the solution itself (bad code, over-engineering) as opposed to the problem's inherent complexity.
- **Essential Complexity:** Complexity that is inherent to the problem being solved — cannot be eliminated, only managed.

---

---

# 1. DRY — Don't Repeat Yourself

> **Every piece of knowledge should exist in ONE place. Change it once, it updates everywhere.**

---

## What DRY Actually Means

DRY is NOT just "don't copy-paste code." It's about **knowledge duplication**:

| Type | Example |
|------|---------|
| **Code duplication** | Same validation logic in 3 controllers |
| **Data duplication** | Customer name stored in `customers` AND `trips` tables |
| **Logic duplication** | Fare calculation formula in frontend AND backend |
| **Documentation duplication** | API behavior described in code comments AND wiki |

---

## ❌ BAD: WET Code (Violates DRY)

```typescript
// trips.controller.ts
@Post()
async createTrip(@Body() dto: CreateTripDto) {
  // Validation duplicated everywhere!
  if (!dto.origin || dto.origin.trim() === '') {
    throw new BadRequestException('Origin is required');
  }
  if (!dto.destination || dto.destination.trim() === '') {
    throw new BadRequestException('Destination is required');
  }
  if (dto.cargoWeightTons <= 0 || dto.cargoWeightTons > 25) {
    throw new BadRequestException('Weight must be between 0 and 25 tons');
  }
  // ... create trip
}

// trips.service.ts (SAME validation repeated!)
async updateTrip(id: string, dto: UpdateTripDto) {
  if (!dto.origin || dto.origin.trim() === '') {
    throw new BadRequestException('Origin is required');
  }
  if (!dto.destination || dto.destination.trim() === '') {
    throw new BadRequestException('Destination is required');
  }
  if (dto.cargoWeightTons <= 0 || dto.cargoWeightTons > 25) {
    throw new BadRequestException('Weight must be between 0 and 25 tons');
  }
  // ... update trip
}
```

**Problems:**
- Fix a bug in validation? Must find and fix in 2+ places
- Add a new rule? Must add in 2+ places
- Miss one spot? Inconsistent behavior

---

## ✅ GOOD: DRY Code

```typescript
// dto/create-trip.dto.ts — validation defined ONCE using class-validator
import { IsNotEmpty, IsString, Min, Max } from 'class-validator';

export class CreateTripDto {
  @IsNotEmpty({ message: 'Origin is required' })
  @IsString()
  origin: string;

  @IsNotEmpty({ message: 'Destination is required' })
  @IsString()
  destination: string;

  @Min(0.1, { message: 'Weight must be at least 0.1 tons' })
  @Max(25, { message: 'Weight must not exceed 25 tons' })
  cargoWeightTons: number;
}

// Controller — zero validation code (handled by NestJS ValidationPipe)
@Post()
async createTrip(@Body() dto: CreateTripDto) {
  return this.tripsService.createTrip(dto);  // Clean!
}
```

---

## More DRY Examples

### Fare Calculation (extract to one place)

```typescript
// ❌ BAD — formula repeated in 3 files
// trips.service.ts
const fare = distance * 15 + weight * 200 + (isExpress ? 500 : 0);

// billing.service.ts  
const fare = distance * 15 + weight * 200 + (isExpress ? 500 : 0);

// invoice.service.ts
const fare = distance * 15 + weight * 200 + (isExpress ? 500 : 0);


// ✅ GOOD — one source of truth
// pricing/fare-calculator.ts
export class FareCalculator {
  static calculate(distance: number, weight: number, isExpress: boolean): number {
    const baseFare = distance * 15;
    const weightCharge = weight * 200;
    const expressSurcharge = isExpress ? 500 : 0;
    return baseFare + weightCharge + expressSurcharge;
  }
}

// Everyone uses FareCalculator.calculate() — change once, updates everywhere
```

### Constants (extract magic numbers)

```typescript
// ❌ BAD — magic numbers scattered
if (weight > 25) throw new Error('Too heavy');
if (rating < 3.0) markInactive();
if (retries > 3) giveUp();

// ✅ GOOD — constants in one place
// constants/business-rules.ts
export const MAX_CARGO_WEIGHT_TONS = 25;
export const MIN_DRIVER_RATING = 3.0;
export const MAX_RETRY_ATTEMPTS = 3;

// Usage
if (weight > MAX_CARGO_WEIGHT_TONS) throw new Error('Too heavy');
```

---

## When DRY Goes Wrong (Over-DRYing)

```typescript
// ❌ OVER-DRY — forcing unrelated things to share code
function formatEntity(entity: any, type: 'trip' | 'driver' | 'payment') {
  if (type === 'trip') return `Trip: ${entity.origin} → ${entity.destination}`;
  if (type === 'driver') return `Driver: ${entity.name} (${entity.rating}★)`;
  if (type === 'payment') return `Payment: ₹${entity.amount}`;
}
// This function has 3 responsibilities! Not actually the same knowledge.

// ✅ BETTER — duplication is OK when things are coincidentally similar
formatTrip(trip: Trip): string { return `Trip: ${trip.origin} → ${trip.destination}`; }
formatDriver(driver: Driver): string { return `Driver: ${driver.name} (${driver.rating}★)`; }
formatPayment(payment: Payment): string { return `Payment: ₹${payment.amount}`; }
```

### The Rule of Three

> Don't abstract until you see the **same pattern three times**. Two occurrences might be coincidence.

---

---

# 2. KISS — Keep It Simple, Stupid

> **The simplest solution that works is the best solution. Complexity is the enemy.**

---

## What KISS Means

- Fewer lines of code = fewer bugs
- Simple code = easier to debug, review, and modify
- If a junior developer can't understand it in 30 seconds, it's too complex
- Choose boring technology over clever technology

---

## ❌ BAD: Over-Engineered (Violates KISS)

```typescript
// Task: Check if a trip is active
// Over-engineered solution

interface IStatusChecker<T> {
  check(entity: T): boolean;
}

class TripStatusCheckerFactory {
  static create(strategy: 'active' | 'completed' | 'cancelled'): IStatusChecker<Trip> {
    switch (strategy) {
      case 'active':
        return new ActiveTripChecker();
      case 'completed':
        return new CompletedTripChecker();
      case 'cancelled':
        return new CancelledTripChecker();
    }
  }
}

class ActiveTripChecker implements IStatusChecker<Trip> {
  check(trip: Trip): boolean {
    return ['pending', 'assigned', 'in_transit'].includes(trip.status);
  }
}

// Usage (20 lines of abstraction for a simple check)
const checker = TripStatusCheckerFactory.create('active');
const isActive = checker.check(trip);
```

## ✅ GOOD: Simple and Clear (KISS)

```typescript
// Task: Check if a trip is active
function isTripActive(trip: Trip): boolean {
  return ['pending', 'assigned', 'in_transit'].includes(trip.status);
}

// Usage
const isActive = isTripActive(trip);
```

**Same result. 3 lines vs 20+ lines. Which would you rather debug at 2 AM?**

---

## More KISS Examples

### Simple Conditional

```typescript
// ❌ COMPLEX — nested ternary (clever but unreadable)
const label = trip.status === 'completed' ? 'Done' : trip.status === 'in_transit' ? 'Moving' : trip.status === 'assigned' ? 'Ready' : 'Waiting';

// ✅ SIMPLE — obvious and scannable
function getTripLabel(status: TripStatus): string {
  switch (status) {
    case 'completed': return 'Done';
    case 'in_transit': return 'Moving';
    case 'assigned': return 'Ready';
    default: return 'Waiting';
  }
}
```

### Data Transformation

```typescript
// ❌ COMPLEX — reduce when map is simpler
const tripNames = trips.reduce((acc, trip) => {
  return [...acc, `${trip.origin} → ${trip.destination}`];
}, [] as string[]);

// ✅ SIMPLE — map is the right tool
const tripNames = trips.map(trip => `${trip.origin} → ${trip.destination}`);
```

### API Response

```typescript
// ❌ COMPLEX — generic response builder with type params
class ResponseBuilder<T, M extends Record<string, any>> {
  private data: T | null = null;
  private meta: M | null = null;
  private statusCode: number = 200;
  
  setData(data: T): this { this.data = data; return this; }
  setMeta(meta: M): this { this.meta = meta; return this; }
  setStatus(code: number): this { this.statusCode = code; return this; }
  build(): { data: T; meta: M; status: number } { /* ... */ }
}

// ✅ SIMPLE — just return an object
return { success: true, data: trip };
```

---

## KISS Decision Framework

Before writing code, ask:
1. **Can I explain this to a junior in one sentence?** If not → simplify
2. **Am I solving a problem that exists right now?** If not → YAGNI
3. **Would a simpler approach work?** If yes → use it
4. **Am I being clever or clear?** Always choose clear

---

---

# 3. YAGNI — You Ain't Gonna Need It

> **Don't build features, abstractions, or infrastructure until you have a proven need.**

---

## What YAGNI Means

- Don't add a caching layer before you have performance problems
- Don't create an interface when you only have one implementation
- Don't support 5 payment gateways when you only use Razorpay
- Don't build a plugin system when you have 0 plugins planned

---

## ❌ BAD: Building for Imaginary Future

```typescript
// "What if we need to support multiple databases someday?"
// You have ONE PostgreSQL database. You've had it for 2 years.

interface IDatabaseAdapter {
  connect(): Promise<void>;
  query(sql: string): Promise<any>;
  disconnect(): Promise<void>;
}

class PostgresAdapter implements IDatabaseAdapter { /* ... */ }
class MongoAdapter implements IDatabaseAdapter { /* ... */ }      // NEVER USED
class MySQLAdapter implements IDatabaseAdapter { /* ... */ }      // NEVER USED

class DatabaseFactory {
  static create(type: 'postgres' | 'mongo' | 'mysql'): IDatabaseAdapter {
    // You only ever pass 'postgres'
  }
}

// Result: 200 lines of code supporting databases you'll never use
// PLUS: you maintain and test code that serves nobody
```

## ✅ GOOD: Build What You Need Now

```typescript
// Just use Prisma with PostgreSQL directly
@Injectable()
export class TripsRepository {
  constructor(private prisma: PrismaService) {}
  
  async findById(id: string): Promise<Trip | null> {
    return this.prisma.trip.findUnique({ where: { id } });
  }
}

// IF (big if) you ever need MongoDB, refactor THEN. Not now.
```

---

## More YAGNI Violations

### Over-Configurable

```typescript
// ❌ YAGNI — configurable everything for a fixed business rule
class PricingEngine {
  constructor(
    private baseRatePerKm: number,      // Always 15
    private weightRatePerTon: number,    // Always 200
    private expressSurcharge: number,    // Always 500
    private nightSurcharge: number,      // Always 300
    private weekendMultiplier: number,   // Always 1.2
    private rainMultiplier: number,      // NEVER USED
    private festivalMultiplier: number,  // NEVER USED
    private loyaltyDiscount: number,     // NEVER USED
  ) {}
}

// ✅ YAGNI — just hardcode what you use
class PricingEngine {
  private static BASE_RATE_PER_KM = 15;
  private static WEIGHT_RATE_PER_TON = 200;
  private static EXPRESS_SURCHARGE = 500;
  
  calculate(distance: number, weight: number, isExpress: boolean): number {
    return distance * PricingEngine.BASE_RATE_PER_KM
      + weight * PricingEngine.WEIGHT_RATE_PER_TON
      + (isExpress ? PricingEngine.EXPRESS_SURCHARGE : 0);
  }
}
// When you ACTUALLY need rain multiplier, add it THEN.
```

### Premature Microservices

```typescript
// ❌ YAGNI — you have 100 users and 3 endpoints
//
// trip-service/
// driver-service/
// payment-service/
// notification-service/
// analytics-service/
// api-gateway/
// service-registry/
// config-server/
//
// Result: 8 repos, 8 deployments, network calls between everything,
// distributed debugging nightmares — for an app that could be one NestJS server

// ✅ YAGNI — monolith until you PROVE you need to split
// src/modules/trips/
// src/modules/drivers/
// src/modules/payments/
// src/modules/notifications/
// One deployment. Simple. Split when you hit 50K users and need independent scaling.
```

### Premature Abstraction

```typescript
// ❌ YAGNI — interface with one implementation
interface INotificationService {
  send(to: string, message: string): Promise<void>;
}

class SMSNotificationService implements INotificationService {
  async send(to: string, message: string): Promise<void> {
    await this.twilioClient.send(to, message);
  }
}

// You ONLY have SMS. No email. No push. No WhatsApp. Just SMS.
// The interface adds complexity with zero benefit RIGHT NOW.

// ✅ YAGNI — just the class, add interface when second impl appears
class NotificationService {
  async sendSMS(to: string, message: string): Promise<void> {
    await this.twilioClient.send(to, message);
  }
}

// When you add email notifications → THEN extract the interface
```

---

## The YAGNI Test

Before building something, ask:

| Question | If YES → | If NO → |
|----------|----------|---------|
| Is a user asking for this RIGHT NOW? | Build it | Don't build it |
| Will this fail without it TODAY? | Build it | Don't build it |
| Am I building this "just in case"? | Don't build it | — |
| Has this caused a real bug/outage? | Fix it | Don't preemptively solve |

---

---

# 4. HOW THEY WORK TOGETHER

> **DRY + KISS + YAGNI are complementary, not competing.**

---

## The Tension

| Situation | DRY says | KISS says | YAGNI says |
|-----------|----------|-----------|------------|
| Same code in 2 places | Extract it! | Only if it's simple | Only if both are stable |
| Want to add config for future | — | Keep it simple | Don't add it yet |
| Complex abstraction to avoid duplication | Extract it | Don't over-abstract | Is it needed now? |
| Building generic solution for one case | — | Specific > generic | Build for today |

---

## The Priority Order

```
1. YAGNI first  — Do I need this at all?
2. KISS second  — What's the simplest way?
3. DRY third    — Am I repeating knowledge?
```

**Why this order?**
- YAGNI prevents you from building unnecessary things
- KISS ensures what you build is simple
- DRY ensures what you build isn't duplicated

If you apply DRY first, you might abstract prematurely. If you apply KISS first, you might build something simple that you don't even need.

---

## Decision Example

**Scenario:** You need to send SMS when trip is created. Might need email later.

| Approach | Principle | Result |
|----------|-----------|--------|
| Build generic NotificationService with interface, factory, multiple implementations | Violates YAGNI + KISS | Over-engineered |
| Just call Twilio directly in TripService | Violates DRY (if SMS used elsewhere too) | Coupled but simple |
| **Create SMSService class. No interface. Used by TripService** | **YAGNI ✓ KISS ✓ DRY ✓** | **Right-sized** |

When you add email later:
1. Create EmailService
2. Extract INotificationService interface (now DRY makes sense because you have 2 implementations)
3. Both implement the interface

---

---

# 5. REAL-WORLD APPLICATION

> **How these principles apply to your daily code decisions.**

---

## Smart Freight Examples

| Decision | Wrong (Over-Engineered) | Right (DRY + KISS + YAGNI) |
|----------|------------------------|---------------------------|
| Trip validation | Generic validator framework | class-validator decorators on DTO |
| Error handling | Custom error hierarchy with 15 classes | 3-4 standard exceptions (BadRequest, NotFound, Conflict, Internal) |
| Config | Dynamic config service with hot-reload | `.env` + ConfigModule (NestJS built-in) |
| Logging | Custom logging framework | NestJS Logger or Winston with preset config |
| Auth | Custom auth system | Passport.js + JWT (battle-tested) |
| Deployment | Kubernetes cluster for 100 users | Single VPS + PM2 (scale when needed) |

---

## The Refactoring Trigger

Don't preemptively apply these principles. Apply them **when you feel pain**:

| Pain Signal | Principle to Apply | Action |
|-------------|-------------------|--------|
| Changed fare formula → missed one spot → bug | DRY | Extract FareCalculator |
| New dev can't understand the code | KISS | Simplify, remove cleverness |
| Spending days on features nobody uses | YAGNI | Delete unused code |
| Same bug appears in 3 places | DRY | Extract to single source |
| Architecture diagram needs 20 minutes to explain | KISS | Simplify architecture |
| "We might need this later" | YAGNI | Delete it. Build when needed. |

---

---

# Common Mistakes

## ❌ BAD: Premature abstraction (Wrong DRY)

```typescript
// Two functions are similar but serve DIFFERENT purposes
function formatTripForCustomer(trip: Trip): string {
  return `${trip.origin} → ${trip.destination} (₹${trip.fare})`;
}

function formatTripForDriver(trip: Trip): string {
  return `${trip.origin} → ${trip.destination} (${trip.cargoWeightTons}T)`;
}

// Someone applies DRY incorrectly:
function formatTrip(trip: Trip, audience: 'customer' | 'driver'): string {
  const route = `${trip.origin} → ${trip.destination}`;
  if (audience === 'customer') return `${route} (₹${trip.fare})`;
  if (audience === 'driver') return `${route} (${trip.cargoWeightTons}T)`;
}
// Now they're coupled — can't evolve independently!
```

## ✅ GOOD: Duplication is fine when things serve different purposes

Keep them separate. They'll likely diverge further over time (customer format might add ETA, driver format might add route details).

---

## ❌ BAD: Clever one-liners (Violates KISS)

```typescript
// "Look how clever I am!"
const activeTrips = trips.reduce((a, t) => (t.status !== 'completed' && t.status !== 'cancelled' ? [...a, t] : a), []);

// Three months later: "What does this do again?"
```

## ✅ GOOD: Readable > clever

```typescript
const activeTrips = trips.filter(trip => 
  trip.status !== 'completed' && trip.status !== 'cancelled'
);
```

---

## ❌ BAD: Gold plating (Violates YAGNI)

```typescript
// User asked for: "Show trip status"
// Developer built: Trip status + status history + status change audit log + 
//                  status change webhooks + status change email notifications +
//                  status change analytics events + custom status workflows

// User: "I just wanted to see if my truck arrived..."
```

## ✅ GOOD: Build exactly what's asked, expand when requested

```typescript
// V1: Just show status
async getTripStatus(tripId: string): Promise<TripStatus> {
  const trip = await this.tripRepo.findById(tripId);
  return trip.status;
}
// Ship it. Get feedback. Iterate.
```

---

# Quick Reference Table

| Mistake | Fix | Principle |
|---------|-----|-----------|
| Same logic in 3+ places | Extract to single function/class | DRY |
| Magic numbers scattered | Constants file | DRY |
| Nested ternary / one-liners | Simple if/switch | KISS |
| Generic framework for one use case | Direct implementation | KISS + YAGNI |
| Interface with one implementation | Just the class (add interface later) | YAGNI |
| Config for unused features | Hardcode, make configurable when needed | YAGNI |
| Premature microservices | Monolith first, split when needed | YAGNI + KISS |
| Forcing unrelated code to share | Separate functions (coincidental similarity ≠ duplication) | Know when NOT to DRY |

---

# Quick Cheat Sheet

| Principle | One-liner | Anti-Pattern | Rule of Thumb |
|-----------|-----------|-------------|---------------|
| **DRY** | One source of truth | WET (Write Everything Twice) | Rule of 3: abstract on 3rd repetition |
| **KISS** | Simplest solution wins | Over-engineering, clever code | Can a junior understand in 30 sec? |
| **YAGNI** | Build only what's needed now | Gold plating, "just in case" code | Is a user asking for this TODAY? |

---

# Priority Order for Decision Making

```
Step 1: YAGNI — "Do I even need this?"
         │
         ▼ YES, I need it
Step 2: KISS — "What's the simplest way?"
         │
         ▼ Got the simple version
Step 3: DRY — "Am I repeating something I already have?"
         │
         ▼ If yes, extract. If no, ship it.
```

---

# Interview Tips

1. **Don't over-engineer in interviews** — "I'll start simple and refactor when the need is proven"
2. **Mention trade-offs** — "This is slightly duplicated, but they serve different purposes so I'm keeping them separate"
3. **Show awareness** — "In production I'd extract this if it's used in 3+ places"
4. **YAGNI for architecture questions** — "I'd start with a monolith and split to microservices only when we hit scaling limits"
5. **KISS for coding questions** — favor readability over cleverness
