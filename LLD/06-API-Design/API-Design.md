# API Design

API Design is the art of **creating clean, predictable, and developer-friendly interfaces** for your services. A well-designed API is like a good UI — intuitive enough that you barely need documentation.

---

## Why API Design Matters?

| Bad API | Good API |
|---------|----------|
| `POST /doStuff` — what does this do? | `POST /trips` — creates a trip |
| Returns 200 for everything (even errors) | Correct HTTP status codes |
| Inconsistent naming (`getTrip`, `fetch_driver`) | Consistent conventions throughout |
| No versioning — breaking changes hit everyone | Versioned, backward compatible |
| No pagination — returns 10,000 records | Paginated, filtered, sorted |

---

## Core Concepts at a Glance

| Concept | Purpose |
|---------|---------|
| **REST Principles** | Standard conventions for resource-based APIs |
| **HTTP Methods** | CRUD mapping (GET, POST, PUT, PATCH, DELETE) |
| **Status Codes** | Communicate success/failure type |
| **Request/Response Design** | What goes in, what comes out |
| **Error Handling** | Consistent, informative error format |
| **Versioning** | Evolve API without breaking clients |
| **Pagination** | Handle large datasets efficiently |
| **Authentication** | Who is calling? |
| **Rate Limiting** | Prevent abuse |
| **Idempotency** | Safe to retry without side effects |

---

- **REST (Representational State Transfer):** An architectural style for distributed systems that uses stateless, resource-based communication over HTTP with standard methods (GET, POST, PUT, DELETE).
- **Resource:** Any entity/concept that can be identified by a URI (e.g., `/trips/123`, `/drivers`). Resources are nouns, not verbs.
- **Endpoint:** A specific URL + HTTP method combination that performs an action on a resource (e.g., `GET /trips/123`).
- **Idempotency:** The property where making the same request multiple times produces the same result as making it once (GET, PUT, DELETE are idempotent; POST is not).
- **HATEOAS:** Hypermedia As The Engine Of Application State — responses include links to related actions/resources, making the API self-discoverable.
- **Content Negotiation:** The process where client and server agree on the response format (JSON, XML) via `Accept` and `Content-Type` headers.
- **Pagination:** Breaking large result sets into smaller pages (offset-based or cursor-based) to reduce response size and improve performance.
- **Rate Limiting:** Restricting the number of API requests a client can make in a time window to prevent abuse and ensure fair usage.
- **API Gateway:** A single entry point that routes requests to appropriate microservices, handling cross-cutting concerns (auth, rate limiting, logging).
- **Idempotency Key:** A unique client-generated key sent with requests to ensure the server processes the operation only once, even if retried.

---

---

# 1. REST PRINCIPLES

> **Resources (nouns) + HTTP Methods (verbs) + Status Codes = RESTful API**

---

## The 6 REST Constraints

| # | Constraint | Meaning |
|---|-----------|---------|
| 1 | **Client-Server** | Client and server are independent; communicate via API |
| 2 | **Stateless** | Each request contains ALL information needed; no session state on server |
| 3 | **Cacheable** | Responses must declare if they're cacheable (via headers) |
| 4 | **Uniform Interface** | Consistent URL structure, HTTP methods, response format |
| 5 | **Layered System** | Client can't tell if connected directly to server or via proxy/gateway |
| 6 | **Code on Demand** (optional) | Server can send executable code to client (rarely used) |

---

## Resource Naming Conventions

### Rules

| Rule | ✅ Good | ❌ Bad |
|------|---------|--------|
| Use **nouns**, not verbs | `/trips` | `/getTrips`, `/createTrip` |
| Use **plural** nouns | `/drivers` | `/driver` |
| Use **kebab-case** | `/trip-stops` | `/tripStops`, `/trip_stops` |
| Hierarchical for nested resources | `/trips/123/stops` | `/getTripStops?tripId=123` |
| No trailing slash | `/trips` | `/trips/` |
| No file extensions | `/trips/123` | `/trips/123.json` |

### URL Structure

```
https://api.smartfreight.in/v1/trips/abc-123/stops?page=1&limit=10
|_____|  |___________________|  |_| |____| |_____| |______________|
scheme        host              ver resource  id    query params
```

---

## HTTP Methods → CRUD

| Method | CRUD | Action | Idempotent | Safe |
|--------|------|--------|-----------|------|
| `GET` | Read | Fetch resource(s) | ✅ | ✅ |
| `POST` | Create | Create new resource | ❌ | ❌ |
| `PUT` | Update (full) | Replace entire resource | ✅ | ❌ |
| `PATCH` | Update (partial) | Modify specific fields | ❌* | ❌ |
| `DELETE` | Delete | Remove resource | ✅ | ❌ |

- **Safe** = doesn't modify server state (read-only)
- **Idempotent** = calling N times = same result as calling once
- *PATCH can be made idempotent depending on implementation

---

## Complete CRUD Example: Trip Resource

```
GET    /v1/trips              → List all trips (with pagination)
GET    /v1/trips/:id          → Get single trip by ID
POST   /v1/trips              → Create a new trip
PUT    /v1/trips/:id          → Full update (replace all fields)
PATCH  /v1/trips/:id          → Partial update (change status only)
DELETE /v1/trips/:id          → Delete/cancel trip

GET    /v1/trips/:id/stops    → Get stops for a trip (nested resource)
POST   /v1/trips/:id/stops    → Add a stop to a trip
DELETE /v1/trips/:id/stops/:stopId → Remove a specific stop
```

---

---

# 2. REQUEST & RESPONSE MODELING

> **Consistent structure for every request and response across your entire API.**

---

## Request Structure

### Headers (common)

| Header | Purpose | Example |
|--------|---------|---------|
| `Authorization` | Auth token | `Bearer eyJhbGc...` |
| `Content-Type` | Request body format | `application/json` |
| `Accept` | Desired response format | `application/json` |
| `X-Request-Id` | Trace/correlation ID | `req-abc-123` |
| `X-Idempotency-Key` | Prevent duplicate processing | `idem-xyz-456` |

### Request Body (POST /v1/trips)

```json
{
  "origin": "Mumbai",
  "destination": "Pune",
  "cargo_weight_tons": 12.5,
  "cargo_description": "Electronics",
  "vehicle_type": "container",
  "pickup_date": "2024-02-15T08:00:00Z",
  "stops": ["Lonavala"],
  "customer_notes": "Handle with care"
}
```

### Validation Rules

| Field | Rule | Error if violated |
|-------|------|-------------------|
| `origin` | Required, string, max 100 chars | "origin is required" |
| `destination` | Required, different from origin | "destination must differ from origin" |
| `cargo_weight_tons` | Required, number, 0.1-25.0 | "weight must be between 0.1 and 25 tons" |
| `vehicle_type` | Required, one of enum values | "invalid vehicle_type" |
| `pickup_date` | Required, ISO 8601, future date | "pickup_date must be in the future" |

---

## Response Structure

### Successful Response (Single Resource)

```json
// GET /v1/trips/abc-123
// Status: 200 OK

{
  "data": {
    "id": "abc-123",
    "origin": "Mumbai",
    "destination": "Pune",
    "distance_km": 148.5,
    "cargo_weight_tons": 12.5,
    "status": "in_transit",
    "driver": {
      "id": "drv-42",
      "name": "Ramesh Kumar",
      "phone": "+91-9876543210"
    },
    "estimated_fare": 8500.00,
    "created_at": "2024-02-10T14:30:00Z",
    "started_at": "2024-02-15T08:15:00Z"
  }
}
```

### Successful Response (Collection/List)

```json
// GET /v1/trips?status=in_transit&page=1&limit=10
// Status: 200 OK

{
  "data": [
    {
      "id": "abc-123",
      "origin": "Mumbai",
      "destination": "Pune",
      "status": "in_transit",
      "created_at": "2024-02-10T14:30:00Z"
    },
    {
      "id": "def-456",
      "origin": "Delhi",
      "destination": "Jaipur",
      "status": "in_transit",
      "created_at": "2024-02-11T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total_items": 47,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Created Response

```json
// POST /v1/trips
// Status: 201 Created
// Header: Location: /v1/trips/new-789

{
  "data": {
    "id": "new-789",
    "origin": "Mumbai",
    "destination": "Pune",
    "status": "pending",
    "created_at": "2024-02-15T10:00:00Z"
  },
  "message": "Trip created successfully"
}
```

---

## Response Envelope Pattern

Use a **consistent wrapper** across all endpoints:

```json
// Success
{
  "success": true,
  "data": { ... },
  "pagination": { ... },   // only for lists
  "message": "Optional success message"
}

// Error
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [ ... ]
  }
}
```

---

---

# 3. HTTP STATUS CODES

> **Use the right status code — it tells the client WHAT happened without parsing the body.**

---

## The Essential Status Codes

### Success (2xx)

| Code | Meaning | When to Use |
|------|---------|-------------|
| `200 OK` | Success | GET, PUT, PATCH successful |
| `201 Created` | Resource created | POST successful |
| `204 No Content` | Success, no body | DELETE successful |

### Client Errors (4xx) — "Your fault"

| Code | Meaning | When to Use |
|------|---------|-------------|
| `400 Bad Request` | Invalid request body/params | Validation failed |
| `401 Unauthorized` | Not authenticated | Missing/invalid token |
| `403 Forbidden` | Authenticated but not allowed | No permission for this resource |
| `404 Not Found` | Resource doesn't exist | Invalid ID |
| `409 Conflict` | State conflict | Duplicate, already exists |
| `422 Unprocessable Entity` | Valid JSON but semantic error | Business rule violation |
| `429 Too Many Requests` | Rate limited | Exceeded API quota |

### Server Errors (5xx) — "Our fault"

| Code | Meaning | When to Use |
|------|---------|-------------|
| `500 Internal Server Error` | Unexpected server failure | Unhandled exception |
| `502 Bad Gateway` | Upstream service failed | Payment gateway down |
| `503 Service Unavailable` | Server temporarily down | Maintenance, overloaded |
| `504 Gateway Timeout` | Upstream timed out | Slow DB/service call |

---

## Decision Tree

```
Request successful?
├── YES → Did we create something?
│   ├── YES → 201 Created
│   ├── NO, returning data → 200 OK
│   └── NO, no body needed → 204 No Content
└── NO → Client's fault or server's fault?
    ├── CLIENT'S FAULT (4xx)
    │   ├── Not logged in? → 401
    │   ├── Logged in but no permission? → 403
    │   ├── Resource not found? → 404
    │   ├── Invalid data format? → 400
    │   ├── Business rule violated? → 422
    │   ├── Already exists/conflict? → 409
    │   └── Too many requests? → 429
    └── SERVER'S FAULT (5xx)
        ├── Our code crashed? → 500
        ├── External service down? → 502
        └── We're overloaded? → 503
```

---

---

# 4. ERROR HANDLING

> **Consistent, informative error responses that help developers debug quickly.**

---

## Error Response Format

```json
// POST /v1/trips — with invalid body
// Status: 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "cargo_weight_tons",
        "message": "must be between 0.1 and 25",
        "received": 30
      },
      {
        "field": "pickup_date",
        "message": "must be a future date",
        "received": "2023-01-01T00:00:00Z"
      }
    ]
  },
  "request_id": "req-abc-123"
}
```

## Error Codes (Application-Level)

Define your own codes beyond HTTP status:

```json
// 404 — but which kind of "not found"?
{
  "error": {
    "code": "TRIP_NOT_FOUND",
    "message": "Trip with ID 'xyz' does not exist"
  }
}

// 409 — but which kind of "conflict"?
{
  "error": {
    "code": "DRIVER_ALREADY_ASSIGNED",
    "message": "Trip already has driver 'DRV-42' assigned"
  }
}

// 422 — business rule
{
  "error": {
    "code": "TRIP_NOT_CANCELLABLE",
    "message": "Cannot cancel trip in 'in_transit' status"
  }
}
```

## Error Code Categories

| Prefix | Category | Example |
|--------|----------|---------|
| `AUTH_*` | Authentication/Authorization | `AUTH_TOKEN_EXPIRED` |
| `VALIDATION_*` | Input validation | `VALIDATION_ERROR` |
| `TRIP_*` | Trip domain errors | `TRIP_NOT_FOUND`, `TRIP_NOT_CANCELLABLE` |
| `PAYMENT_*` | Payment errors | `PAYMENT_FAILED`, `PAYMENT_ALREADY_PROCESSED` |
| `DRIVER_*` | Driver errors | `DRIVER_UNAVAILABLE` |
| `RATE_LIMIT_*` | Throttling | `RATE_LIMIT_EXCEEDED` |

---

## Security: What NOT to Expose in Errors

```json
// ❌ BAD — leaks internal info
{
  "error": "PostgresError: relation 'trips' at column 'driver_id' violates FK constraint",
  "stack": "at TripService.create (src/trips/trip.service.ts:45)..."
}

// ✅ GOOD — safe, helpful
{
  "error": {
    "code": "INVALID_DRIVER",
    "message": "The specified driver does not exist"
  }
}
```

---

---

# 5. PAGINATION

> **Never return ALL records. Break large datasets into pages.**

---

## Offset-Based Pagination

```
GET /v1/trips?page=2&limit=20
```

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 20,
    "total_items": 156,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

**Pros:** Simple, can jump to any page
**Cons:** Inconsistent if data changes between pages (items shift), slow for large offsets (`OFFSET 100000` scans 100K rows)

---

## Cursor-Based Pagination

```
GET /v1/trips?cursor=eyJpZCI6ImFiYy0xMjMifQ&limit=20
```

```json
{
  "data": [...],
  "pagination": {
    "limit": 20,
    "next_cursor": "eyJpZCI6ImRlZi00NTYifQ",
    "has_next": true
  }
}
```

**Pros:** Consistent results (no skipping/duplicates), fast regardless of position
**Cons:** Can't jump to page N, can only go forward/backward

---

## When to Use Which?

| Use Case | Best Pagination |
|----------|----------------|
| Admin dashboard with page numbers | Offset-based |
| Mobile app infinite scroll | Cursor-based |
| Real-time feed (new items added frequently) | Cursor-based |
| Small dataset (<1000 items) | Offset-based (simpler) |
| Large dataset + need performance | Cursor-based |

---

---

# 6. FILTERING, SORTING & SEARCH

> **Let clients get exactly the data they need.**

---

## Filtering

```
GET /v1/trips?status=in_transit&origin=Mumbai&created_after=2024-01-01
GET /v1/drivers?status=available&rating_gte=4.0
GET /v1/payments?method=upi&amount_gte=1000&amount_lte=50000
```

### Conventions

| Operator | URL Format | Meaning |
|----------|-----------|---------|
| Equals | `?status=active` | Exact match |
| Greater than | `?rating_gte=4.0` | >= |
| Less than | `?amount_lte=5000` | <= |
| In list | `?status=pending,assigned` | Multiple values (OR) |
| Date range | `?created_after=2024-01-01&created_before=2024-02-01` | Between dates |

---

## Sorting

```
GET /v1/trips?sort_by=created_at&sort_order=desc
GET /v1/drivers?sort_by=rating&sort_order=desc
```

Or using a compact format:
```
GET /v1/trips?sort=-created_at,+distance_km
# - prefix = descending, + prefix = ascending
```

---

## Search

```
GET /v1/trips?search=Mumbai
GET /v1/drivers?q=Ramesh
```

Search typically queries across multiple fields (origin, destination, driver name) using full-text search or ILIKE.

---

---

# 7. API VERSIONING

> **Evolve your API without breaking existing clients.**

---

## Versioning Strategies

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| **URL Path** (most common) | `/v1/trips`, `/v2/trips` | Explicit, easy to understand | URL changes |
| **Header** | `Accept: application/vnd.smartfreight.v1+json` | Clean URLs | Hidden, harder to test |
| **Query Param** | `/trips?version=1` | Easy to add | Easy to forget |

### Recommendation: Use URL path versioning

```
https://api.smartfreight.in/v1/trips
https://api.smartfreight.in/v2/trips
```

---

## When to Version (Breaking Changes)

| Breaking (needs new version) | Non-Breaking (safe) |
|-----------------------------|---------------------|
| Removing a field from response | Adding a new field to response |
| Changing a field's type | Adding a new optional query param |
| Renaming a field | Adding a new endpoint |
| Changing URL structure | Adding a new enum value |
| Making optional field required | Deprecating (but still supporting) |

---

## Versioning in Practice (NestJS)

```typescript
// v1 — original
@Controller('v1/trips')
export class TripsV1Controller {
  @Get(':id')
  getTrip(@Param('id') id: string) {
    return this.tripsService.findOne(id);
    // Returns: { id, origin, destination, fare }
  }
}

// v2 — added detailed pricing breakdown
@Controller('v2/trips')
export class TripsV2Controller {
  @Get(':id')
  getTrip(@Param('id') id: string) {
    return this.tripsService.findOneV2(id);
    // Returns: { id, origin, destination, pricing: { base, gst, toll, total } }
  }
}
```

---

---

# 8. AUTHENTICATION & AUTHORIZATION

> **Auth answers: WHO are you (authentication) and WHAT can you do (authorization)?**

---

## Common Patterns

| Pattern | Best For | How It Works |
|---------|----------|-------------|
| **API Key** | Server-to-server, simple apps | Static key in header |
| **JWT (Bearer Token)** | User-facing APIs | Signed token with claims |
| **OAuth 2.0** | Third-party access | Authorization code flow |
| **Session Cookie** | Web apps (SSR) | Server stores session |

---

## JWT Flow (Most Common for APIs)

```
1. Client: POST /v1/auth/login { email, password }
2. Server: Validates → Returns { access_token, refresh_token }
3. Client: Stores tokens, sends access_token with every request
4. Server: Validates token on every request (middleware)
5. Token expires → Client uses refresh_token to get new access_token
```

### Request with Auth

```
GET /v1/trips
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Payload (Claims)

```json
{
  "sub": "user-123",          // subject (user ID)
  "email": "shubham@smartfreight.in",
  "role": "admin",            // for RBAC
  "iat": 1708000000,         // issued at
  "exp": 1708003600          // expires (1 hour)
}
```

---

## Role-Based Access Control (RBAC)

| Endpoint | Customer | Driver | Admin |
|----------|----------|--------|-------|
| `GET /v1/trips` | Own trips only | Assigned trips | All trips |
| `POST /v1/trips` | ✅ | ❌ | ✅ |
| `PATCH /v1/trips/:id/status` | ❌ | ✅ (own) | ✅ |
| `GET /v1/drivers` | ❌ | ❌ | ✅ |
| `DELETE /v1/trips/:id` | ❌ | ❌ | ✅ |

---

---

# 9. IDEMPOTENCY

> **Same request sent twice = same result. Critical for payments and any mutation.**

---

## Why Idempotency?

```
Client → POST /v1/payments → Server processes → Response lost (network timeout)
Client doesn't know if payment went through!
Client retries → POST /v1/payments → WITHOUT idempotency: DOUBLE CHARGE! 💸
                                      WITH idempotency: Returns original result ✅
```

---

## Implementation

```
Client sends:
POST /v1/payments
X-Idempotency-Key: idem-abc-123  ← client generates unique key
{ "trip_id": "T001", "amount": 15000 }

Server:
1. Check if idem-abc-123 already processed
2. If YES → return stored response (don't process again)
3. If NO → process payment, store response with key
```

### Methods and Idempotency

| Method | Naturally Idempotent? | Need Idempotency Key? |
|--------|----------------------|----------------------|
| GET | ✅ Yes | No |
| PUT | ✅ Yes (replace) | No |
| DELETE | ✅ Yes | No |
| POST | ❌ No | **YES** (for payments, bookings) |
| PATCH | Depends | Sometimes |

---

---

# 10. RATE LIMITING

> **Protect your API from abuse and ensure fair usage.**

---

## Response Headers

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100        ← max requests per window
X-RateLimit-Remaining: 67     ← remaining in current window
X-RateLimit-Reset: 1708003600 ← when window resets (Unix timestamp)
```

## When Exceeded

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 30 seconds.",
    "retry_after": 30
  }
}
```

## Rate Limit Tiers

| Tier | Limit | Who |
|------|-------|-----|
| Free | 100 req/min | Unverified users |
| Standard | 1000 req/min | Paying customers |
| Premium | 10000 req/min | Enterprise |
| Internal | Unlimited | Service-to-service |

---

---

# 11. API DESIGN: FULL EXAMPLE

> **Complete API spec for Smart Freight's Trip module.**

---

## Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/v1/trips` | Create a new trip | Customer |
| GET | `/v1/trips` | List trips (filtered) | Customer/Admin |
| GET | `/v1/trips/:id` | Get trip details | Customer/Driver/Admin |
| PATCH | `/v1/trips/:id` | Update trip | Admin |
| PATCH | `/v1/trips/:id/status` | Update trip status | Driver/Admin |
| DELETE | `/v1/trips/:id` | Cancel trip | Customer/Admin |
| POST | `/v1/trips/:id/assign` | Assign driver to trip | Admin |
| GET | `/v1/trips/:id/tracking` | Get live location | Customer |
| POST | `/v1/trips/:id/rating` | Rate completed trip | Customer |

---

## Example: Create Trip

### Request

```http
POST /v1/trips HTTP/1.1
Host: api.smartfreight.in
Authorization: Bearer eyJhbGc...
Content-Type: application/json
X-Idempotency-Key: create-trip-1708000001

{
  "origin": "Mumbai",
  "destination": "Pune",
  "cargo_weight_tons": 12.5,
  "cargo_description": "Electronics - LED TVs",
  "vehicle_type": "container",
  "pickup_date": "2024-02-15T08:00:00Z",
  "stops": ["Lonavala"],
  "special_instructions": "Fragile cargo, avoid rough roads"
}
```

### Success Response

```http
HTTP/1.1 201 Created
Location: /v1/trips/trip-789
Content-Type: application/json

{
  "success": true,
  "data": {
    "id": "trip-789",
    "origin": "Mumbai",
    "destination": "Pune",
    "distance_km": 148.5,
    "cargo_weight_tons": 12.5,
    "vehicle_type": "container",
    "status": "pending",
    "estimated_fare": 8500.00,
    "pickup_date": "2024-02-15T08:00:00Z",
    "stops": [
      { "city": "Lonavala", "order": 1 }
    ],
    "created_at": "2024-02-10T14:30:00Z"
  },
  "message": "Trip created successfully"
}
```

### Error Responses

```http
HTTP/1.1 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "cargo_weight_tons", "message": "exceeds max capacity of 25T" }
    ]
  }
}
```

```http
HTTP/1.1 401 Unauthorized

{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "Access token has expired. Please refresh."
  }
}
```

---

---

# Common Mistakes

## ❌ BAD: Verbs in URLs

```
POST /createTrip
GET /getAllTrips
PUT /updateTripStatus
DELETE /removeTrip
```

## ✅ GOOD: Nouns + HTTP methods

```
POST /v1/trips          ← method says "create"
GET /v1/trips           ← method says "list"
PATCH /v1/trips/:id     ← method says "update"
DELETE /v1/trips/:id    ← method says "delete"
```

---

## ❌ BAD: 200 for everything

```json
// Status: 200 OK
{ "success": false, "error": "Trip not found" }
```

Client has to parse body to know if it worked!

## ✅ GOOD: Correct HTTP status

```json
// Status: 404 Not Found
{ "error": { "code": "TRIP_NOT_FOUND", "message": "Trip 'xyz' not found" } }
```

---

## ❌ BAD: Inconsistent naming

```
GET /v1/trips           ← plural
GET /v1/driver/:id      ← singular (inconsistent!)
GET /v1/trip-stops      ← kebab-case
GET /v1/payment_history ← snake_case (inconsistent!)
```

## ✅ GOOD: One convention everywhere

```
GET /v1/trips
GET /v1/drivers/:id
GET /v1/trip-stops
GET /v1/payment-history
```

---

## ❌ BAD: Returning unnecessary data

```json
// GET /v1/trips — list endpoint returning EVERYTHING
{
  "data": [
    {
      "id": "T001",
      "origin": "Mumbai",
      "destination": "Pune",
      "driver": { "id": "...", "name": "...", "phone": "...", "license": "...", "address": "..." },
      "truck": { "id": "...", "model": "...", "capacity": "...", "maintenance_history": [...] },
      "stops": [...],
      "payment": { "id": "...", "amount": "...", "gateway_response": {...} },
      // 50 more fields...
    }
  ]
}
```

## ✅ GOOD: Lean list, detailed single

```json
// GET /v1/trips — lean list
{ "data": [{ "id": "T001", "origin": "Mumbai", "destination": "Pune", "status": "in_transit" }] }

// GET /v1/trips/T001 — full details (only when needed)
{ "data": { "id": "T001", ..., "driver": {...}, "stops": [...] } }
```

---

## ❌ BAD: No pagination

```json
// GET /v1/trips returns ALL 50,000 trips
// Response: 15MB JSON, client crashes, server OOM
```

## ✅ GOOD: Always paginate collections

```
GET /v1/trips?page=1&limit=20
```

---

# Quick Reference Table

| Mistake | Fix |
|---------|-----|
| Verbs in URLs | Use nouns + HTTP methods |
| 200 for errors | Use correct status codes (4xx/5xx) |
| Inconsistent naming | Pick one convention (plural, kebab-case) |
| No versioning | URL path: `/v1/resource` |
| No pagination | Always paginate lists |
| Returning too much data | Lean list, detailed single resource |
| No error codes | Application-level codes (TRIP_NOT_FOUND) |
| No idempotency for payments | X-Idempotency-Key header |
| Leaking internals in errors | Generic messages, log details server-side |

---

# Quick Cheat Sheet

| Concept | One-liner | Key Rule |
|---------|-----------|----------|
| **REST** | Resources + HTTP methods + status codes | URLs are nouns, methods are verbs |
| **GET** | Read (safe, idempotent) | Never modify data |
| **POST** | Create (not idempotent) | Returns 201 + Location header |
| **PUT** | Full replace (idempotent) | Send ALL fields |
| **PATCH** | Partial update | Send only changed fields |
| **DELETE** | Remove (idempotent) | Returns 204 No Content |
| **200** | Success | Default for GET/PUT/PATCH |
| **201** | Created | For POST success |
| **400** | Bad request | Validation failure |
| **401** | Unauthorized | Not authenticated |
| **403** | Forbidden | No permission |
| **404** | Not found | Resource doesn't exist |
| **429** | Rate limited | Too many requests |
| **Pagination** | Break large results into pages | Offset (simple) vs Cursor (performant) |
| **Versioning** | `/v1/resource` | Version in URL path |
| **Idempotency** | Same request → same result | Use X-Idempotency-Key for POST |

---

# Interview Tips for API Design

1. **Start with resources** — identify the main entities (trips, drivers, payments)
2. **List endpoints** — CRUD for each resource + any special actions
3. **Show request/response** — actual JSON examples win interviews
4. **Mention error handling** — consistent error codes + proper HTTP status
5. **Mention pagination** — shows you think about scale
6. **Mention auth** — even briefly: "JWT Bearer token in header"
7. **Mention idempotency** — especially for payment/booking endpoints
8. **State trade-offs** — "I chose cursor pagination because the feed has frequent inserts"
