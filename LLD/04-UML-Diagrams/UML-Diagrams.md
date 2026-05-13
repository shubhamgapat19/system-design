# UML Diagrams

UML (Unified Modeling Language) is a **standardized visual language** for modeling software systems. In LLD interviews, you draw these diagrams to communicate your design before writing code.

---

## Why UML?

| Without UML | With UML |
|-------------|----------|
| "Let me explain my 20 classes verbally..." | One diagram shows the entire structure |
| Ambiguous relationships between objects | Clear arrows: inheritance, composition, dependency |
| Interviewer confused about your flow | Sequence diagram shows exact call order |
| No shared vocabulary | Industry-standard notation everyone understands |

---

## The 3 Diagrams You MUST Know for Interviews

| Diagram | Shows | When to Use |
|---------|-------|-------------|
| **Class Diagram** | Structure — classes, attributes, methods, relationships | "Design the classes for X system" |
| **Sequence Diagram** | Behavior — interaction between objects over time | "Walk me through what happens when user does Y" |
| **Use-Case Diagram** | Requirements — what actors can do in the system | "What are the main features of this system?" |

---


- **UML:** A standardized visual modeling language used to specify, visualize, construct, and document the artifacts of a software system.
- **Class Diagram:** A structural UML diagram that shows classes, their attributes, methods, and the relationships (association, inheritance, composition, aggregation) between them.
- **Sequence Diagram:** A behavioral UML diagram that shows how objects interact in a particular sequence of time, depicting the order of messages exchanged.
- **Use-Case Diagram:** A behavioral UML diagram that captures the functional requirements of a system by showing actors (users/systems) and the use cases (actions) they can perform.
- **Association:** A relationship where one class uses or is connected to another (e.g., Driver drives Truck).
- **Aggregation:** A "has-a" relationship where the child can exist independently of the parent (e.g., Fleet has Trucks — trucks exist without the fleet).
- **Composition:** A strong "has-a" relationship where the child cannot exist without the parent (e.g., Order has OrderItems — items die when order is deleted).
- **Inheritance (Generalization):** An "is-a" relationship where a child class inherits from a parent class.
- **Dependency:** A weak relationship where one class uses another temporarily (e.g., as a method parameter).
- **Interface Realization:** A class implements an interface (contract).

---

---

# 1. CLASS DIAGRAMS

> **Show the static structure of your system — classes, their contents, and how they relate.**

This is the **#1 most important diagram** in LLD interviews. You'll draw this for every design problem.

---

## Class Notation

```mermaid
classDiagram
    class ClassName {
        +publicAttribute: Type
        -privateAttribute: Type
        #protectedAttribute: Type
        ~packageAttribute: Type
        +publicMethod(param: Type) ReturnType
        -privateMethod() void
        #protectedMethod()* ReturnType
    }
```

### Visibility Symbols

| Symbol | Meaning | Python Equivalent |
|--------|---------|-------------------|
| `+` | Public | `self.name` |
| `-` | Private | `self.__name` |
| `#` | Protected | `self._name` |
| `~` | Package/Internal | Module-level |

### Stereotypes

| Stereotype | Meaning |
|------------|---------|
| `<<abstract>>` | Abstract class (can't instantiate) |
| `<<interface>>` | Interface (only method signatures) |
| `<<enum>>` | Enumeration |
| `<<static>>` | Static/class-level |

---

## Relationship Types

```mermaid
classDiagram
    class A
    class B
    class C
    class D
    class E
    class F
    class G
    class H

    A --|> B : Inheritance (is-a)
    C ..|> D : Interface Realization (implements)
    E --> F : Association (uses)
    G o-- H : Aggregation (has-a, weak)
```

```mermaid
classDiagram
    class P
    class Q
    class R
    class S

    P *-- Q : Composition (has-a, strong)
    R ..> S : Dependency (temporary use)
```

### Relationship Cheat Sheet

| Arrow | Name | Meaning | Example | Memory Trick |
|-------|------|---------|---------|--------------|
| `──▷` (solid + triangle) | **Inheritance** | "is-a" | `Dog ──▷ Animal` | Solid = strong bond |
| `··▷` (dashed + triangle) | **Realization** | "implements" | `Razorpay ··▷ PaymentGateway` | Dashed = promise to fulfill |
| `──>` (solid + arrow) | **Association** | "uses/knows" | `Driver ──> Truck` | Simple connection |
| `◇──` (hollow diamond) | **Aggregation** | "has-a" (weak) | `Fleet ◇── Truck` | Hollow = truck can leave |
| `◆──` (filled diamond) | **Composition** | "has-a" (strong) | `Order ◆── OrderItem` | Filled = dies together |
| `··>` (dashed + arrow) | **Dependency** | "temporarily uses" | `Controller ··> Logger` | Dashed = weak/temporary |

### Multiplicity (Cardinality)

| Notation | Meaning |
|----------|---------|
| `1` | Exactly one |
| `0..1` | Zero or one (optional) |
| `*` or `0..*` | Zero or many |
| `1..*` | One or many |
| `3..5` | Between 3 and 5 |

---

## Full Class Diagram Example: Logistics Trip System

```mermaid
classDiagram
    class Trip {
        -String trip_id
        -DateTime created_at
        -TripStatus status
        +assign_driver(driver: Driver)
        +start()
        +complete()
        +get_fare() float
    }

    class Driver {
        -String driver_id
        -String name
        -String phone
        -float rating
        +accept_trip(trip: Trip)
        +update_location(lat: float, lng: float)
    }

    class Truck {
        -String registration_no
        -String model
        -float capacity_tons
        -TruckStatus status
        +is_available() bool
    }

    class Route {
        -String origin
        -String destination
        -list~String~ waypoints
        -float distance_km
        +calculate_eta() DateTime
    }

    class Payment {
        -String payment_id
        -float amount
        -PaymentStatus status
        +charge()
        +refund()
    }

    class TripStatus {
        <<enum>>
        PENDING
        ASSIGNED
        IN_TRANSIT
        COMPLETED
        CANCELLED
    }

    class TruckStatus {
        <<enum>>
        AVAILABLE
        IN_TRANSIT
        MAINTENANCE
    }

    class PaymentStatus {
        <<enum>>
        PENDING
        COMPLETED
        FAILED
        REFUNDED
    }

    Trip "1" --> "1" Driver : assigned to
    Trip "1" --> "1" Truck : uses
    Trip "1" *-- "1" Route : has
    Trip "1" *-- "1" Payment : has
    Driver "1" --> "1" Truck : drives
    Trip --> TripStatus
    Truck --> TruckStatus
    Payment --> PaymentStatus
```

### How to Read This Diagram

1. **Trip** is the central entity — it connects drivers, trucks, routes, and payments
2. **Composition (◆)** — Route and Payment can't exist without a Trip (they die together)
3. **Association (→)** — Trip knows about Driver, but Driver can exist independently
4. **Enums** — Status fields are finite state machines

---

## Class Diagram: Drawing Process (Interview Steps)

```
Step 1: Identify NOUNS from requirements → These become classes
Step 2: Identify VERBS → These become methods
Step 3: Identify ADJECTIVES/DATA → These become attributes
Step 4: Draw relationships between classes
Step 5: Add multiplicity (1, *, 0..1)
Step 6: Mark visibility (+, -, #)
```

### Example Thought Process

**Problem:** "Design a parking lot system"

| Step | Extract | Result |
|------|---------|--------|
| Nouns | Parking lot, floor, spot, vehicle, ticket | Classes: `ParkingLot`, `Floor`, `Spot`, `Vehicle`, `Ticket` |
| Verbs | park, unpark, pay, find spot | Methods: `park()`, `unpark()`, `pay()`, `find_available_spot()` |
| Data | spot number, vehicle type, entry time | Attributes: `spot_no`, `vehicle_type`, `entry_time` |
| Relations | Lot has floors, floor has spots | `ParkingLot ◆── Floor ◆── Spot` |
| Multiplicity | One lot has many floors | `ParkingLot "1" *-- "1..*" Floor` |

---

---

# 2. SEQUENCE DIAGRAMS

> **Show how objects interact over time — the exact order of method calls and responses.**

Interviewers ask: "Walk me through what happens when a user books a trip." This is your answer — visually.

---

## Notation

```mermaid
sequenceDiagram
    participant A as Actor/Object
    participant B as Another Object
    
    A->>B: Synchronous call (solid arrow)
    B-->>A: Return response (dashed arrow)
    A-)B: Async message (open arrow)
    
    Note over A,B: Notes span objects
    
    alt condition is true
        A->>B: Do this
    else condition is false
        A->>B: Do that
    end
    
    loop every 5 seconds
        A->>B: Poll status
    end
    
    opt optional behavior
        A->>B: Only if needed
    end
```

### Arrow Types

| Arrow | Meaning |
|-------|---------|
| `─▶` (solid, filled) | Synchronous call (caller waits) |
| `──▶` (dashed, filled) | Return/response |
| `─▷` (solid, open) | Asynchronous message (fire & forget) |
| `──▷` (dashed, open) | Async response/callback |

### Fragments (Combined Frames)

| Fragment | Meaning | Use When |
|----------|---------|----------|
| `alt / else` | If-else branching | Different paths based on condition |
| `opt` | Optional | Step happens only sometimes |
| `loop` | Repetition | Polling, retries, batch processing |
| `par` | Parallel | Multiple things happen simultaneously |
| `break` | Break out | Error/exception exits the flow |

---

## Full Sequence Diagram Example: Trip Booking Flow

```mermaid
sequenceDiagram
    actor Customer
    participant API as BookingAPI
    participant TS as TripService
    participant DM as DriverMatcher
    participant PS as PaymentService
    participant NS as NotificationService
    participant DB as Database

    Customer->>API: POST /trips/book {origin, dest, cargo}
    API->>TS: create_trip(origin, dest, cargo)
    TS->>DB: INSERT trip (status=PENDING)
    DB-->>TS: trip_id

    TS->>DM: find_available_driver(origin, vehicle_type)
    DM->>DB: SELECT drivers WHERE available=true
    DB-->>DM: [driver_1, driver_2, driver_3]
    DM->>DM: rank by rating, distance
    DM-->>TS: best_driver

    alt driver found
        TS->>DB: UPDATE trip SET driver_id, status=ASSIGNED
        TS->>PS: hold_payment(trip_id, estimated_fare)
        PS-->>TS: hold_id

        TS-->>API: {trip_id, driver, eta, fare}
        API-->>Customer: 201 Created {trip details}

        par Send notifications
            NS-)Customer: SMS "Trip confirmed, driver Ramesh arriving"
            NS-)DM: Push "New trip assigned: Mumbai→Pune"
        end
    else no driver available
        TS->>DB: UPDATE trip SET status=CANCELLED
        TS-->>API: {error: "No drivers available"}
        API-->>Customer: 503 Service Unavailable
    end
```

### How to Read This Diagram

1. **Time flows top → down** — first thing at top, last at bottom
2. **Lifelines** (vertical dashed lines) show object's existence over time
3. **Arrows** show messages/calls between objects
4. **`alt` block** shows branching — driver found vs not found
5. **`par` block** shows parallel notifications happening simultaneously

---

## Sequence Diagram: Drawing Process

```
Step 1: Identify the TRIGGER (user action or API call)
Step 2: List all PARTICIPANTS (objects/services involved)
Step 3: Walk through the HAPPY PATH first (everything works)
Step 4: Add ERROR/ALTERNATIVE paths (alt/else blocks)
Step 5: Mark async operations (notifications, background jobs)
Step 6: Add return values on dashed arrows
```

---

## Another Example: Payment Flow

```mermaid
sequenceDiagram
    actor User
    participant API as PaymentAPI
    participant OS as OrderService
    participant PG as PaymentGateway
    participant RZ as Razorpay
    participant DB as Database
    participant NS as NotificationService

    User->>API: POST /payments {order_id, amount, method}
    API->>OS: validate_order(order_id)
    OS->>DB: SELECT order WHERE id=order_id
    DB-->>OS: order_details
    
    alt order not found or already paid
        OS-->>API: ERROR "Invalid order"
        API-->>User: 400 Bad Request
    else order valid
        OS-->>API: order_confirmed
        API->>PG: initiate_payment(amount, method)
        PG->>RZ: create_order(amount)
        RZ-->>PG: razorpay_order_id
        PG-->>API: payment_link

        API-->>User: 200 {payment_link, razorpay_order_id}
        
        Note over User,RZ: User completes payment on Razorpay checkout
        
        RZ-)API: webhook: payment.captured {payment_id, status}
        API->>PG: verify_signature(webhook_data)
        PG-->>API: signature_valid
        
        API->>DB: UPDATE payment SET status=COMPLETED
        API->>OS: mark_order_paid(order_id)
        
        par Post-payment actions
            NS-)User: SMS "Payment ₹{amount} received"
            OS-)OS: trigger_fulfillment(order_id)
        end
    end
```

---

---

# 3. USE-CASE DIAGRAMS

> **Show WHAT the system does from the user's perspective — actors and their actions.**

Use-case diagrams are drawn first during requirements gathering. They answer: "Who uses this system and what can they do?"

---

## Notation

```mermaid
graph LR
    subgraph System Boundary
        UC1((Use Case 1))
        UC2((Use Case 2))
        UC3((Use Case 3))
    end
    
    Actor1[🧑 Actor] --> UC1
    Actor1 --> UC2
    Actor2[🧑 Actor 2] --> UC3
    UC1 -.->|<<include>>| UC3
    UC2 -.->|<<extend>>| UC3
```

### Elements

| Element | Symbol | Meaning |
|---------|--------|---------|
| **Actor** | Stick figure | External entity that interacts with system (user, admin, external API) |
| **Use Case** | Oval/ellipse | A specific action/feature the system provides |
| **System Boundary** | Rectangle | Defines what's inside vs outside the system |
| **Association** | Solid line | Actor can perform this use case |
| **Include** | Dashed arrow + `<<include>>` | Use case ALWAYS includes another (mandatory sub-step) |
| **Extend** | Dashed arrow + `<<extend>>` | Use case OPTIONALLY extends another (conditional) |
| **Generalization** | Solid arrow + triangle | Specialized actor inherits from general actor |

### Include vs Extend

| | `<<include>>` | `<<extend>>` |
|---|---|---|
| **When** | ALWAYS happens | SOMETIMES happens |
| **Direction** | Base → Included | Extension → Base |
| **Example** | "Book Trip" includes "Authenticate" | "Book Trip" extended by "Apply Coupon" |
| **Analogy** | Every ATM withdrawal includes PIN verification | ATM withdrawal optionally prints receipt |

---

## Full Use-Case Diagram: Smart Freight Platform

```mermaid
graph TB
    subgraph Smart Freight System
        UC1((Book Trip))
        UC2((Track Shipment))
        UC3((Make Payment))
        UC4((Rate Driver))
        UC5((Manage Fleet))
        UC6((View Reports))
        UC7((Assign Driver))
        UC8((Update Trip Status))
        UC9((Manage Users))
        UC10((Authenticate))
        UC11((Apply Coupon))
        UC12((Generate Invoice))
    end

    Customer[🧑 Customer] --> UC1
    Customer --> UC2
    Customer --> UC3
    Customer --> UC4

    Driver[🚛 Driver] --> UC8
    Driver --> UC2

    Admin[👤 Admin] --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC9

    UC1 -.->|<<include>>| UC10
    UC3 -.->|<<include>>| UC10
    UC1 -.->|<<extend>>| UC11
    UC3 -.->|<<include>>| UC12
```

### Actors Identified

| Actor | Role | Key Use Cases |
|-------|------|---------------|
| **Customer** | Shipper who books freight | Book Trip, Track, Pay, Rate |
| **Driver** | Truck driver who fulfills trips | Update Status, Track |
| **Admin** | Platform operator | Manage Fleet, Reports, Users |
| **(System) Razorpay** | External payment system | Process Payment (external actor) |
| **(System) GPS API** | External tracking | Provide location data |

---

## Use-Case Description Template

For each use case in interviews, describe it briefly:

```
Use Case: Book Trip
───────────────────
Actor: Customer
Precondition: Customer is authenticated
Trigger: Customer clicks "Book Now"

Main Flow (Happy Path):
1. Customer enters origin, destination, cargo details
2. System calculates route and estimated fare
3. System shows available time slots
4. Customer confirms booking
5. System assigns driver
6. System sends confirmation

Alternative Flows:
- 3a. No slots available → Show next available date
- 5a. No driver available → Queue request, notify customer

Postcondition: Trip created with status PENDING/ASSIGNED
```

---

## Use-Case Diagram: Drawing Process

```
Step 1: Identify ACTORS — Who interacts with the system? (humans + external systems)
Step 2: Identify USE CASES — What can each actor DO? (use verb phrases)
Step 3: Draw SYSTEM BOUNDARY — What's inside your system vs external?
Step 4: Connect actors to their use cases (solid lines)
Step 5: Add <<include>> for mandatory sub-steps
Step 6: Add <<extend>> for optional features
```

---

---

# Bonus: Activity Diagram (Quick Overview)

> **Shows the flow of control — like a flowchart but with support for parallel and branching flows.**

Useful for showing business processes and workflows.

```mermaid
flowchart TD
    A([Start]) --> B{Customer authenticated?}
    B -->|No| C[Show Login Page]
    C --> B
    B -->|Yes| D[Enter Trip Details]
    D --> E[Calculate Route & Fare]
    E --> F{Fare accepted?}
    F -->|No| G([End - Cancelled])
    F -->|Yes| H[Process Payment]
    H --> I{Payment success?}
    I -->|No| J[Show Error, Retry]
    J --> H
    I -->|Yes| K[Assign Driver]
    K --> L[Send Confirmations]
    L --> M([End - Trip Created])
```

---

---

# Common Mistakes

## ❌ BAD: Missing multiplicity

```
Trip ──── Driver
```
How many drivers per trip? How many trips per driver? Nobody knows!

## ✅ GOOD: Always add multiplicity

```
Trip "1" ──── "1" Driver       (one trip, one driver)
Driver "1" ──── "0..*" Trip    (one driver, many trips over time)
```

---

## ❌ BAD: Every relationship is Association

```
Order ──── OrderItem ──── Product ──── Category
```
Are these all the same strength? Does OrderItem survive without Order?

## ✅ GOOD: Use correct relationship type

```
Order ◆── OrderItem     (Composition — item dies with order)
OrderItem ──> Product   (Association — product exists independently)
Product ──> Category    (Association — category exists independently)
```

---

## ❌ BAD: Sequence diagram without return arrows

```
User → API → Service → DB
```
What comes back? Did it succeed? What data was returned?

## ✅ GOOD: Show both calls AND returns

```
User → API: POST /book
API → DB: INSERT
DB --> API: trip_id
API --> User: 201 {trip_id}
```

---

## ❌ BAD: Use-case diagram with implementation details

```
((Connect to PostgreSQL))
((Execute SQL Query))
((Parse JSON Response))
```

## ✅ GOOD: Use cases are USER-LEVEL goals

```
((Book Trip))
((Track Shipment))
((Make Payment))
```

---

## ❌ BAD: Too many classes in one diagram

50 classes with arrows everywhere = unreadable spaghetti

## ✅ GOOD: Focus on core entities (5-8 classes per diagram)

Show the most important relationships. Use separate diagrams for different subsystems.

---

# Quick Reference Table

| Mistake | Fix |
|---------|-----|
| Missing multiplicity | Always add (1, *, 0..1, 1..*) |
| All relationships same type | Choose: Association, Aggregation, Composition, Dependency |
| No return arrows in sequence | Show response on dashed arrows |
| Implementation details in use cases | Keep use cases at user-goal level |
| 50-class mega diagram | 5-8 classes per diagram, split by subsystem |
| No visibility markers | Add +, -, # to all attributes/methods |

---

# Quick Cheat Sheet

| Concept | One-liner | Key Point |
|---------|-----------|-----------|
| **Class Diagram** | Static structure of classes & relationships | Draw for EVERY LLD problem |
| **Sequence Diagram** | Object interactions over time | Show the "what happens when" flow |
| **Use-Case Diagram** | Actor + actions overview | Requirements gathering, system scope |
| **Composition (◆)** | Strong has-a, child dies with parent | Order ◆── OrderItem |
| **Aggregation (◇)** | Weak has-a, child survives | Fleet ◇── Truck |
| **Association (→)** | Uses/knows relationship | Driver → Truck |
| **`<<include>>`** | Mandatory sub-step | Always happens |
| **`<<extend>>`** | Optional feature | Sometimes happens |
| **Multiplicity** | How many of each | 1, 0..1, *, 1..* |

---

# Interview Tips for UML

1. **Always start with a class diagram** — even if not asked, it shows you think structurally
2. **Use sequence diagrams for "walk me through"** questions — shows you understand the flow
3. **Don't over-engineer** — 5-8 classes is enough for most problems
4. **Name things clearly** — `TripService` not `TS`, `assign_driver()` not `do_stuff()`
5. **Draw relationships AFTER classes** — first get the nouns right, then connect them
6. **Explain as you draw** — "Trip HAS a Route (composition because route can't exist without trip)"

