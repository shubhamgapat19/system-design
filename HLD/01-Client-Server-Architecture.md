# Client-Server Architecture — The Foundation of Distributed Systems

The foundation of every distributed system. Before you design any scalable system, you must deeply understand how clients talk to servers, what happens at each layer, and how the internet actually moves data. Every system design interview starts here.



- **Client:** Any device or application that initiates a request to a server (browser, mobile app, CLI, IoT device).
- **Server:** A machine/process that listens for incoming requests, processes them, and sends back responses.
- **Client-Server Model:** An architecture where clients (requesters) and servers (providers) communicate over a network, with clear separation of concerns.
- **Request-Response Cycle:** Client sends a request → Server processes → Server sends response → Client renders/uses it.
- **Stateless Protocol:** Each request is independent; the server doesn't remember previous requests (HTTP is stateless).
- **Stateful Connection:** The server maintains session information across requests (WebSocket, TCP connections).
- **Thin Client:** Client does minimal processing, relies on server for logic (e.g., server-rendered web pages).
- **Thick/Fat Client:** Client handles significant logic locally (e.g., React SPA, mobile apps).
- **API (Application Programming Interface):** A contract/interface through which clients communicate with servers.
- **Latency:** Time taken for a request to travel from client to server and back (round-trip time).
- **Throughput:** Number of requests a server can handle per unit time (requests/second).
- **Bandwidth:** Maximum data transfer capacity of the network link (Mbps, Gbps).
- **Port:** A logical endpoint on a server; a single IP can serve multiple services via different ports (HTTP:80, HTTPS:443, PostgreSQL:5432).
- **Socket:** A combination of IP + Port that uniquely identifies a network connection endpoint.
- **Proxy:** An intermediary server that sits between client and server, forwarding requests on behalf of one.
- **Reverse Proxy:** A server that sits in front of backend servers, forwarding client requests to the right server (Nginx, HAProxy).
- **IP Address:** A unique numerical identifier assigned to every device on a network (IPv4: 32-bit, IPv6: 128-bit).
- **MAC Address:** Hardware-level address burned into the network interface card (NIC); used in local network communication.
- **Packet:** The smallest unit of data transmitted over a network; contains headers (routing info) + payload (actual data).
- **Protocol:** A set of rules governing communication between systems (HTTP, TCP, UDP, FTP, SMTP).

---

## 1. How the Internet Actually Works (Full Picture)

> **A client sends bits over wires/radio to a server, which sends bits back. Everything else is abstraction layers.**

### The OSI Model — 7 Layers of Networking

Every piece of data you send travels through these layers:

```mermaid
graph TD
    A[7. Application Layer<br/>HTTP, FTP, SMTP, DNS<br/>What the user sees] --> B[6. Presentation Layer<br/>Encryption TLS/SSL, Compression<br/>Data formatting]
    B --> C[5. Session Layer<br/>Session management<br/>Connection persistence]
    C --> D[4. Transport Layer<br/>TCP/UDP<br/>Reliable vs Fast delivery]
    D --> E[3. Network Layer<br/>IP, Routing<br/>Which path to take?]
    E --> F[2. Data Link Layer<br/>Ethernet, WiFi, MAC<br/>Node-to-node transfer]
    F --> G[1. Physical Layer<br/>Cables, Radio, Fiber<br/>Raw bits on wire]
```

### Simplified for Interviews (TCP/IP Model — 4 Layers)

| Layer | OSI Equivalent | Protocol | What It Does |
|---|---|---|---|
| **Application** | 7, 6, 5 | HTTP, DNS, FTP, SMTP | User-facing communication |
| **Transport** | 4 | TCP, UDP | End-to-end delivery, port addressing |
| **Internet** | 3 | IP, ICMP | Routing between networks |
| **Network Access** | 2, 1 | Ethernet, WiFi | Physical transmission |

### What Happens When You Type swiggy.com (Complete)

```mermaid
sequenceDiagram
    participant User as Browser
    participant Cache as Browser Cache
    participant OS as OS DNS Cache
    participant Router as Router
    participant ISP as ISP Recursive Resolver
    participant Root as Root DNS (.)
    participant TLD as TLD DNS (.com)
    participant Auth as Authoritative DNS (swiggy.com)
    participant CDN as CDN Edge Server
    participant LB as Load Balancer
    participant App as App Server
    participant DB as Database
    participant Redis as Redis Cache

    Note over User,Auth: Phase 1: DNS Resolution (~50-200ms)
    User->>Cache: swiggy.com IP?
    Cache-->>User: Not found
    User->>OS: Check OS DNS cache
    OS-->>User: Not found
    User->>Router: Check router cache
    Router-->>User: Not found
    User->>ISP: Recursive query: swiggy.com?
    ISP->>Root: Who handles .com?
    Root-->>ISP: TLD server at x.x.x.x
    ISP->>TLD: Who handles swiggy.com?
    TLD-->>ISP: Auth server at y.y.y.y
    ISP->>Auth: IP for swiggy.com?
    Auth-->>ISP: 103.97.x.x (TTL: 300s)
    ISP-->>User: 103.97.x.x

    Note over User,LB: Phase 2: TCP + TLS (~30-100ms)
    User->>LB: SYN
    LB-->>User: SYN-ACK
    User->>LB: ACK (TCP established)
    User->>LB: ClientHello (TLS)
    LB-->>User: ServerHello + Certificate
    User->>LB: Key Exchange
    LB-->>User: Finished (TLS established)

    Note over User,Redis: Phase 3: HTTP Request-Response (~100-500ms)
    User->>LB: GET /api/home HTTP/2
    LB->>App: Forward (sticky/round-robin)
    App->>Redis: Check cache for home feed
    Redis-->>App: Cache HIT → return data
    App-->>LB: 200 OK + JSON
    LB-->>User: Response delivered

    Note over User,CDN: Phase 4: Static Assets (parallel)
    User->>CDN: GET /static/bundle.js
    CDN-->>User: 200 OK (from edge, ~20ms)
```

### Step-by-Step Breakdown

| Step | What Happens | Time |
|---|---|---|
| 1. URL Parsing | Browser parses `https://swiggy.com/` into protocol + domain + path | ~0ms |
| 2. Browser Cache | Check if response is cached (Cache-Control, ETag) | ~0ms |
| 3. DNS Resolution | Resolve domain → IP (recursive DNS lookup) | 20-200ms |
| 4. TCP Handshake | 3-way handshake: SYN → SYN-ACK → ACK | 10-30ms |
| 5. TLS Handshake | Negotiate encryption (certificates, keys) | 30-100ms |
| 6. HTTP Request | Send GET request with headers, cookies | ~1ms |
| 7. Server Processing | Load balancer → app server → cache/DB | 50-500ms |
| 8. HTTP Response | Server sends back status + headers + body | depends on size |
| 9. Browser Rendering | Parse HTML → Build DOM → CSSOM → Layout → Paint | 100-1000ms |
| 10. JS Execution | React hydration, API calls for dynamic data | 200-2000ms |

---

## 2. Client-Server vs Other Architectures

> **Not everything is client-server. Know the alternatives and when they apply.**

### Architecture Comparison

```mermaid
graph LR
    subgraph "Client-Server (1:N)"
        C1[Client 1] --> S[Server]
        C2[Client 2] --> S
        C3[Client 3] --> S
    end
```

```mermaid
graph LR
    subgraph "Peer-to-Peer (N:N)"
        P1[Peer A] <--> P2[Peer B]
        P2 <--> P3[Peer C]
        P1 <--> P3
    end
```

```mermaid
graph LR
    subgraph "3-Tier Architecture"
        CT[Client Tier<br/>Browser] --> MT[Middle Tier<br/>App Server]
        MT --> DT[Data Tier<br/>Database]
    end
```

```mermaid
graph LR
    subgraph "Microservices"
        GW[API Gateway] --> S1[Auth Service]
        GW --> S2[Order Service]
        GW --> S3[Payment Service]
        S2 --> S3
    end
```

### Detailed Comparison Table

| Architecture | Structure | Pros | Cons | Use Case |
|---|---|---|---|---|
| **Client-Server** | 1 server, many clients | Simple, centralized control, easy security | Single point of failure, server bottleneck | Most web apps (Swiggy, Zomato) |
| **Peer-to-Peer** | All nodes equal | No SPOF, scales naturally, no server cost | Hard to manage, security issues, discovery hard | BitTorrent, Bitcoin, WebRTC video |
| **3-Tier** | Presentation → Logic → Data | Separation of concerns, independent scaling | More complex, more network hops | Enterprise apps (banking systems) |
| **N-Tier** | Many specialized layers | Maximum flexibility | Over-engineering risk, latency | Large enterprise (insurance, ERP) |
| **Microservices** | Many small independent services | Independent deploy, tech flexibility, team autonomy | Network complexity, distributed debugging | Large scale (Netflix, Uber, Amazon) |
| **Serverless** | Functions triggered by events | Zero ops, auto-scale, pay-per-use | Cold starts, vendor lock-in, limited runtime | Event-driven (image resize, webhooks) |
| **Event-Driven** | Components react to events | Loosely coupled, async, scalable | Hard to debug, eventual consistency | Real-time systems (stock trading, IoT) |

### When to Use What?

```python
# Decision Framework
if users < 1000 and team_size <= 3:
    use = "Monolithic Client-Server"  # Your Smart Freight MVP

elif users < 100_000 and team_size <= 10:
    use = "Client-Server with 3-Tier separation"

elif users > 1_000_000 or team_size > 20:
    use = "Microservices"

elif need_real_time and peer_communication:
    use = "P2P (WebRTC for video, blockchain for trust)"

elif traffic_is_spiky and event_driven:
    use = "Serverless (Lambda/Cloud Functions)"
```

### Real-world Analogy

| Architecture | Analogy |
|---|---|
| **Client-Server** | Restaurant: You order (client), kitchen cooks (server) |
| **P2P** | Potluck: Everyone brings AND eats food |
| **3-Tier** | Restaurant chain: Front desk → Kitchen → Warehouse |
| **Microservices** | Food court: Pizza counter, Chinese counter, Juice bar — each independent |
| **Serverless** | Food truck: Appears when needed, gone when not |

---

## 3. Layers of a Production System (Deep Dive)

> **Every production system has these layers. System design interviews expect you to identify and discuss each.**

### Complete System Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        WEB[Web Browser<br/>React/Next.js]
        MOB[Mobile App<br/>React Native/Flutter]
        IOT[IoT Devices<br/>GPS Trackers]
    end

    subgraph "Edge Layer"
        DNS[DNS<br/>Route 53/Cloudflare]
        CDN[CDN<br/>CloudFront/Cloudflare]
        WAF[WAF<br/>Web Application Firewall]
    end

    subgraph "Ingress Layer"
        LB[Load Balancer<br/>Nginx/ALB/HAProxy]
        AG[API Gateway<br/>Kong/AWS API GW]
        RL[Rate Limiter<br/>Token Bucket]
    end

    subgraph "Application Layer"
        APP1[App Server 1<br/>NestJS/Django]
        APP2[App Server 2<br/>NestJS/Django]
        APP3[App Server 3<br/>NestJS/Django]
    end

    subgraph "Service Layer"
        AUTH[Auth Service]
        TRIP[Trip Service]
        PAY[Payment Service]
        NOTIF[Notification Service]
    end

    subgraph "Data Layer"
        CACHE[Cache<br/>Redis/Memcached]
        DB_W[DB Primary<br/>PostgreSQL Write]
        DB_R1[DB Replica 1<br/>Read]
        DB_R2[DB Replica 2<br/>Read]
        SEARCH[Search<br/>Elasticsearch]
        BLOB[Object Store<br/>S3/MinIO]
    end

    subgraph "Async Layer"
        MQ[Message Queue<br/>Kafka/RabbitMQ]
        WORKER[Workers<br/>Background Jobs]
        CRON[Scheduler<br/>Cron Jobs]
    end

    WEB --> DNS
    MOB --> DNS
    IOT --> DNS
    DNS --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> AG
    AG --> RL
    RL --> APP1
    RL --> APP2
    RL --> APP3
    APP1 --> AUTH
    APP1 --> TRIP
    APP2 --> PAY
    APP3 --> NOTIF
    TRIP --> CACHE
    TRIP --> DB_W
    TRIP --> DB_R1
    PAY --> DB_W
    AUTH --> CACHE
    NOTIF --> MQ
    MQ --> WORKER
    WORKER --> DB_W
    TRIP --> SEARCH
    NOTIF --> BLOB
```

### Layer-by-Layer Deep Dive

#### Layer 1: Client Layer

| Type | Examples | Characteristics |
|---|---|---|
| **Web (SPA)** | React, Vue, Angular | JS-heavy, API calls, runs in browser |
| **Web (SSR)** | Next.js, Nuxt | Server renders HTML, hydrates on client |
| **Mobile Native** | Swift, Kotlin | Platform APIs, offline support, push notifs |
| **Mobile Cross-platform** | React Native, Flutter | Single codebase, native feel |
| **IoT/Embedded** | GPS tracker, sensors | Low power, intermittent connectivity, UDP |
| **CLI** | curl, custom tools | Scripting, automation |
| **Desktop** | Electron, Tauri | Rich UI, local file access |

```python
# Example: A client making an API call (Python requests)
import requests

# Simple GET request
response = requests.get(
    "https://api.smartfreight.in/api/trips",
    headers={
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9...",
        "Content-Type": "application/json",
        "X-Request-Id": "req_abc123",  # For distributed tracing
    },
    params={"status": "active", "page": 1, "limit": 20},
    timeout=5,  # Never make requests without timeout!
)

if response.status_code == 200:
    trips = response.json()["data"]
elif response.status_code == 401:
    # Token expired → refresh and retry
    pass
elif response.status_code == 429:
    # Rate limited → exponential backoff
    retry_after = int(response.headers.get("Retry-After", 60))
```

#### Layer 2: DNS & CDN (Edge Layer)

```python
# DNS resolution happens before your code even runs
# But you can observe it:

import socket
import time

start = time.time()
ip = socket.gethostbyname("swiggy.com")
dns_time = (time.time() - start) * 1000

print(f"swiggy.com → {ip} (resolved in {dns_time:.1f}ms)")
# Output: swiggy.com → 103.97.1.1 (resolved in 23.4ms)
```

**CDN Decision Matrix:**

| Content Type | Serve From | Why |
|---|---|---|
| Images, CSS, JS, Fonts | CDN | Static, cacheable, serve from edge |
| HTML (SSR) | CDN + Origin | Cache at edge with short TTL |
| API responses | Origin (App server) | Dynamic, personalized |
| Video/Audio | CDN with streaming | Large files, bandwidth-intensive |
| User uploads | Object store (S3) + CDN | Store centrally, cache at edge |

#### Layer 3: Load Balancer & API Gateway

```python
# Conceptual: What a load balancer does internally

class LoadBalancer:
    def __init__(self, servers: list[str]):
        self.servers = servers
        self.current = 0
        self.health_status = {s: True for s in servers}

    def round_robin(self) -> str:
        """Simplest algorithm: rotate through servers"""
        healthy = [s for s in self.servers if self.health_status[s]]
        if not healthy:
            raise Exception("All servers down!")
        server = healthy[self.current % len(healthy)]
        self.current += 1
        return server

    def least_connections(self, active_connections: dict) -> str:
        """Route to server with fewest active connections"""
        healthy = {s: c for s, c in active_connections.items()
                   if self.health_status[s]}
        return min(healthy, key=healthy.get)

    def health_check(self, server: str) -> bool:
        """Ping server every 10s, mark unhealthy if no response"""
        try:
            response = requests.get(f"http://{server}/health", timeout=2)
            return response.status_code == 200
        except:
            return False


# Load Balancing Algorithms Comparison
"""
| Algorithm          | How It Works                    | Best For                    |
|--------------------|----------------------------------|-----------------------------|
| Round Robin        | 1→2→3→1→2→3                    | Equal server capacity       |
| Weighted RR        | 1→1→1→2→2→3 (by weight)       | Unequal server specs        |
| Least Connections  | Route to server with min conns  | Long-lived connections      |
| IP Hash            | hash(client_ip) % servers       | Session affinity (sticky)   |
| Consistent Hashing | Hash ring, minimal redistribution| Cache servers, stateful     |
| Random             | Pick any server                 | Simple, surprisingly good   |
"""
```

#### Layer 4: Application Server

```python
# What happens INSIDE a server when a request arrives

# NestJS / Express equivalent in Python (FastAPI)
from fastapi import FastAPI, Depends, HTTPException, Request
from datetime import datetime
import uuid

app = FastAPI()

# Middleware: Runs BEFORE every request
@app.middleware("http")
async def add_request_context(request: Request, call_next):
    # 1. Generate unique request ID for tracing
    request_id = str(uuid.uuid4())
    
    # 2. Log incoming request
    start = datetime.now()
    
    # 3. Process the actual request
    response = await call_next(request)
    
    # 4. Log response time
    duration = (datetime.now() - start).total_seconds() * 1000
    print(f"[{request_id}] {request.method} {request.url.path} → {response.status_code} ({duration:.0f}ms)")
    
    # 5. Add tracking headers to response
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.0f}ms"
    return response


# Route handler: Business logic
@app.get("/api/trips/{trip_id}")
async def get_trip(trip_id: str, current_user = Depends(get_current_user)):
    """
    Request lifecycle:
    1. Authentication (JWT verification)
    2. Authorization (does this user own this trip?)
    3. Validation (is trip_id a valid format?)
    4. Cache check (is this in Redis?)
    5. Database query (if cache miss)
    6. Response serialization (Python dict → JSON)
    7. Response sent back through middleware
    """
    # Check cache first
    cached = await redis.get(f"trip:{trip_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss → DB query
    trip = await db.query("SELECT * FROM trips WHERE id = $1", trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check authorization
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your trip")
    
    # Cache for next time (TTL: 5 minutes)
    await redis.setex(f"trip:{trip_id}", 300, json.dumps(trip.dict()))
    
    return trip
```

#### Layer 5: Database Layer

```python
# Connection Pooling — Critical for production

"""
WITHOUT connection pooling:
  Every request → open new DB connection → query → close connection
  Problem: Opening connections is EXPENSIVE (TCP + auth = 50-100ms each)
  At 1000 req/s, you're opening 1000 connections/second → DB crashes

WITH connection pooling:
  App starts → open 20 connections → keep them alive → reuse them
  Every request → borrow connection from pool → query → return to pool
  At 1000 req/s, 20 connections handle everything efficiently
"""

# Prisma (your stack) handles pooling automatically
# But conceptually, here's what's happening:

class ConnectionPool:
    def __init__(self, min_connections=5, max_connections=20):
        self.pool = []
        self.min = min_connections
        self.max = max_connections
        # Pre-create minimum connections
        for _ in range(min_connections):
            self.pool.append(self._create_connection())

    def get_connection(self):
        if self.pool:
            return self.pool.pop()
        elif self.active_count < self.max:
            return self._create_connection()
        else:
            # Wait for a connection to be returned
            raise Exception("Pool exhausted — all connections in use")

    def release_connection(self, conn):
        self.pool.append(conn)  # Return to pool for reuse
```

### Smart Freight System — Mapped to Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT LAYER                                                     │
│ • React Native (Driver app) — GPS tracking, trip updates        │
│ • Next.js (Admin dashboard) — fleet management, analytics       │
│ • IoT device (GPS tracker) — sends location every 10 seconds    │
├─────────────────────────────────────────────────────────────────┤
│ EDGE LAYER                                                       │
│ • Vercel Edge (dashboard CDN + SSR)                             │
│ • Cloudflare (DDoS protection, WAF)                             │
├─────────────────────────────────────────────────────────────────┤
│ INGRESS LAYER                                                    │
│ • Vercel/AWS ALB (load balancing) — auto-managed initially      │
│ • Rate limiting (100 req/min per user for API)                  │
├─────────────────────────────────────────────────────────────────┤
│ APPLICATION LAYER                                                │
│ • NestJS server (handles all API requests)                      │
│ • JWT authentication (stateless, scalable)                      │
│ • Prisma ORM (type-safe DB queries)                             │
├─────────────────────────────────────────────────────────────────┤
│ DATA LAYER                                                       │
│ • PostgreSQL (trips, users, vehicles, invoices)                 │
│ • Redis (real-time truck locations, session cache, rate limits) │
├─────────────────────────────────────────────────────────────────┤
│ ASYNC LAYER                                                      │
│ • BullMQ (job queue: send notifications, process GPS batches)   │
│ • Cron (daily: generate invoices, weekly: fleet reports)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. HTTP Protocol — Complete Deep Dive

> **HTTP is the language clients and servers speak. Master every detail.**

### HTTP Versions Evolution

| Version | Year | Key Feature | Connection Model |
|---|---|---|---|
| **HTTP/0.9** | 1991 | GET only, no headers | One request per connection |
| **HTTP/1.0** | 1996 | Headers, status codes, POST | New connection per request |
| **HTTP/1.1** | 1997 | Keep-alive, chunked transfer, pipelining | Persistent connections |
| **HTTP/2** | 2015 | Multiplexing, header compression, server push | Single connection, multiple streams |
| **HTTP/3** | 2022 | QUIC (UDP-based), 0-RTT | No head-of-line blocking |

```mermaid
graph LR
    subgraph "HTTP/1.1 (6 parallel connections)"
        C1[Request 1] --> S1[Response 1]
        C2[Request 2] --> S2[Response 2]
        C3[Request 3] --> S3[Blocked until 1 or 2 finish]
    end
```

```mermaid
graph LR
    subgraph "HTTP/2 (1 connection, multiplexed)"
        C1[Stream 1: Request] --> S1[Stream 1: Response]
        C2[Stream 2: Request] --> S2[Stream 2: Response]
        C3[Stream 3: Request] --> S3[Stream 3: Response]
    end
```

### HTTP Request — Anatomy

```http
POST /api/v1/trips HTTP/1.1
Host: api.smartfreight.in
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzIn0.abc
Accept: application/json
Accept-Encoding: gzip, deflate, br
User-Agent: SmartFreight-iOS/2.1.0
X-Request-Id: req_550e8400-e29b-41d4-a716-446655440000
X-Client-Version: 2.1.0
Cache-Control: no-cache
Content-Length: 156

{
  "origin": {
    "lat": 18.5204,
    "lng": 73.8567,
    "address": "Pune, Maharashtra"
  },
  "destination": {
    "lat": 19.0760,
    "lng": 72.8777,
    "address": "Mumbai, Maharashtra"
  },
  "truck_type": "14_wheeler",
  "cargo_weight_kg": 8000
}
```

**Request Components Explained:**

| Component | Purpose | Example |
|---|---|---|
| **Method** | What action to perform | POST (create) |
| **Path** | Which resource | /api/v1/trips |
| **Version** | HTTP version | HTTP/1.1 |
| **Host** | Which server (virtual hosting) | api.smartfreight.in |
| **Content-Type** | Format of body | application/json |
| **Authorization** | Who is making the request | Bearer JWT token |
| **Accept** | What format client wants back | application/json |
| **Accept-Encoding** | Compression algorithms supported | gzip, br |
| **User-Agent** | Client identification | App name + version |
| **X-Request-Id** | Distributed tracing ID | UUID |
| **Cache-Control** | Caching directives | no-cache |
| **Content-Length** | Size of body in bytes | 156 |

### HTTP Response — Anatomy

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8
X-Request-Id: req_550e8400-e29b-41d4-a716-446655440000
X-Response-Time: 142ms
Cache-Control: no-store
RateLimit-Limit: 100
RateLimit-Remaining: 87
RateLimit-Reset: 1705312800
Location: /api/v1/trips/TRIP_20240115_001
Date: Mon, 15 Jan 2024 10:30:00 GMT
Content-Length: 245

{
  "success": true,
  "data": {
    "trip_id": "TRIP_20240115_001",
    "status": "scheduled",
    "origin": "Pune, Maharashtra",
    "destination": "Mumbai, Maharashtra",
    "estimated_distance_km": 150,
    "estimated_duration_hours": 3.5,
    "estimated_cost": 12500,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### HTTP Methods — Complete Reference

| Method | Purpose | Idempotent? | Safe? | Has Body? | Cacheable? |
|---|---|---|---|---|---|
| `GET` | Read/retrieve resource | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| `POST` | Create new resource | ❌ No | ❌ No | ✅ Yes | ❌ No |
| `PUT` | Replace entire resource | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| `PATCH` | Partial update | ❌ No | ❌ No | ✅ Yes | ❌ No |
| `DELETE` | Remove resource | ✅ Yes | ❌ No | Optional | ❌ No |
| `HEAD` | GET without body (headers only) | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| `OPTIONS` | What methods are supported? (CORS preflight) | ✅ Yes | ✅ Yes | ❌ No | ❌ No |

**Key Terms:**
- **Idempotent** = Calling it 1 time or 100 times produces the same result (PUT the same data = same outcome)
- **Safe** = Doesn't modify server state (GET just reads, never changes data)

### HTTP Status Codes — The Complete Picture

```python
# Status Code Decision Tree for API Design

"""
2xx — SUCCESS (everything worked)
├── 200 OK              → GET succeeded, data in body
├── 201 Created         → POST succeeded, new resource created
├── 202 Accepted        → Request received, processing async (queued)
├── 204 No Content      → DELETE succeeded, nothing to return
└── 206 Partial Content → Range request (video streaming, large files)

3xx — REDIRECTION (go somewhere else)
├── 301 Moved Permanently → URL changed forever (SEO: passes link juice)
├── 302 Found             → Temporary redirect (login → dashboard)
├── 304 Not Modified      → Use your cached version (ETag matched)
└── 307 Temporary Redirect→ Same as 302 but preserves HTTP method

4xx — CLIENT ERROR (you messed up)
├── 400 Bad Request       → Invalid JSON, missing required field
├── 401 Unauthorized      → No token / token expired (WHO are you?)
├── 403 Forbidden         → Valid token but no permission (you CAN'T)
├── 404 Not Found         → Resource doesn't exist
├── 405 Method Not Allowed→ POST to a GET-only endpoint
├── 409 Conflict          → Duplicate entry, version conflict
├── 413 Payload Too Large → Request body exceeds limit
├── 422 Unprocessable     → Valid JSON but business logic fails
├── 429 Too Many Requests → Rate limited, check Retry-After header
└── 451 Unavailable       → Blocked for legal reasons

5xx — SERVER ERROR (we messed up)
├── 500 Internal Server Error → Unhandled exception, bug in code
├── 502 Bad Gateway           → Upstream server returned invalid response
├── 503 Service Unavailable   → Server overloaded or in maintenance
└── 504 Gateway Timeout       → Upstream server took too long
"""
```

### Headers You Must Know

| Header | Direction | Purpose | Example |
|---|---|---|---|
| `Content-Type` | Both | Format of body | `application/json` |
| `Authorization` | Request | Authentication credentials | `Bearer eyJ...` |
| `Cache-Control` | Both | Caching rules | `max-age=3600, public` |
| `ETag` | Response | Version identifier for caching | `"abc123"` |
| `If-None-Match` | Request | Conditional GET (send ETag) | `"abc123"` |
| `Set-Cookie` | Response | Set cookie on client | `session_id=xyz; HttpOnly; Secure` |
| `Cookie` | Request | Send cookies to server | `session_id=xyz` |
| `X-Forwarded-For` | Request | Client IP behind proxy/LB | `203.0.113.50` |
| `Retry-After` | Response | When to retry (rate limit/503) | `60` (seconds) |
| `Location` | Response | URL of new resource (201) | `/api/trips/123` |
| `CORS headers` | Response | Cross-origin permissions | `Access-Control-Allow-Origin: *` |

---

## 5. TCP vs UDP — In Depth

> **TCP = reliable delivery (order guaranteed). UDP = fast delivery (speed over reliability).**

### TCP — Transmission Control Protocol

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    Note over C,S: Connection Establishment (3-way handshake)
    C->>S: SYN (seq=100)
    S->>C: SYN-ACK (seq=300, ack=101)
    C->>S: ACK (seq=101, ack=301)
    Note over C,S: Connection Established ✅

    Note over C,S: Data Transfer (reliable)
    C->>S: Data packet 1 (seq=101, 500 bytes)
    S->>C: ACK (ack=601) "Got it, send next"
    C->>S: Data packet 2 (seq=601, 500 bytes)
    Note over S: Packet lost! ❌
    C->>S: Data packet 2 (retransmit after timeout)
    S->>C: ACK (ack=1101) "Got it"

    Note over C,S: Connection Termination (4-way handshake)
    C->>S: FIN
    S->>C: ACK
    S->>C: FIN
    C->>S: ACK
    Note over C,S: Connection Closed ✅
```

**TCP Features:**
| Feature | How It Works |
|---|---|
| **Reliability** | Acknowledgments + retransmission on timeout |
| **Ordering** | Sequence numbers ensure packets arrive in order |
| **Flow Control** | Receiver tells sender how much it can handle (window size) |
| **Congestion Control** | Slow start → detect congestion → back off (AIMD) |
| **Error Detection** | Checksum on every segment |

### UDP — User Datagram Protocol

```mermaid
sequenceDiagram
    participant C as Client (GPS Tracker)
    participant S as Server

    Note over C,S: No handshake! Just send.
    C->>S: Location: 18.52, 73.85 (t=10:00:01)
    C->>S: Location: 18.52, 73.86 (t=10:00:11)
    C->>S: Location: 18.53, 73.86 (t=10:00:21)
    Note over S: Packet 2 lost — doesn't matter!
    Note over S: Next one arrives in 10 seconds anyway.
    C->>S: Location: 18.53, 73.87 (t=10:00:31)
```

### Complete Comparison

| Feature | TCP | UDP |
|---|---|---|
| **Connection** | Connection-oriented (handshake required) | Connectionless (fire and forget) |
| **Reliability** | Guaranteed delivery with ACK | No guarantee, no retransmission |
| **Ordering** | Packets arrive in order | Packets may arrive out of order |
| **Speed** | Slower (overhead for reliability) | Faster (minimal overhead) |
| **Header Size** | 20-60 bytes | 8 bytes |
| **Flow Control** | Yes (sliding window) | No |
| **Congestion Control** | Yes (slow start, AIMD) | No |
| **Use When** | Data MUST arrive correctly | Speed > reliability |
| **Analogy** | Registered post (tracking, confirmation) | Throwing a paper airplane |

### Protocol Mapping

| Protocol | Runs On | Why |
|---|---|---|
| HTTP/1.1, HTTP/2 | TCP | Web requests must be reliable |
| HTTP/3 (QUIC) | UDP | Built reliability on top of UDP for speed |
| DNS | UDP (usually) | Small queries, speed matters, retry manually |
| WebSocket | TCP | Persistent reliable connection |
| Video Streaming | UDP (RTP) | Dropped frame < lag |
| Online Gaming | UDP | Stale position < waiting |
| SMTP (Email) | TCP | Emails must not be lost |
| GPS Tracking | UDP | Next ping in 10s makes old one irrelevant |

### Code Example: TCP Server + Client

```python
# TCP Server (simplified)
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # SOCK_STREAM = TCP
server.bind(("0.0.0.0", 8080))
server.listen(5)  # Queue up to 5 connections

print("Server listening on port 8080...")

while True:
    client_socket, address = server.accept()  # Blocks until connection
    data = client_socket.recv(1024)  # Read up to 1024 bytes
    print(f"Received from {address}: {data.decode()}")
    
    client_socket.send(b"HTTP/1.1 200 OK\r\n\r\nHello!")
    client_socket.close()
```

```python
# UDP Server (simplified) — for GPS pings
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # SOCK_DGRAM = UDP
server.bind(("0.0.0.0", 9090))

print("GPS receiver listening on port 9090...")

while True:
    data, address = server.recvfrom(512)  # No accept() — no connection!
    lat, lng, truck_id = data.decode().split(",")
    print(f"Truck {truck_id} at ({lat}, {lng})")
    # No response needed — fire and forget
```

---

## 6. Stateless vs Stateful — When to Choose What

> **Stateless = server forgets after each request. Stateful = server remembers.**

### Stateless Architecture (Default for Web)

```mermaid
sequenceDiagram
    participant C as Client
    participant LB as Load Balancer
    participant S1 as Server 1
    participant S2 as Server 2
    participant S3 as Server 3

    C->>LB: Request 1 + JWT Token
    LB->>S1: Forward (any server works)
    S1-->>C: Response

    C->>LB: Request 2 + JWT Token
    LB->>S3: Forward (different server — still works!)
    S3-->>C: Response

    Note over S1,S3: No server stores session state.<br/>JWT contains all needed info.
```

```python
# Stateless: Every request carries everything needed

# JWT token contains:
{
    "user_id": "usr_123",
    "role": "fleet_owner",
    "company_id": "comp_456",
    "exp": 1705398400  # Expiry timestamp
}

# Server doesn't need to "remember" anything
# Just decode the token → get user info → process request → respond
```

### Stateful Architecture (When You Need It)

```mermaid
sequenceDiagram
    participant C as Client (Driver App)
    participant LB as Load Balancer
    participant S2 as Server 2 (holds WebSocket)

    C->>LB: WebSocket: Connect
    LB->>S2: Route to Server 2
    S2-->>C: Connected ✅
    Note over C,S2: Persistent connection maintained

    S2->>C: Push: "New trip assigned!"
    S2->>C: Push: "Route updated!"
    C->>S2: Send: "Trip accepted"
    
    Note over LB: ALL messages from this client<br/>MUST go to Server 2
```

### Detailed Comparison

| Aspect | Stateless | Stateful |
|---|---|---|
| **State location** | Client carries state (JWT, cookies) | Server stores state (session, connection) |
| **Scalability** | Excellent — add servers freely | Limited — sticky sessions needed |
| **Load Balancing** | Any algorithm works | Need session affinity / sticky routing |
| **Server failure** | Client retries to any server | Session lost, must reconnect |
| **Memory per user** | Zero on server | Session object per user (~1-10 KB) |
| **Bandwidth** | Higher (token in every request) | Lower (session ID only) |
| **Example** | REST API + JWT | WebSocket chat, database connections |
| **Scale to 1M users** | Add more servers, zero code change | Complex: shared session store needed |

### When to Use Stateful?

```python
# Use stateful connections when ALL of these are true:
# 1. Real-time bidirectional communication needed
# 2. Server needs to push data to client unprompted
# 3. Low latency is critical (no HTTP overhead per message)

STATEFUL_USE_CASES = [
    "Real-time chat (WhatsApp, Slack)",
    "Live location tracking (showing truck on map)",
    "Multiplayer gaming",
    "Collaborative editing (Google Docs)",
    "Live sports scores / stock tickers",
    "Video/audio calls (WebRTC signaling)",
]

# For everything else → default to STATELESS
STATELESS_USE_CASES = [
    "CRUD APIs (trips, users, invoices)",
    "Authentication (login, signup)",
    "Search queries",
    "File uploads",
    "Payment processing",
    "Report generation",
]
```

### Hybrid Approach (Most Production Systems)

```
Your Smart Freight App:
├── Stateless (90% of traffic)
│   ├── REST API: Create trip, get invoices, manage fleet
│   ├── Authentication: JWT tokens
│   └── File uploads: Presigned S3 URLs
│
└── Stateful (10% of traffic, but critical)
    ├── WebSocket: Live truck location on admin dashboard
    ├── WebSocket: Real-time trip status for driver
    └── Server-Sent Events: Push notifications
```

---

## 7. DNS — The Internet's Phonebook (Deep Dive)

> **Converts human-readable domain names to IP addresses. The first thing that happens in EVERY web request.**

### Complete DNS Hierarchy

```mermaid
graph TD
    A[Root DNS Servers<br/>13 clusters worldwide<br/>Know where .com, .in, .org live] --> B[TLD Servers<br/>.com → Verisign<br/>.in → NIXI<br/>.org → PIR]
    B --> C[Authoritative DNS<br/>swiggy.com → Cloudflare<br/>smartfreight.in → Route53]
    C --> D[DNS Records<br/>A: swiggy.com → 103.97.1.1<br/>CNAME: www → swiggy.com<br/>MX: mail → mx.swiggy.com]
```

### DNS Caching Hierarchy (Why second visit is fast)

```
Request: api.smartfreight.in → ?

1. Browser cache        (Chrome stores DNS for ~60s)        → MISS
2. OS cache             (Windows/Linux DNS cache)           → MISS
3. Router cache         (Home router caches DNS)            → MISS
4. ISP Resolver cache   (Jio/Airtel recursive resolver)    → MISS
5. Root → TLD → Auth    (Full recursive resolution)        → RESOLVED!
6. Result cached at EVERY level with TTL

Next request (within TTL): Browser cache → HIT! (0ms)
```

### DNS Record Types (Complete)

| Type | Name | Points To | Use Case | Example |
|---|---|---|---|---|
| **A** | Address | IPv4 address | Main website | `smartfreight.in → 13.234.x.x` |
| **AAAA** | IPv6 Address | IPv6 address | IPv6 support | `smartfreight.in → 2600:...` |
| **CNAME** | Canonical Name | Another domain | Aliases, CDN | `www.smartfreight.in → smartfreight.in` |
| **MX** | Mail Exchange | Mail server | Email routing | `smartfreight.in → mail.google.com` |
| **NS** | Nameserver | DNS server | Delegation | `smartfreight.in → ns1.aws.com` |
| **TXT** | Text | Arbitrary text | Verification, SPF | `v=spf1 include:_spf.google.com` |
| **SRV** | Service | Host + port | Service discovery | `_sip._tcp → sip.smartfreight.in:5060` |
| **PTR** | Pointer | Domain name | Reverse DNS (IP→domain) | `1.1.97.103 → swiggy.com` |
| **SOA** | Start of Authority | Primary NS + admin | Zone metadata | Serial, refresh, retry, expire |

### DNS in System Design

```python
# DNS-based load balancing (Geo-routing)
"""
User in Mumbai → DNS resolves to Mumbai data center (ap-south-1)
User in US     → DNS resolves to Virginia data center (us-east-1)

Implementation (AWS Route 53):
  - Latency-based routing: Route to nearest AWS region
  - Geolocation routing: Route by country/continent
  - Weighted routing: 80% to v2, 20% to v3 (canary deploy)
  - Failover routing: Primary → Secondary (health check based)
"""

# TTL Strategy
"""
High TTL (86400 = 24 hours):
  ✅ Less DNS queries, faster for users
  ❌ Slow failover — takes 24h to switch traffic

Low TTL (60 = 1 minute):
  ✅ Fast failover — switch traffic in 60 seconds
  ❌ More DNS queries, slight latency increase

Production recommendation:
  - Normal operations: TTL = 300 (5 minutes)
  - Before migration: Reduce to TTL = 60 (1 minute)
  - After migration stable: Increase back to 300+
"""
```

---

## 8. Communication Patterns

> **Beyond simple request-response — know ALL the ways clients and servers can communicate.**

### Pattern Comparison

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    Note over C,S: 1. Short Polling (simple but wasteful)
    loop Every 5 seconds
        C->>S: Any new messages?
        S-->>C: No / Yes + data
    end

    Note over C,S: 2. Long Polling (better)
    C->>S: Any new messages? (hold connection open)
    Note over S: Waits until data available...
    S-->>C: Yes! Here's the data (after 30s)
    C->>S: Any new messages? (immediately reconnect)

    Note over C,S: 3. WebSocket (best for real-time)
    C->>S: Upgrade: websocket
    S-->>C: 101 Switching Protocols
    Note over C,S: Full-duplex connection ✅
    S->>C: Push: New message!
    C->>S: Send: Typing indicator
    S->>C: Push: Another message!

    Note over C,S: 4. Server-Sent Events (SSE)
    C->>S: GET /events (Accept: text/event-stream)
    S-->>C: data: {"msg": "hello"}\n\n
    S-->>C: data: {"msg": "update"}\n\n
    Note over C,S: One-way: Server → Client only
```

### Comparison Table

| Pattern | Direction | Connection | Latency | Complexity | Use Case |
|---|---|---|---|---|---|
| **Short Polling** | Client → Server | New per poll | High (poll interval) | Low | Legacy systems, simple checks |
| **Long Polling** | Client → Server | Held open | Medium | Medium | Chat (fallback), notifications |
| **WebSocket** | Bidirectional | Persistent | Very Low | High | Chat, gaming, live tracking |
| **SSE** | Server → Client | Persistent | Low | Low | News feed, stock prices, logs |
| **Webhooks** | Server → Server | New per event | Event-driven | Low | Payment callbacks, GitHub hooks |
| **gRPC Streaming** | Bidirectional | Persistent (HTTP/2) | Very Low | High | Microservice communication |

### Code Examples

```python
# WebSocket — Real-time truck tracking (your use case)
import asyncio
import websockets
import json

# SERVER: Push truck locations to dashboard
connected_admins = set()

async def handle_admin(websocket, path):
    connected_admins.add(websocket)
    try:
        async for message in websocket:
            # Admin might send commands (e.g., "focus on truck MH12AB1234")
            data = json.loads(message)
            print(f"Admin request: {data}")
    finally:
        connected_admins.remove(websocket)

async def broadcast_truck_location(truck_id, lat, lng):
    """Called when GPS ping received from truck"""
    message = json.dumps({
        "type": "location_update",
        "truck_id": truck_id,
        "lat": lat,
        "lng": lng,
        "timestamp": "2024-01-15T10:30:00Z"
    })
    # Push to ALL connected admin dashboards
    for admin in connected_admins:
        await admin.send(message)


# SSE — One-way server push (simpler than WebSocket)
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/api/trips/{trip_id}/live")
async def trip_live_updates(trip_id: str):
    """Driver app subscribes to trip status updates"""
    async def event_stream():
        while True:
            # Check for updates (in reality, use pub/sub)
            update = await get_trip_update(trip_id)
            if update:
                yield f"data: {json.dumps(update)}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

### When to Use What — Decision Tree

```
Need real-time updates?
├── NO → Use REST (standard request-response)
│
└── YES → Who needs to initiate?
    ├── Only Server → Client: Use SSE
    │   (notifications, live scores, log streaming)
    │
    ├── Both directions: Use WebSocket
    │   (chat, gaming, collaborative editing)
    │
    └── Server → Server (on event): Use Webhooks
        (payment confirmation, GitHub push events)

Still unsure? Default to:
- REST for 90% of your API
- WebSocket for truly interactive features
- SSE when you just need server push (simpler than WS)
```

---

## 9. Ports, Sockets, and Connection Management

> **A single server IP can serve thousands of different services because of ports.**

### How Ports Work

```
IP Address = Building address (123 MG Road, Pune)
Port       = Apartment number (Flat 80, Flat 443, Flat 5432)

One server (IP: 13.234.100.50) can run:
  :80    → Nginx (HTTP)
  :443   → Nginx (HTTPS)
  :3000  → NestJS app
  :5432  → PostgreSQL
  :6379  → Redis
  :9090  → Prometheus metrics
```

### Well-Known Ports

| Port | Service | Protocol |
|---|---|---|
| 20, 21 | FTP (data, control) | TCP |
| 22 | SSH | TCP |
| 25 | SMTP (email sending) | TCP |
| 53 | DNS | UDP/TCP |
| 80 | HTTP | TCP |
| 443 | HTTPS | TCP |
| 3000 | Node.js dev server | TCP |
| 3306 | MySQL | TCP |
| 5432 | PostgreSQL | TCP |
| 6379 | Redis | TCP |
| 8080 | HTTP alternate / proxy | TCP |
| 27017 | MongoDB | TCP |

### Socket — The Full Connection Identity

```python
# A socket uniquely identifies a connection:
# (Source IP, Source Port, Dest IP, Dest Port, Protocol)

# That's why a single server can handle thousands of connections:
# Each client uses a DIFFERENT source port

# Connection 1: (192.168.1.5:54321, 13.234.100.50:443, TCP)
# Connection 2: (192.168.1.5:54322, 13.234.100.50:443, TCP)  ← different source port!
# Connection 3: (203.0.113.10:48901, 13.234.100.50:443, TCP) ← different client entirely

# Maximum concurrent connections per server:
# Theoretical: 65535 ports × many client IPs = millions
# Practical: Limited by RAM, file descriptors, CPU
# Linux default: 1024 file descriptors (increase with ulimit)
# Production: 10K-100K concurrent connections is normal
```

---

## 10. Security Layer — HTTPS, TLS, Certificates

> **Every production system uses HTTPS. Understand what happens during that TLS handshake.**

### TLS Handshake (Simplified)

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    Note over C,S: TLS 1.3 Handshake (1-RTT)
    C->>S: ClientHello<br/>Supported ciphers<br/>Random number<br/>Key share (guess)
    S->>C: ServerHello<br/>Chosen cipher<br/>Certificate<br/>Key share<br/>Finished
    Note over C: Verify certificate ✅<br/>Compute shared secret
    C->>S: Finished (encrypted)
    Note over C,S: All further traffic is encrypted 🔒
```

### What TLS Protects

| Threat | Without TLS | With TLS |
|---|---|---|
| **Eavesdropping** | Attacker reads your passwords in plaintext | Encrypted — gibberish to attacker |
| **Tampering** | Attacker modifies data in transit | Integrity check detects modification |
| **Impersonation** | Attacker pretends to be your server | Certificate proves server identity |

### Certificate Chain of Trust

```
Root CA (DigiCert, Let's Encrypt)      ← Pre-installed in your browser/OS
  └── Intermediate CA                   ← Issued by Root CA
        └── Your Certificate            ← Issued by Intermediate CA
              (smartfreight.in)           (proves you own this domain)
```

```python
# In production — always verify TLS
import requests

# ✅ GOOD: Verify SSL certificate (default)
response = requests.get("https://api.smartfreight.in/health")

# ❌ BAD: Never do this in production!
# response = requests.get("https://api.smartfreight.in/health", verify=False)
```

---

## 11. Common Mistakes & Anti-Patterns

### ❌ BAD: Polling for real-time data

```python
# Client polls every 2 seconds — wastes bandwidth and server resources
while True:
    response = requests.get("/api/truck/location")
    update_map(response.json())
    time.sleep(2)  # 30 requests/minute per client!
    # 1000 drivers = 30,000 requests/minute for NOTHING if no change
```

### ✅ GOOD: Use WebSocket or SSE for real-time

```python
# Server pushes ONLY when location changes
async with websockets.connect("wss://api.smartfreight.in/ws/trucks") as ws:
    async for message in ws:
        location = json.loads(message)
        update_map(location)  # Only fires when there's actual new data
```

---

### ❌ BAD: No timeout on HTTP requests

```python
# If server hangs, your app hangs FOREVER
response = requests.get("https://api.example.com/data")  # No timeout!
```

### ✅ GOOD: Always set timeouts

```python
# Connect timeout: 3s, Read timeout: 10s
response = requests.get(
    "https://api.example.com/data",
    timeout=(3, 10)  # (connect_timeout, read_timeout)
)
```

---

### ❌ BAD: Treating network as reliable

```python
# Assumes network never fails
def create_trip(data):
    response = requests.post("/api/trips", json=data)
    return response.json()  # What if timeout? What if 500?
```

### ✅ GOOD: Retry with exponential backoff

```python
import time
import random

def create_trip_with_retry(data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post("/api/trips", json=data, timeout=10)
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                time.sleep(retry_after)
            elif response.status_code >= 500:  # Server error — retryable
                raise Exception(f"Server error: {response.status_code}")
            else:  # 4xx — client error, don't retry
                raise Exception(f"Client error: {response.status_code}")
        except (requests.Timeout, requests.ConnectionError, Exception) as e:
            if attempt == max_retries - 1:
                raise  # Give up after max retries
            # Exponential backoff with jitter
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"Retry {attempt + 1} after {wait:.1f}s: {e}")
            time.sleep(wait)
```

---

### ❌ BAD: Hardcoding server URLs

```python
# What happens when you need staging? Or the IP changes?
response = requests.get("http://13.234.100.50:3000/api/trips")
```

### ✅ GOOD: Use environment variables + DNS

```python
import os

API_BASE = os.environ.get("API_URL", "https://api.smartfreight.in")
response = requests.get(f"{API_BASE}/api/trips")
# Production: API_URL=https://api.smartfreight.in
# Staging:    API_URL=https://staging-api.smartfreight.in
# Local:      API_URL=http://localhost:3000
```

---

### ❌ BAD: Sending sensitive data in URL

```python
# Passwords/tokens in URL get logged in server access logs, browser history, proxies!
requests.get("https://api.example.com/login?password=secret123")
```

### ✅ GOOD: Use headers or request body for sensitive data

```python
# Token in header (never logged by default)
requests.get("https://api.example.com/me",
    headers={"Authorization": "Bearer eyJ..."})

# Credentials in POST body
requests.post("https://api.example.com/login",
    json={"email": "user@example.com", "password": "secret123"})
```

---

## 12. Quick Reference: Common Mistakes Table

| Mistake | Problem | Fix |
|---|---|---|
| No timeout on requests | App hangs forever if server unresponsive | Always set `timeout=(3, 10)` |
| Polling for real-time | Wastes bandwidth, overloads server | Use WebSocket or SSE |
| No retry logic | Single failure = permanent failure | Exponential backoff with jitter |
| Hardcoded URLs | Can't switch environments | Environment variables |
| Secrets in URL | Logged everywhere, visible in browser history | Use headers/body |
| Ignoring status codes | Treating errors as success | Handle 4xx/5xx properly |
| No request ID | Can't trace issues in distributed system | Generate UUID, pass in X-Request-Id |
| Trusting network | No handling for partitions, timeouts | Design for failure |
| No connection pooling | Exhausts DB/server connections | Use pool (Prisma does this) |
| Large payloads over REST | Slow, memory intensive | Pagination, compression, streaming |

---

## 13. Back-of-the-Envelope Numbers

> **Know these for estimation questions in interviews.**

### Latency Numbers Every Programmer Should Know

| Operation | Latency | Notes |
|---|---|---|
| L1 cache reference | 0.5 ns | CPU cache |
| L2 cache reference | 7 ns | |
| RAM access | 100 ns | Main memory |
| SSD random read | 150 μs (150,000 ns) | 1000x slower than RAM |
| HDD random read | 10 ms (10,000,000 ns) | 100x slower than SSD |
| Send 1 KB over 1 Gbps network | 10 μs | Local data center |
| Round trip within data center | 0.5 ms | Same region |
| DNS lookup | 20-120 ms | First time only |
| TCP handshake | 10-30 ms | 1 round trip |
| TLS handshake | 30-100 ms | 1-2 round trips |
| HTTP request (same region) | 50-200 ms | Full round trip |
| HTTP request (cross-continent) | 200-500 ms | Speed of light limitation |
| Read 1 MB from SSD | 1 ms | Sequential |
| Read 1 MB from HDD | 20 ms | Sequential |
| Read 1 MB from network | 10 ms | 1 Gbps link |

### Server Capacity Rules of Thumb

| Metric | Typical Value |
|---|---|
| Single server QPS (queries/sec) | 10K-50K (depending on work per request) |
| Single PostgreSQL | 5K-20K queries/sec |
| Single Redis | 100K-500K operations/sec |
| Single Kafka broker | 100K-1M messages/sec |
| WebSocket connections per server | 10K-100K (memory limited) |
| Nginx (reverse proxy) | 50K-100K concurrent connections |

### Data Size Rules of Thumb

| Data | Size |
|---|---|
| UUID | 36 bytes (string) / 16 bytes (binary) |
| Timestamp (ISO 8601) | 24 bytes |
| IPv4 address | 4 bytes |
| IPv6 address | 16 bytes |
| Average tweet/message | ~200 bytes |
| Average JSON API response | 1-10 KB |
| Average web page | 2-5 MB |
| 1 minute of 1080p video | ~130 MB |
| 1 million users × 1 KB profile | 1 GB |
| 1 billion rows × 100 bytes | 100 GB |

---

## 14. Interview Questions & Answer Frameworks

### Q1: "What happens when you type google.com in the browser?"

**Answer Framework (expand each as needed):**
```
1. URL Parsing       → Protocol (HTTPS), domain (google.com), path (/)
2. DNS Resolution    → Browser cache → OS → Router → ISP → Root → TLD → Auth → IP
3. TCP Connection    → 3-way handshake (SYN, SYN-ACK, ACK)
4. TLS Handshake     → ClientHello → ServerHello+Cert → Key Exchange → Encrypted
5. HTTP Request      → GET / HTTP/2, headers (cookies, user-agent)
6. Server Processing → Load balancer → App server → Search index
7. HTTP Response     → 200 OK + HTML + headers (cache-control, content-type)
8. Rendering         → Parse HTML → DOM tree → CSSOM → Render tree → Layout → Paint
9. JS Execution      → Download scripts → Parse → Execute → Hydrate
10. Subsequent loads → Service worker, prefetch, cached assets
```

### Q2: "Design a basic client-server system for [X]"

**Framework:**
```
Step 1: Requirements
  - Functional: What does the system DO?
  - Non-functional: How many users? Latency requirements? Availability?

Step 2: API Design
  - Define endpoints (REST/gRPC/GraphQL)
  - Request/Response format
  - Authentication method

Step 3: Architecture
  - Client type (web, mobile, both?)
  - Server layers (API → Service → Data)
  - Database choice (SQL vs NoSQL)
  - Caching strategy

Step 4: Communication
  - Sync (REST) vs Async (WebSocket/Queue)
  - Error handling & retries

Step 5: Scaling Considerations
  - Stateless servers for horizontal scaling
  - Read replicas for read-heavy
  - Message queues for write-heavy
```

### Q3: "How would you handle 10M daily active users?"

```
Traffic estimation:
  10M DAU × 10 requests/day = 100M requests/day
  100M / 86400 seconds = ~1,200 requests/second (avg)
  Peak (3x avg) = ~3,600 requests/second

Architecture:
  1. CDN → 60-70% traffic never hits your servers (static assets)
  2. Load Balancer → distribute across 10-20 app servers
  3. App Servers (stateless) → scale horizontally
  4. Redis Cache → 80% cache hit rate → only 20% queries hit DB
  5. Database → Read replicas for read-heavy queries
  6. Message Queue → async processing (notifications, analytics)

  Effective DB load: 3,600 × 0.30 (not cached, not CDN) × 0.20 (cache miss) = ~216 QPS
  Single PostgreSQL handles 10K+ QPS → comfortable!
```

### Q4: "Stateless vs Stateful — when to pick stateful?"

```
Default: STATELESS (REST + JWT)
  → Simpler, scales horizontally, any server handles any request

Exception — use STATEFUL when you need:
  1. Real-time bidirectional communication (chat, gaming)
  2. Server-initiated push (live notifications without polling)
  3. Persistent context (streaming connection, transaction in progress)

Hybrid: Most apps are 90% stateless REST + 10% stateful WebSocket
```

### Q5: "TCP vs UDP — give a real-world system design example"

```
GPS Fleet Tracking (Smart Freight):
  - GPS device sends location every 10 seconds
  - UDP is perfect because:
    • If one packet is lost, next one arrives in 10 seconds anyway
    • No handshake overhead (thousands of trucks sending pings)
    • Slightly stale location (20s old) is acceptable
  - TCP would waste bandwidth on ACKs for data that's immediately outdated

Payment API:
  - MUST use TCP (via HTTPS) because:
    • Every byte must arrive correctly (₹12,500.00 not ₹1,250.00)
    • Ordering matters (debit before credit)
    • Lost packet = lost money
    • Idempotency key ensures no double-charge on retry
```

---

## 15. Quick Cheat Sheet

| Concept | One-liner | When It Matters |
|---|---|---|
| Client-Server | Client requests, server responds | Foundation of web/mobile |
| OSI Model | 7 layers of networking abstraction | Understanding where things break |
| HTTP | Stateless text protocol for web | API design, caching, debugging |
| HTTP/2 | Multiplexed, compressed, server push | Performance optimization |
| TCP | Reliable, ordered delivery | APIs, file transfer, payments |
| UDP | Fast, unreliable delivery | Streaming, gaming, GPS pings |
| Stateless | Server remembers nothing between requests | Horizontal scaling |
| Stateful | Server maintains persistent connection | Real-time features |
| DNS | Domain → IP resolution | First step in every request |
| TLS/HTTPS | Encrypted communication | Security (non-negotiable) |
| Ports | Logical endpoints on a server | Running multiple services on one machine |
| Connection Pool | Reuse expensive connections | Database performance |
| Exponential Backoff | Retry with increasing delays | Resilient network calls |
| Idempotency | Same request = same result | Safe retries, payment systems |

---


