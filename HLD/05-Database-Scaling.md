# Database Scaling — The Hardest Problem in System Design

The database is the hardest component to scale. App servers are stateless — just add more. But databases hold your data, your source of truth. You can't just "add more databases" without solving consistency, replication lag, distributed transactions, and data partitioning. Every system design interview tests this.

---

- **Replication:** Copying data from one database server (primary) to one or more servers (replicas) for fault tolerance and read scaling.
- **Primary (Master):** The database server that handles all write operations and propagates changes to replicas.
- **Replica (Slave/Secondary):** A read-only copy of the primary database that serves read queries.
- **Replication Lag:** The delay between a write on the primary and when that write appears on a replica.
- **Synchronous Replication:** Primary waits for replica to confirm write before acknowledging to client (strong consistency, higher latency).
- **Asynchronous Replication:** Primary acknowledges write immediately and sends to replica in background (faster, risk of data loss).
- **Partitioning:** Splitting a large table's data across multiple database instances based on a key.
- **Sharding:** Horizontal partitioning of data across multiple database servers, each holding a subset of rows.
- **Shard Key:** The column used to determine which shard a row belongs to (e.g., user_id, region).
- **Vertical Partitioning:** Splitting a table's columns across databases (frequently accessed columns together).
- **Horizontal Partitioning:** Splitting a table's rows across databases (range-based, hash-based, etc.).
- **Read Replica:** A replica dedicated to serving read queries, reducing load on the primary.
- **Connection Pooling:** Maintaining a pool of reusable database connections to avoid expensive connection setup per request.
- **N+1 Query Problem:** Making N additional queries in a loop instead of fetching all data in one query with a JOIN.
- **Denormalization:** Intentionally duplicating data across tables to avoid expensive JOINs at query time.
- **Materialized View:** A precomputed query result stored as a table, refreshed periodically.
- **Hot Spot:** A shard or partition that receives disproportionately more traffic than others.
- **Consistent Hashing:** A hashing technique that minimizes data redistribution when shards are added/removed.
- **Write-Ahead Log (WAL):** A sequential log of all changes, used for crash recovery and replication.
- **ACID:** Atomicity, Consistency, Isolation, Durability — guarantees provided by traditional SQL databases.
- **BASE:** Basically Available, Soft state, Eventually consistent — the NoSQL counterpart to ACID.
- **CAP Theorem:** A distributed system can provide at most 2 of 3: Consistency, Availability, Partition Tolerance.

---

## 1. Why Database Scaling is Hard

> **App servers are stateless cattle. Databases are stateful pets. You can't just kill and replace them.**

### The Fundamental Problem

```mermaid
graph TD
    subgraph "Easy to Scale (Stateless)"
        LB[Load Balancer] --> A1[App Server 1]
        LB --> A2[App Server 2]
        LB --> A3[+ Add 10 more instantly]
    end
    
    subgraph "Hard to Scale (Stateful)"
        A1 --> DB[(Single Database<br/>All data lives here<br/>Can't just copy it)]
        A2 --> DB
        A3 --> DB
    end
```

```python
"""
Why can't you just add more databases like app servers?

1. DATA CONSISTENCY
   If you copy the DB, writes to Copy A won't appear in Copy B.
   User writes to Copy A, reads from Copy B → sees stale data!

2. DISTRIBUTED TRANSACTIONS
   Transfer ₹10,000 from Account A to Account B.
   If A is on Shard 1 and B is on Shard 2 — how do you ensure atomicity?
   What if Shard 2 crashes mid-transfer?

3. JOINs ACROSS SHARDS
   SELECT trips.*, drivers.name FROM trips JOIN drivers...
   If trips are on Shard 1 and drivers on Shard 2 — you need cross-shard JOIN.
   This is SLOW and COMPLEX.

4. REBALANCING
   You have 4 shards. Need to add a 5th.
   You must move 20% of ALL data while the system is running.
   Without downtime. Without losing transactions.
"""
```

### The Scaling Ladder (Do These In Order!)

```mermaid
graph TD
    A[Step 1: Optimize Queries<br/>Indexes, query tuning, EXPLAIN ANALYZE<br/>FREE — just better SQL] --> B[Step 2: Connection Pooling<br/>PgBouncer / Prisma pool<br/>Handles 5-10x more connections]
    B --> C[Step 3: Caching Layer<br/>Redis for hot data<br/>Reduces DB load 80-95%]
    C --> D[Step 4: Vertical Scaling<br/>More RAM, faster CPU/SSD<br/>Quick win, no code changes]
    D --> E[Step 5: Read Replicas<br/>Offload reads to copies<br/>Works for read-heavy apps]
    E --> F[Step 6: Denormalization<br/>Precompute, materialized views<br/>Trade storage for speed]
    F --> G[Step 7: Sharding<br/>Split data across DBs<br/>LAST RESORT — massive complexity]
```

### When to Do What

| Current State | Symptom | Fix | Effort |
|---|---|---|---|
| < 1K users | Everything fine | Don't touch it | None |
| 1K-10K users | Queries > 200ms | Add indexes, optimize queries | Low |
| 10K-50K users | Connection errors | Add connection pooling (PgBouncer) | Low |
| 50K-100K users | DB CPU at 70%+ | Add Redis cache layer | Medium |
| 100K-500K users | Still slow after caching | Vertical scale (bigger machine) | Low |
| 500K-2M users | Reads overwhelming primary | Add read replicas | Medium |
| 2M-10M users | Writes bottlenecked | Denormalize, CQRS, queue writes | High |
| 10M+ users | Single DB can't hold all data | Sharding | Very High |

---

## 2. Query Optimization (Step 1 — Free Performance)

> **Before you spend money on infrastructure, make your queries efficient. Most slow apps have bad queries, not infrastructure problems.**

### The EXPLAIN ANALYZE Superpower

```sql
-- ❌ BAD: Full table scan (reads ALL rows)
EXPLAIN ANALYZE
SELECT * FROM trips WHERE driver_id = 'drv_123' AND status = 'active';

-- Output: Seq Scan on trips (cost=0.00..5432.00 rows=1000000)
-- Time: 450ms 😱 (scanning 1 million rows!)

-- ✅ GOOD: After adding index
CREATE INDEX idx_trips_driver_status ON trips(driver_id, status);

EXPLAIN ANALYZE
SELECT * FROM trips WHERE driver_id = 'drv_123' AND status = 'active';

-- Output: Index Scan using idx_trips_driver_status (cost=0.42..8.44 rows=5)
-- Time: 0.3ms 🚀 (1500x faster!)
```

### Index Strategy

```sql
-- Rule: Create indexes for columns used in WHERE, JOIN, ORDER BY

-- 1. Single-column index (most common)
CREATE INDEX idx_trips_status ON trips(status);

-- 2. Composite index (multiple columns — ORDER MATTERS!)
CREATE INDEX idx_trips_owner_status_date ON trips(fleet_owner_id, status, created_at DESC);
-- ✅ Works for: WHERE fleet_owner_id = X AND status = Y ORDER BY created_at
-- ❌ Won't help: WHERE status = Y (first column must be present)

-- 3. Partial index (only index a subset of rows)
CREATE INDEX idx_active_trips ON trips(driver_id) WHERE status = 'active';
-- Smaller index, faster lookups — only indexes active trips (not the 10M completed ones)

-- 4. Covering index (includes data columns — avoids table lookup)
CREATE INDEX idx_trips_covering ON trips(fleet_owner_id, status) INCLUDE (origin, destination, eta);
-- Query can be answered entirely from index without reading the table!
```

### Common Query Anti-Patterns

```sql
-- ❌ N+1 Query Problem (most common performance killer)
-- Your code does:
SELECT * FROM trips WHERE fleet_owner_id = 'owner_1'; -- Returns 100 trips
-- Then for EACH trip:
SELECT * FROM drivers WHERE id = 'drv_1';  -- 1 query per trip
SELECT * FROM drivers WHERE id = 'drv_2';
-- ... 100 individual queries! 

-- ✅ Fix: Single query with JOIN
SELECT t.*, d.name as driver_name, d.phone 
FROM trips t
JOIN drivers d ON t.driver_id = d.id
WHERE t.fleet_owner_id = 'owner_1';
-- 1 query instead of 101!


-- ❌ SELECT * (fetches ALL columns — even blob/text you don't need)
SELECT * FROM trips; -- Fetches 50 columns including large JSON fields

-- ✅ Select only what you need
SELECT id, status, origin, destination, eta FROM trips;


-- ❌ LIKE with leading wildcard (can't use index)
SELECT * FROM drivers WHERE name LIKE '%Kumar%';  -- Full table scan!

-- ✅ Use full-text search or prefix match
SELECT * FROM drivers WHERE name LIKE 'Kumar%';   -- Can use index
-- Or better: Use pg_trgm extension or Elasticsearch for text search


-- ❌ Functions on indexed columns (index bypassed)
SELECT * FROM trips WHERE YEAR(created_at) = 2024;  -- Can't use index on created_at!

-- ✅ Use range instead
SELECT * FROM trips WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';


-- ❌ No LIMIT on large result sets
SELECT * FROM trips WHERE fleet_owner_id = 'owner_1'; -- Returns 500,000 rows!

-- ✅ Pagination
SELECT * FROM trips WHERE fleet_owner_id = 'owner_1' 
ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- ✅ Even better: Cursor-based pagination (avoids OFFSET performance degradation)
SELECT * FROM trips WHERE fleet_owner_id = 'owner_1' 
  AND created_at < '2024-01-15T10:00:00Z'  -- cursor from last page
ORDER BY created_at DESC LIMIT 20;
```

---

## 3. Connection Pooling (Step 2)

> **Opening a new database connection takes 50-100ms. If every request opens a new connection, you're wasting time and exhausting DB limits.**

### The Problem

```python
"""
PostgreSQL default: max_connections = 100

Without pooling:
  10 app servers × 20 concurrent requests = 200 connections needed
  But max is 100 → Connection refused errors!
  
  Also: Each new connection = TCP handshake + auth + SSL = 50-100ms overhead

With pooling:
  10 app servers × 5 pool connections = 50 total connections
  Each connection REUSED for thousands of requests
  Connection setup happens ONCE at startup, not per-request
"""
```

### How Connection Pooling Works

```mermaid
sequenceDiagram
    participant R1 as Request 1
    participant R2 as Request 2
    participant R3 as Request 3
    participant Pool as Connection Pool (size=5)
    participant DB as PostgreSQL

    Note over Pool,DB: App startup: Pool creates 5 connections
    Pool->>DB: Open connection 1
    Pool->>DB: Open connection 2
    Pool->>DB: Open connection 3
    Pool->>DB: Open connection 4
    Pool->>DB: Open connection 5

    R1->>Pool: Need a connection
    Pool-->>R1: Here's connection 3 (borrowed)
    R1->>DB: SELECT * FROM trips...
    DB-->>R1: Results
    R1->>Pool: Return connection 3

    R2->>Pool: Need a connection
    Pool-->>R2: Here's connection 3 (reused!)
    R2->>DB: INSERT INTO trips...
    DB-->>R2: OK
    R2->>Pool: Return connection 3
```

### PgBouncer — Production-Grade Connection Pooler

```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
smartfreight = host=127.0.0.1 port=5432 dbname=smartfreight

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5

# Pool Mode:
# session    — connection locked for entire session (safest, least efficient)
# transaction — connection returned after each transaction (DEFAULT, best balance)
# statement   — connection returned after each query (most efficient, some limitations)
pool_mode = transaction

# Pool Sizing
default_pool_size = 20        # Connections per user/database pair
max_client_conn = 1000        # Max client connections to PgBouncer
reserve_pool_size = 5         # Extra connections for surge
reserve_pool_timeout = 3      # Wait time before using reserve

# Timeouts
server_idle_timeout = 600     # Close idle server connections after 10 min
client_idle_timeout = 0       # Never disconnect idle clients
query_timeout = 30            # Kill queries running > 30 seconds
```

```python
# Prisma (your stack) has built-in connection pooling:
# DATABASE_URL="postgresql://user:pass@localhost:5432/smartfreight?connection_limit=10&pool_timeout=10"

# connection_limit: Max connections in pool (per Prisma instance)
# pool_timeout: Max wait time if all connections busy

# For production with multiple NestJS instances:
# 3 NestJS servers × 10 pool connections = 30 connections to PostgreSQL
# PostgreSQL max_connections = 100 → plenty of headroom
```

### Pool Sizing Formula

```python
# How to calculate optimal pool size:

"""
PostgreSQL rule of thumb:
  Optimal connections = (CPU cores × 2) + effective_spindle_count
  
  For SSD: effective_spindle_count ≈ 1 (SSD parallelism handled differently)
  
  Example: 8-core server with SSD
  Optimal = (8 × 2) + 1 = 17 connections
  
  More connections ≠ more throughput!
  At 17 connections: 15,000 queries/sec
  At 100 connections: 12,000 queries/sec (context switching overhead!)

PgBouncer pool size:
  = PostgreSQL optimal connections / number of PgBouncer instances
  = 17 / 1 = 17 (single PgBouncer)
  
Max client connections:
  = Number of app instances × connections per instance × safety margin
  = 5 servers × 20 connections × 2 = 200 max_client_conn
"""
```

---

## 4. Read Replicas (Step 5 — Read Scaling)

> **70-90% of database traffic is reads. Offload reads to copies of your database.**

### How Read Replication Works

```mermaid
graph TD
    subgraph "Application Layer"
        APP[App Server]
    end
    
    subgraph "Database Layer"
        PRIMARY[(Primary DB<br/>Handles ALL writes<br/>PostgreSQL Master)]
        R1[(Read Replica 1<br/>Serves reads<br/>Async copy)]
        R2[(Read Replica 2<br/>Serves reads<br/>Async copy)]
        R3[(Read Replica 3<br/>Analytics/Reports<br/>Separate workload)]
    end
    
    APP -->|"WRITE: INSERT, UPDATE, DELETE"| PRIMARY
    APP -->|"READ: SELECT"| R1
    APP -->|"READ: SELECT"| R2
    
    PRIMARY -->|"WAL Stream<br/>(replication)"| R1
    PRIMARY -->|"WAL Stream<br/>(replication)"| R2
    PRIMARY -->|"WAL Stream<br/>(replication)"| R3
```

### Synchronous vs Asynchronous Replication

```mermaid
sequenceDiagram
    participant C as Client
    participant P as Primary
    participant R as Replica

    Note over C,R: SYNCHRONOUS Replication
    C->>P: INSERT INTO trips VALUES(...)
    P->>P: Write to local WAL
    P->>R: Send WAL record
    R->>R: Apply WAL record
    R-->>P: ACK (confirmed!)
    P-->>C: 201 Created ✅
    Note over C,R: Client waits for replica to confirm.<br/>Slower but consistent.

    Note over C,R: ASYNCHRONOUS Replication
    C->>P: INSERT INTO trips VALUES(...)
    P->>P: Write to local WAL
    P-->>C: 201 Created ✅ (immediate response!)
    P->>R: Send WAL record (background)
    R->>R: Apply WAL record
    Note over C,R: Client doesn't wait for replica.<br/>Faster but replica may lag.
```

| Mode | Consistency | Write Speed | Data Loss Risk | Use Case |
|---|---|---|---|---|
| **Synchronous** | Strong (replica always current) | Slower (wait for replica ACK) | None (0 data loss) | Financial transactions, payments |
| **Asynchronous** | Eventual (replica may lag 0.1-5s) | Faster (no waiting) | Small (last few writes if primary crashes) | Most applications (DEFAULT) |
| **Semi-synchronous** | Near-strong (at least 1 replica ACK) | Medium | Minimal | Good balance for critical data |

### Replication Lag Problem

```python
"""
The Read-After-Write Consistency Problem:

Timeline:
  t=0ms:   User creates a trip (writes to PRIMARY)
  t=1ms:   Server returns "Trip created!" to user
  t=2ms:   User's dashboard page loads (reads from REPLICA)
  t=2ms:   Replica hasn't received the write yet (replication lag = 50ms)
  t=2ms:   Dashboard shows NO new trip! User is confused. 😡
  t=50ms:  Replica receives the write (now consistent)
  t=60ms:  User refreshes → NOW they see the trip
"""

# Solution 1: Read-your-writes consistency
async def get_trips_for_owner(owner_id: str, just_wrote: bool = False):
    if just_wrote:
        # User just created/updated something — read from PRIMARY
        return await primary_db.query(
            "SELECT * FROM trips WHERE fleet_owner_id = $1", owner_id
        )
    else:
        # Normal read — can use replica
        return await replica_db.query(
            "SELECT * FROM trips WHERE fleet_owner_id = $1", owner_id
        )

# Solution 2: Time-based routing
async def smart_read(query: str, user_id: str):
    last_write_time = await redis.get(f"last_write:{user_id}")
    
    if last_write_time and (time.time() - float(last_write_time)) < 5:
        # User wrote within last 5 seconds — use primary
        return await primary_db.query(query)
    else:
        # Safe to use replica
        return await replica_db.query(query)

async def on_write(user_id: str):
    # Record when this user last wrote
    await redis.setex(f"last_write:{user_id}", 10, str(time.time()))

# Solution 3: Monotonic reads (track replica position)
# Read from a specific replica that's known to be up-to-date
# PostgreSQL: pg_last_wal_replay_lsn() tells you replica's position
```

### Implementation with Prisma (Your Stack)

```typescript
// prisma/schema.prisma — defining read replicas

// NestJS service with read/write splitting
@Injectable()
export class TripService {
  constructor(
    private prismaWrite: PrismaClient,   // Points to primary
    private prismaRead: PrismaClient,    // Points to replica
  ) {}

  // Writes ALWAYS go to primary
  async createTrip(data: CreateTripDto) {
    return this.prismaWrite.trip.create({ data });
  }

  // Reads go to replica (eventual consistency OK for listing)
  async getTrips(ownerId: string) {
    return this.prismaRead.trip.findMany({
      where: { fleetOwnerId: ownerId },
      orderBy: { createdAt: 'desc' },
    });
  }

  // Critical reads go to primary (need latest data)
  async getTripForPayment(tripId: string) {
    return this.prismaWrite.trip.findUnique({
      where: { id: tripId },
    });
  }
}
```

### Read Replica Scaling Math

```python
"""
Smart Freight at scale:
  Traffic: 10,000 requests/second
  Read:Write ratio: 80:20
  
  Reads: 8,000/sec
  Writes: 2,000/sec
  
  Single PostgreSQL capacity: ~15,000 queries/sec
  
WITHOUT replicas:
  10,000 queries/sec on single DB → 67% capacity → getting close to limit
  
WITH 2 read replicas:
  Primary: 2,000 writes/sec → 13% capacity ✅
  Replica 1: 4,000 reads/sec → 27% capacity ✅
  Replica 2: 4,000 reads/sec → 27% capacity ✅
  
  Total capacity: 3 × 15,000 = 45,000 queries/sec
  You went from handling 15K to 45K queries/sec!
  
  (Actually less because replicas also apply writes, but you get the idea)
"""
```

---

## 5. Partitioning & Sharding (Step 7 — Last Resort)

> **When a single database can't hold all your data or handle all writes, split the data across multiple databases.**

### Vertical Partitioning (Split by Columns)

```mermaid
graph LR
    subgraph "Before: One big table"
        BIG[trips table<br/>id, status, origin, dest,<br/>driver_id, vehicle_id,<br/>route_geojson (5MB),<br/>cargo_manifest (2MB),<br/>invoice_pdf_url]
    end
    
    subgraph "After: Split by access pattern"
        CORE[trips_core<br/>id, status, origin, dest<br/>driver_id, vehicle_id<br/>— Accessed every request]
        HEAVY[trips_details<br/>trip_id, route_geojson,<br/>cargo_manifest<br/>— Accessed rarely]
        BILLING[trips_billing<br/>trip_id, invoice_pdf_url,<br/>amount, payment_status<br/>— Accessed by billing service]
    end
    
    BIG --> CORE
    BIG --> HEAVY
    BIG --> BILLING
```

```sql
-- Before: Single wide table (slow because large rows)
SELECT * FROM trips WHERE id = 'trip_123';
-- Returns 50 columns, 5MB of data (including geojson you don't need)

-- After: Core table is tiny and fast
SELECT id, status, origin, destination, driver_id, eta 
FROM trips_core WHERE id = 'trip_123';
-- Returns 6 columns, 200 bytes (25,000x smaller!)

-- Only fetch heavy data when specifically needed (route page)
SELECT route_geojson FROM trips_details WHERE trip_id = 'trip_123';
```

### Horizontal Partitioning (Split by Rows)

```mermaid
graph TD
    APP[Application] --> ROUTER[Shard Router<br/>Which shard has this data?]
    
    ROUTER -->|"user_id 1-250K"| S1[(Shard 1<br/>West India<br/>MH, GJ, RJ)]
    ROUTER -->|"user_id 250K-500K"| S2[(Shard 2<br/>South India<br/>KA, TN, KL)]
    ROUTER -->|"user_id 500K-750K"| S3[(Shard 3<br/>North India<br/>DL, UP, PB)]
    ROUTER -->|"user_id 750K-1M"| S4[(Shard 4<br/>East India<br/>WB, OR, JH)]
```

### Sharding Strategies

#### Strategy 1: Range-Based Sharding

```python
"""
Split data by ranges of the shard key.
Example: Shard by created_at date range.
"""

def get_shard_by_range(trip_date: str) -> str:
    year_month = trip_date[:7]  # "2024-01"
    
    SHARD_MAP = {
        "2024-01": "shard-1", "2024-02": "shard-1", "2024-03": "shard-1",
        "2024-04": "shard-2", "2024-05": "shard-2", "2024-06": "shard-2",
        "2024-07": "shard-3", "2024-08": "shard-3", "2024-09": "shard-3",
        "2024-10": "shard-4", "2024-11": "shard-4", "2024-12": "shard-4",
    }
    return SHARD_MAP.get(year_month, "shard-default")

# Pros: Range queries efficient (all data for Q1 on one shard)
# Cons: Hot spots! Current month's shard gets ALL new writes
```

#### Strategy 2: Hash-Based Sharding

```python
"""
Hash the shard key and mod by number of shards.
Distributes data evenly — no hot spots.
"""

import hashlib

def get_shard_by_hash(user_id: str, num_shards: int = 4) -> int:
    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    return hash_value % num_shards

# user_id "usr_123" → hash → shard 2
# user_id "usr_456" → hash → shard 0
# user_id "usr_789" → hash → shard 3

# Pros: Even distribution, no hot spots
# Cons: Range queries require hitting ALL shards
#        Adding shards redistributes most data (use consistent hashing to fix)
```

#### Strategy 3: Directory-Based Sharding

```python
"""
A lookup table maps each entity to its shard.
Maximum flexibility but lookup table is a SPOF.
"""

# Shard directory (stored in a separate DB or Redis)
SHARD_DIRECTORY = {
    "fleet_owner_1": "shard-west",
    "fleet_owner_2": "shard-south",
    "fleet_owner_3": "shard-north",
}

def get_shard(fleet_owner_id: str) -> str:
    return SHARD_DIRECTORY.get(fleet_owner_id, assign_new_shard(fleet_owner_id))

# Pros: Can move users between shards easily (rebalancing)
# Cons: Directory is a SPOF, lookup adds latency
```

#### Strategy 4: Geographic Sharding (Best for Smart Freight!)

```python
"""
Shard by geographic region — perfect for logistics/delivery.
Users and data are naturally isolated by region.
"""

def get_shard_by_region(state: str) -> str:
    REGION_SHARDS = {
        # West India
        "Maharashtra": "shard-west",
        "Gujarat": "shard-west",
        "Rajasthan": "shard-west",
        "Goa": "shard-west",
        
        # South India
        "Karnataka": "shard-south",
        "Tamil Nadu": "shard-south",
        "Kerala": "shard-south",
        "Andhra Pradesh": "shard-south",
        "Telangana": "shard-south",
        
        # North India
        "Delhi": "shard-north",
        "Uttar Pradesh": "shard-north",
        "Punjab": "shard-north",
        "Haryana": "shard-north",
        
        # East India
        "West Bengal": "shard-east",
        "Odisha": "shard-east",
        "Bihar": "shard-east",
        "Jharkhand": "shard-east",
    }
    return REGION_SHARDS.get(state, "shard-default")

# Why this works for logistics:
# - Trips are local (Pune → Mumbai is within West shard)
# - Drivers operate in regions (a MH driver doesn't take trips in TN)
# - Fleet owners have regional operations
# - Cross-region trips (rare) can be stored on origin shard
```

### Sharding Strategy Comparison

| Strategy | Distribution | Range Queries | Rebalancing | Hotspots |
|---|---|---|---|---|
| **Range** | Uneven (new data hits latest range) | ✅ Efficient | Easy (move ranges) | ⚠️ Latest range is hot |
| **Hash** | Even | ❌ Scatter-gather all shards | Hard (rehashing) | ✅ None |
| **Directory** | Configurable | Depends on mapping | ✅ Easy (update lookup) | Configurable |
| **Geographic** | Proportional to region activity | ✅ Within region | Medium | ⚠️ If one region dominates |

### Choosing a Shard Key

```python
"""
The shard key determines EVERYTHING. Choose wrong and you're stuck.

GOOD shard keys:
  ✅ user_id — each user's data is isolated
  ✅ fleet_owner_id — all trips for an owner on one shard
  ✅ region/state — geographic isolation
  ✅ tenant_id — for multi-tenant SaaS

BAD shard keys:
  ❌ created_at — latest shard gets all writes (hot spot)
  ❌ status — only 5 values, terrible distribution
  ❌ email — can't do range queries, no business meaning
  ❌ auto-increment id — latest shard always hot

Rules for choosing:
  1. High cardinality (many unique values)
  2. Even distribution (no shard gets 80% of traffic)
  3. Query alignment (most queries include this column in WHERE)
  4. Stability (value doesn't change — can't move rows between shards)
"""
```

---

## 6. Cross-Shard Challenges

> **Once you shard, simple operations become distributed problems.**

### Problem 1: Cross-Shard JOINs

```python
"""
Before sharding (easy):
  SELECT t.*, d.name FROM trips t JOIN drivers d ON t.driver_id = d.id
  → Single database, instant JOIN

After sharding (nightmare):
  Trips are on shard by fleet_owner_id
  Drivers are on shard by driver_id
  A trip's driver might be on a DIFFERENT shard!
"""

# Solutions:
# 1. Denormalize — store driver_name directly in trips table
# 2. Application-level JOIN — fetch from both shards, merge in code
# 3. Shared tables — keep small reference tables (drivers, vehicles) on ALL shards

async def get_trip_with_driver(trip_id: str):
    # Application-level JOIN
    trip = await shard_router.query_trip(trip_id)
    driver = await shard_router.query_driver(trip["driver_id"])
    trip["driver_name"] = driver["name"]
    return trip
    # Downside: 2 network roundtrips instead of 1 JOIN
```

### Problem 2: Cross-Shard Transactions

```python
"""
Transfer a trip from Fleet Owner A (shard-west) to Fleet Owner B (shard-north):
  1. Deduct from A's account on shard-west
  2. Credit to B's account on shard-north
  
  If step 1 succeeds but step 2 fails → money disappeared!
"""

# Solution: Saga Pattern (eventually consistent)
class TransferTripSaga:
    async def execute(self, trip_id: str, from_owner: str, to_owner: str):
        # Step 1: Reserve on source shard
        await shard_west.query(
            "UPDATE trips SET status='transferring', locked=true WHERE id=$1", trip_id
        )
        
        try:
            # Step 2: Create on destination shard
            await shard_north.query(
                "INSERT INTO trips (id, fleet_owner_id, ...) VALUES ($1, $2, ...)",
                trip_id, to_owner
            )
            
            # Step 3: Confirm on source
            await shard_west.query(
                "DELETE FROM trips WHERE id=$1", trip_id
            )
        except Exception:
            # Compensating transaction (rollback)
            await shard_west.query(
                "UPDATE trips SET status='active', locked=false WHERE id=$1", trip_id
            )
            raise
```

### Problem 3: Scatter-Gather Queries

```python
"""
"Show me all active trips across ALL regions"
Data is spread across 4 shards → must query all 4!
"""

async def get_all_active_trips() -> list:
    # Query all shards in parallel
    results = await asyncio.gather(
        shard_west.query("SELECT * FROM trips WHERE status='active'"),
        shard_south.query("SELECT * FROM trips WHERE status='active'"),
        shard_north.query("SELECT * FROM trips WHERE status='active'"),
        shard_east.query("SELECT * FROM trips WHERE status='active'"),
    )
    
    # Merge results
    all_trips = []
    for shard_result in results:
        all_trips.extend(shard_result)
    
    # Sort merged results (each shard returned sorted, but merge needed)
    all_trips.sort(key=lambda t: t["created_at"], reverse=True)
    
    return all_trips[:50]  # Return top 50

# This is expensive! Solutions:
# 1. Maintain a "global view" table updated via events
# 2. Use Elasticsearch for cross-shard searching
# 3. Cache the aggregated result
```

### Problem 4: Rebalancing (Adding a New Shard)

```python
"""
You have 4 shards, each at 80% capacity. Need to add shard 5.

With hash sharding (user_id % 4 → user_id % 5):
  20% of ALL data needs to move! While system is running!
  
With consistent hashing:
  Only ~20% of data moves (1/N of total data)
  
Rebalancing process:
  1. Add new shard (empty)
  2. Start double-writing to both old and new shard (for affected keys)
  3. Backfill historical data to new shard
  4. Verify data integrity
  5. Switch reads to new shard
  6. Stop writing to old location
  7. Clean up old data

  This takes hours/days for large datasets. Plan ahead!
"""
```

---

## 7. Denormalization — Trade Storage for Speed

> **Normalization is for data integrity. Denormalization is for performance. At scale, you need both.**

### When to Denormalize

```sql
-- NORMALIZED (3rd Normal Form): Correct but slow at scale
-- To show trip card, need 3 JOINs:

SELECT 
    t.id, t.status, t.origin, t.destination,
    d.name as driver_name, d.phone as driver_phone,
    v.plate_number, v.vehicle_type,
    fo.company_name
FROM trips t
JOIN drivers d ON t.driver_id = d.id
JOIN vehicles v ON t.vehicle_id = v.id
JOIN fleet_owners fo ON t.fleet_owner_id = fo.id
WHERE t.fleet_owner_id = 'owner_123';

-- At 10M trips, this JOIN is EXPENSIVE (50-200ms)


-- DENORMALIZED: Duplicate data for read speed
-- Single table with embedded data:

SELECT id, status, origin, destination, 
       driver_name, driver_phone,       -- duplicated from drivers table
       plate_number, vehicle_type,      -- duplicated from vehicles table
       company_name                     -- duplicated from fleet_owners table
FROM trips_denormalized
WHERE fleet_owner_id = 'owner_123';

-- No JOINs! Simple index scan (1-5ms) 🚀
```

### Denormalization Patterns

| Pattern | How | Trade-off | Use When |
|---|---|---|---|
| **Embed related data** | Store driver_name in trips table | Duplicate data, update complexity | Read-heavy, JOINs are bottleneck |
| **Precomputed aggregates** | Store trip_count in fleet_owners table | Stale counts | Dashboard showing counts |
| **Materialized views** | Precompute JOINs into a table | Storage, refresh overhead | Complex reporting queries |
| **Event-sourced projections** | Build read-optimized tables from events | Eventual consistency | CQRS architectures |

```sql
-- Materialized View Example (PostgreSQL)
CREATE MATERIALIZED VIEW fleet_dashboard AS
SELECT 
    fo.id as fleet_owner_id,
    fo.company_name,
    COUNT(t.id) as total_trips,
    COUNT(t.id) FILTER (WHERE t.status = 'active') as active_trips,
    SUM(t.revenue) as total_revenue,
    AVG(t.rating) as avg_rating
FROM fleet_owners fo
LEFT JOIN trips t ON fo.id = t.fleet_owner_id
GROUP BY fo.id, fo.company_name;

-- Create index on materialized view
CREATE INDEX idx_fleet_dashboard_owner ON fleet_dashboard(fleet_owner_id);

-- Refresh periodically (every 5 minutes)
REFRESH MATERIALIZED VIEW CONCURRENTLY fleet_dashboard;
-- CONCURRENTLY: doesn't lock reads during refresh

-- Dashboard query is now instant:
SELECT * FROM fleet_dashboard WHERE fleet_owner_id = 'owner_123';
-- 0.1ms instead of 200ms! 
```

### When NOT to Denormalize

```python
DONT_DENORMALIZE_WHEN = [
    "Write-heavy workload (updates to denormalized data are expensive)",
    "Data changes frequently (driver changes phone → update 10M trip rows?)",
    "Storage is a concern (10x duplication)",
    "Your query is fast enough with indexes (< 10ms is fine)",
    "You haven't tried caching first (Redis solves most read issues)",
    "Team can't handle the update complexity",
]

DENORMALIZE_WHEN = [
    "Read:Write ratio > 100:1 for this data",
    "JOIN queries are consistently > 100ms despite indexes",
    "Caching doesn't help (too many unique queries)",
    "Data rarely changes (fleet owner name changes once a year)",
    "You're already sharded (cross-shard JOINs impossible)",
]
```

---

## 8. CQRS — Command Query Responsibility Segregation

> **Use different models for reading and writing. Writes go to normalized DB. Reads go to optimized read store.**

### Architecture

```mermaid
graph TD
    subgraph "Write Side (Commands)"
        W_API[Write API<br/>POST /trips, PUT /trips/:id] --> W_SERVICE[Command Handler]
        W_SERVICE --> W_DB[(Write DB<br/>PostgreSQL<br/>Normalized, ACID)]
        W_SERVICE --> EVENTS[Event Bus<br/>Kafka/RabbitMQ]
    end
    
    subgraph "Read Side (Queries)"
        R_API[Read API<br/>GET /trips, GET /dashboard] --> R_SERVICE[Query Handler]
        R_SERVICE --> R_DB[(Read Store<br/>Redis / Elasticsearch<br/>Denormalized, fast)]
    end
    
    EVENTS --> PROJECTOR[Projector<br/>Updates read store<br/>when events arrive]
    PROJECTOR --> R_DB
```

```python
# Write side: Create a trip (normalized, consistent)
async def create_trip(data: CreateTripDTO):
    # Write to primary DB (normalized tables with foreign keys)
    trip = await write_db.query("""
        INSERT INTO trips (id, fleet_owner_id, driver_id, origin, destination, status)
        VALUES ($1, $2, $3, $4, $5, 'scheduled')
        RETURNING *
    """, data.id, data.fleet_owner_id, data.driver_id, data.origin, data.destination)
    
    # Publish event (for read side to consume)
    await kafka.publish("trip.created", {
        "trip_id": trip["id"],
        "fleet_owner_id": trip["fleet_owner_id"],
        "driver_name": data.driver_name,  # Include for read model
        "vehicle_plate": data.vehicle_plate,
        "origin": data.origin,
        "destination": data.destination,
    })
    
    return trip


# Read side: Projector builds denormalized read model
async def on_trip_created(event: dict):
    """Kafka consumer — updates read-optimized store"""
    await redis.hset(f"trip:{event['trip_id']}", mapping={
        "id": event["trip_id"],
        "status": "scheduled",
        "origin": event["origin"],
        "destination": event["destination"],
        "driver_name": event["driver_name"],     # Already denormalized!
        "vehicle_plate": event["vehicle_plate"],  # No JOIN needed!
    })
    
    # Also update fleet owner's trip list
    await redis.lpush(f"fleet:{event['fleet_owner_id']}:trips", event["trip_id"])


# Read side: Query is super fast (no JOINs, no DB)
async def get_trip(trip_id: str):
    return await redis.hgetall(f"trip:{trip_id}")

async def get_fleet_trips(fleet_owner_id: str):
    trip_ids = await redis.lrange(f"fleet:{fleet_owner_id}:trips", 0, 49)
    trips = []
    for tid in trip_ids:
        trips.append(await redis.hgetall(f"trip:{tid}"))
    return trips
```

### When to Use CQRS

```python
USE_CQRS_WHEN = [
    "Read and write patterns are vastly different",
    "Read queries need denormalized data (dashboards, feeds)",
    "You need different scaling for reads vs writes",
    "Complex domain logic on write side",
    "Multiple read representations needed (search, timeline, analytics)",
]

DONT_USE_CQRS_WHEN = [
    "Simple CRUD app",
    "Team is small (1-3 devs) — complexity isn't justified",
    "Strong consistency required everywhere",
    "You haven't tried simpler solutions (caching, read replicas)",
]
```

---

## 9. Database Types — SQL vs NoSQL at Scale

> **Different data models for different problems. No single database fits all use cases.**

### Complete Comparison

| Feature | SQL (PostgreSQL) | Document (MongoDB) | Key-Value (Redis) | Wide-Column (Cassandra) | Graph (Neo4j) |
|---|---|---|---|---|---|
| **Data Model** | Tables, rows, columns | JSON documents | Key → Value | Column families | Nodes, edges |
| **Schema** | Strict (predefined) | Flexible (schemaless) | None | Semi-structured | Nodes + relationships |
| **Query** | SQL (JOINs, aggregations) | JSON queries | GET/SET | CQL (SQL-like) | Cypher |
| **Consistency** | Strong (ACID) | Configurable | Strong (single key) | Eventual (tunable) | ACID |
| **Scale** | Vertical (hard to shard) | Horizontal (auto-shard) | Horizontal (cluster) | Horizontal (designed for it) | Vertical mostly |
| **Best For** | Complex relations, transactions | Variable schema, rapid iteration | Caching, sessions, real-time | Time-series, high write throughput | Social networks, recommendations |

### When to Use What

```python
DATABASE_SELECTION = {
    "PostgreSQL (SQL)": {
        "use_when": [
            "Complex relationships between entities (trips ↔ drivers ↔ vehicles)",
            "Need ACID transactions (payments, invoices)",
            "Complex queries with JOINs and aggregations",
            "Data has a well-defined, stable schema",
            "Need strong consistency",
        ],
        "examples": "User accounts, orders, financial records, ERP systems"
    },
    
    "MongoDB (Document)": {
        "use_when": [
            "Schema varies per document (different trip types have different fields)",
            "Rapid prototyping (schema can evolve without migrations)",
            "Embedded/nested data (trip with all checkpoints as subdocument)",
            "Need horizontal scaling with auto-sharding",
        ],
        "examples": "Content management, product catalogs, IoT sensor data"
    },
    
    "Redis (Key-Value)": {
        "use_when": [
            "Need sub-millisecond latency",
            "Caching layer",
            "Session storage",
            "Real-time counters and leaderboards",
            "Pub/sub messaging",
            "Rate limiting",
        ],
        "examples": "Cache, sessions, real-time location, online status"
    },
    
    "Cassandra (Wide-Column)": {
        "use_when": [
            "Massive write throughput (100K+ writes/sec)",
            "Time-series data (GPS pings, logs, metrics)",
            "Need to operate across multiple data centers",
            "Can tolerate eventual consistency",
            "Data is append-heavy (rarely updated)",
        ],
        "examples": "GPS tracking history, event logs, metrics, messaging"
    },
    
    "Elasticsearch (Search)": {
        "use_when": [
            "Full-text search",
            "Complex filtering and aggregations on large datasets",
            "Auto-complete / typeahead",
            "Log analysis and monitoring",
        ],
        "examples": "Search, log analysis, analytics dashboards"
    },
    
    "Neo4j (Graph)": {
        "use_when": [
            "Heavily interconnected data",
            "Relationship queries (friends of friends, recommendations)",
            "Fraud detection (finding cycles/patterns)",
            "Knowledge graphs",
        ],
        "examples": "Social networks, recommendation engines, fraud detection"
    },
}
```

### Smart Freight — Multi-Database Architecture

```python
SMART_FREIGHT_DATABASES = {
    "PostgreSQL (Primary)": {
        "stores": "Trips, drivers, vehicles, fleet owners, invoices, payments",
        "why": "Relational data, ACID for financial operations, Prisma ORM",
    },
    "Redis": {
        "stores": "Real-time truck locations, sessions, rate limits, cache",
        "why": "Sub-ms reads, pub/sub for live tracking, ephemeral data",
    },
    "Elasticsearch (future)": {
        "stores": "Trip search index, driver search, route optimization",
        "why": "Full-text search, geo queries, complex filtering",
    },
    "TimescaleDB or Cassandra (future)": {
        "stores": "GPS history (millions of points per day)",
        "why": "Time-series optimized, auto-partitioning by time",
    },
}
```

---

## 10. Database Scaling at Scale — Real Company Examples

### Instagram (PostgreSQL at Scale)

```
Scale: 2 billion+ monthly active users

Strategy:
  - PostgreSQL sharded by user_id
  - ~20 shards (logical), hundreds of physical machines
  - Uses Vitess (database clustering system) for management
  - Read replicas per shard (3-5 replicas each)
  - Memcached/Redis for caching layer
  
Key Insight: 
  "We stayed on PostgreSQL because our data is highly relational 
   (users, posts, likes, follows, comments) and we need transactions."
```

### Uber (Mixed Database Architecture)

```
Scale: 20M+ rides/day, 5M drivers globally

Databases:
  - MySQL/PostgreSQL: User data, trip records (sharded by city)
  - Cassandra: Real-time driver locations (massive write throughput)
  - Redis: Caching, real-time matching, surge pricing
  - Elasticsearch: Trip search, driver search
  - Custom in-memory: Geospatial matching (H3 hexagonal grid)
  
Key Insight:
  "No single database can handle all our needs. We use 
   the right tool for each job."
```

### Discord (Cassandra → ScyllaDB)

```
Scale: 150M+ monthly active users, trillions of messages

Problem: Cassandra couldn't handle their message read patterns.
  - Message tables were growing to billions of rows
  - Hot channels caused partition hotspots
  
Solution: Migrated to ScyllaDB (C++ rewrite of Cassandra)
  - 4x lower latency (p99 from 40ms to 10ms)
  - Consistent performance at scale
  
Data model: Messages partitioned by (channel_id, bucket)
  - bucket = time-based (1 bucket per 10 days)
  - Avoids infinite partition growth
```

---

## 11. Common Mistakes & Anti-Patterns

### ❌ BAD: Sharding too early

```python
# Day 1: 100 users, 5,000 rows
# Developer: "Let me set up a 4-shard cluster for future scale!"
# 
# Result:
# - 2 months of engineering time setting up sharding
# - Cross-shard JOIN bugs
# - 4x infrastructure cost
# - Product development completely stalled
# - Competitors launched while you were configuring databases
```

### ✅ GOOD: Scale when metrics demand it

```python
# Scale only when:
# - DB CPU consistently > 70%
# - Query latency > 200ms after index optimization
# - Storage > 80% full
# - Connection pool exhausted regularly
#
# Order: Indexes → Pooling → Cache → Vertical → Replicas → Shard
```

---

### ❌ BAD: No indexes on frequently queried columns

```sql
-- Table has 10M rows, query runs 50 times/second with no index:
SELECT * FROM trips WHERE fleet_owner_id = 'owner_123' AND status = 'active';
-- Full table scan: 3 seconds! Server melting!
```

### ✅ GOOD: Indexes based on actual query patterns

```sql
-- Check which queries are slow:
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;

-- Add targeted index:
CREATE INDEX idx_trips_owner_status ON trips(fleet_owner_id, status)
WHERE status IN ('active', 'scheduled');
-- Now: 0.3ms ✅
```

---

### ❌ BAD: Using database as a queue

```python
# Polling a table for "pending" jobs:
while True:
    jobs = db.query("SELECT * FROM jobs WHERE status = 'pending' LIMIT 10 FOR UPDATE")
    for job in jobs:
        process(job)
        db.query("UPDATE jobs SET status = 'done' WHERE id = $1", job.id)
    time.sleep(1)

# Problems:
# - Constant polling wastes DB resources
# - FOR UPDATE locks cause contention
# - Not designed for high-throughput queuing
```

### ✅ GOOD: Use a proper message queue

```python
# Use Redis (BullMQ), RabbitMQ, or Kafka for job processing
# Database stores results, queue handles the workflow

await queue.add("process-trip", { trip_id: "trip_123" })

# Worker picks up job (no polling, event-driven):
@worker.process("process-trip")
async def handle(job):
    trip = await db.query("SELECT * FROM trips WHERE id = $1", job.data.trip_id)
    result = process_trip(trip)
    await db.query("UPDATE trips SET result = $1 WHERE id = $2", result, trip.id)
```

---

### ❌ BAD: Not handling replication lag

```python
# User creates trip → immediately redirected to trip page
# Trip page reads from replica → trip not there yet (lag!)
# User sees "Trip not found" error 😡
```

### ✅ GOOD: Read-your-writes consistency

```python
# After a write, direct that user's reads to primary for 5 seconds
async def create_trip(user_id: str, data: dict):
    trip = await primary_db.create(data)
    await redis.setex(f"read_primary:{user_id}", 5, "1")  # 5 second window
    return trip

async def get_trips(user_id: str):
    force_primary = await redis.get(f"read_primary:{user_id}")
    db = primary_db if force_primary else replica_db
    return await db.query("SELECT * FROM trips WHERE owner_id = $1", user_id)
```

---

## 12. Quick Reference: Mistakes Table

| Mistake | Problem | Fix |
|---|---|---|
| Sharding too early | Wasted months, massive complexity | Exhaust simpler options first |
| No indexes | Full table scans, 1000x slower | Index columns in WHERE/JOIN/ORDER BY |
| No connection pooling | Connection exhaustion, timeouts | PgBouncer or Prisma built-in pool |
| DB as message queue | High contention, constant polling | Use Redis/BullMQ/Kafka |
| Ignoring replication lag | Users see stale data after writes | Read-your-writes pattern |
| SELECT * everywhere | Fetches unnecessary data | Select only needed columns |
| N+1 queries | 100 queries instead of 1 | Use JOINs or eager loading |
| No monitoring | Don't know what's slow | pg_stat_statements, slow query log |
| Same DB for OLTP and OLAP | Analytics queries kill production | Separate analytics replica |
| Unbounded queries | SELECT with no LIMIT returns 1M rows | Always paginate |

---

## 13. Back-of-the-Envelope: Database Sizing

```python
"""
Smart Freight Database Sizing (1 year):

Users:
  Fleet owners: 10,000 × 2 KB = 20 MB
  Drivers: 50,000 × 1 KB = 50 MB
  Vehicles: 30,000 × 0.5 KB = 15 MB

Trips:
  100K trips/month × 12 months = 1.2M trips
  1.2M × 2 KB per trip = 2.4 GB

GPS Locations:
  50K drivers × 6 pings/min × 60 min × 12 hours × 365 days
  = 50K × 6 × 60 × 12 × 365 = 11.8 BILLION rows/year
  × 50 bytes per row = 590 GB/year
  → THIS is why you need TimescaleDB/Cassandra for GPS!

Invoices:
  1.2M × 5 KB = 6 GB

Total (excluding GPS): ~10 GB → Single PostgreSQL handles easily
GPS data: 590 GB/year → Needs time-series DB + auto-partitioning

Queries Per Second:
  Reads: 50K drivers checking status × 1 req/10s = 5,000 reads/sec
  Writes: GPS pings = 50K × 0.1/sec = 5,000 writes/sec
  
  10,000 total QPS → Single PostgreSQL can handle with good indexes + connection pool
  GPS writes → Batch + write to TimescaleDB (designed for this)
"""
```

---

## 14. Interview Questions & Answer Frameworks

### Q1: "How do you scale a database?"

```
Step-by-step approach (always in this order):

1. Query optimization — indexes, EXPLAIN ANALYZE, fix N+1
   (Free, biggest impact)

2. Connection pooling — PgBouncer, 10x more connections
   (Easy, no code changes)

3. Caching — Redis for hot data, 80-95% less DB traffic
   (Medium effort, massive impact)

4. Vertical scaling — bigger machine (more RAM, SSD, CPU)
   (Quick, but has ceiling)

5. Read replicas — offload 70-90% of queries to replicas
   (Medium effort, linear read scaling)

6. Denormalization / CQRS — separate read and write models
   (High effort, eliminates expensive JOINs)

7. Sharding — split data across multiple databases
   (Very high effort, LAST resort)
```

### Q2: "When would you use NoSQL over SQL?"

```
Choose SQL (PostgreSQL) when:
  - Data is relational (references between entities)
  - Need ACID transactions (financial operations)
  - Complex queries with JOINs and aggregations
  - Schema is well-defined and stable

Choose NoSQL when:
  - Document DB (MongoDB): Variable schema, rapid prototyping
  - Key-Value (Redis): Caching, sessions, real-time data
  - Wide-Column (Cassandra): Massive writes, time-series
  - Graph (Neo4j): Relationship queries (social, recommendations)

Most systems use BOTH:
  PostgreSQL for core data + Redis for caching + Elasticsearch for search
```

### Q3: "What is sharding and when do you need it?"

```
Sharding = splitting rows across multiple database servers.

When to shard:
  - Single DB can't hold all data (> 1-5 TB)
  - Write throughput exceeds single DB capacity (> 50K writes/sec)
  - You've exhausted all other options (vertical, replicas, caching)

How to choose shard key:
  - High cardinality (many unique values)
  - Even distribution (no hot spots)
  - Query-aligned (most queries include shard key in WHERE)
  - Examples: user_id, region, tenant_id

Challenges after sharding:
  - Cross-shard JOINs (use denormalization)
  - Distributed transactions (use Saga pattern)
  - Scatter-gather queries (use aggregation service)
  - Rebalancing when adding shards (use consistent hashing)
```

### Q4: "How do you handle read-after-write consistency with replicas?"

```
Problem: User writes to primary, reads from replica, doesn't see own write.

Solutions:
1. Read from primary for N seconds after write
   - Track last_write_time per user in Redis
   - If within 5s, route reads to primary

2. Causal consistency
   - Write returns a version/timestamp
   - Client sends version with subsequent reads
   - Replica serves request only if it has that version

3. Synchronous replication (strongest but slowest)
   - Primary waits for replica ACK before responding
   - Guaranteed consistency but higher write latency

4. Client-side cache
   - After write, client caches result locally
   - Shows local data while replica catches up
```

### Q5: "Design the database architecture for a ride-sharing app"

```
Core tables (PostgreSQL — primary):
  - users (riders + drivers)
  - trips (ride records, status)
  - payments (transactions)
  - vehicles

Read-optimized (Redis):
  - Real-time driver locations (GEO data structure)
  - Active ride status
  - Surge pricing cache
  - Rate limiting counters

Search (Elasticsearch):
  - Driver search by name/plate
  - Trip history search

Time-series (Cassandra/TimescaleDB):
  - GPS location history (billions of points)
  - Driver telemetry (speed, fuel, hours)

Scaling strategy:
  Phase 1: Single PostgreSQL + Redis
  Phase 2: Read replicas (2x), bigger Redis
  Phase 3: Shard PostgreSQL by city/region
  Phase 4: Cassandra for GPS (write-heavy)
```

---

## 15. Quick Cheat Sheet

| Concept | One-liner | Key Takeaway |
|---|---|---|
| Read Replicas | Read-only copies of primary DB | Scale reads linearly |
| Replication Lag | Delay between primary and replica | Read-your-writes to mitigate |
| Connection Pooling | Reuse DB connections | 10x more concurrent connections |
| Sharding | Split rows across databases | Last resort, massive complexity |
| Shard Key | Column that determines which shard | Must be high-cardinality, even, stable |
| Denormalization | Duplicate data to avoid JOINs | Trade storage for read speed |
| CQRS | Separate read and write models | Different DBs for reading vs writing |
| Materialized View | Precomputed query as table | Instant dashboards |
| Vertical Partitioning | Split columns across tables | Separate hot from cold data |
| Horizontal Partitioning | Split rows across tables/DBs | = Sharding |
| N+1 Problem | Loop of individual queries | Fix with JOIN or eager loading |
| ACID | Atomicity, Consistency, Isolation, Durability | SQL guarantee |
| CAP Theorem | Can't have all 3: C, A, P | Choose CP or AP |
| Saga Pattern | Distributed transaction via compensating actions | Cross-shard consistency |
