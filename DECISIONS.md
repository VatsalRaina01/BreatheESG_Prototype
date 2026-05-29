# Design Decisions — Breathe ESG

This document explains the key choices made while building this prototype, and the reasoning behind each one. Every decision was made deliberately — to ship something working and honest in 4 days, not to cut corners.

---

## 1. One Django app, not microservices

**What we did:** Built a single Django application with four internal apps — `core`, `ingestion`, `review`, `dashboard`.

**Why:** Microservices require service discovery, API gateways, distributed logging, and significantly more DevOps work. For a prototype, that overhead produces no benefit. The internal app boundaries are already clean, so splitting into separate services later would be a straightforward extraction.

**What we avoided:** Premature complexity. The app works, deploys as one unit, and is easy to debug.

---

## 2. Synchronous file processing — no background workers

**What we did:** When a file is uploaded, it is parsed and saved to the database in the same HTTP request. The user waits, then gets a result.

**Why:** Adding a task queue (Celery) and message broker (Redis) is two extra infrastructure dependencies. For files under 10MB — which covers most real-world SAP and utility exports — processing completes in under 5 seconds. That is acceptable for a prototype.

**Path to production:** The entire pipeline is already in one class (`IngestionPipeline.process()`). Wrapping it in a background task is about 5 lines of code. The architecture supports this without restructuring.

---

## 3. SQLite locally, PostgreSQL in production

**What we did:** Used SQLite for local development. Used `dj-database-url` so the database is swapped just by setting an environment variable.

**Why:** SQLite requires zero installation and zero setup. Every model uses standard Django fields — no Postgres-specific types. Switching databases is one environment variable change.

---

## 4. JWT authentication, not session cookies

**What we did:** Used `djangorestframework-simplejwt` to issue tokens on login. The React frontend stores the token and attaches it to every API request.

**Why:** React SPAs and session-based auth are a poor fit — sessions require sticky servers and CSRF handling. JWTs are stateless, simpler to implement, and the standard approach for this architecture.

**Acknowledged trade-off:** Tokens stored in localStorage are theoretically vulnerable to XSS. In production, we would use httpOnly cookies instead. For a prototype, this is an acceptable and well-understood trade-off.

---

## 5. Two separate tables for raw and normalized data

**What we did:** `RawRecord` stores the original CSV row as JSON, unchanged. `NormalizedRecord` stores the cleaned, classified version.

**Why:** If an analyst questions a normalized value — say, a unit conversion looks wrong — they can click "View Raw Data" and see exactly what the parser received. If a bug is found in the parser, we can re-process all raw records without asking clients to re-upload files. Mixing raw and normalized data in one table would lose this capability.

---

## 6. One parser class per source type

**What we did:** Three parser classes — `SAPParser`, `UtilityParser`, `TravelParser` — all inheriting from `BaseParser`.

**Why:** The three sources have fundamentally different parsing challenges:
- **SAP:** Semicolons, German headers, German decimal format (comma), YYYYMMDD dates, leading zeros on material numbers
- **Utility:** Billing periods that cross month boundaries, "Estimated" vs "Actual" reads, meter-to-facility mapping
- **Travel:** IATA airport codes, Haversine distance calculation, cabin class emission factors

A single universal parser would be an unmaintainable tangle of conditionals. Separate classes keep each parser focused, readable, and independently testable.

---

## 7. JSON field for source-specific metadata

**What we did:** Each `NormalizedRecord` has a `source_metadata` JSONField that stores source-specific fields (plant code for SAP, meter number for utility, airport codes for travel).

**Why:** SAP records need `plant_code`, `po_number`, `vendor_id`. Utility records need `meter_number`, `read_type`, `billing_period`. Travel records need `origin_iata`, `destination_iata`, `cabin_class`. Adding a column for each would produce a table with 30+ columns that are mostly empty for any given record type. JSON keeps the schema clean while preserving all source data.

**Trade-off:** JSON fields cannot be efficiently indexed. For a prototype, filtering by metadata is not required. In production, the most-queried metadata fields would be promoted to proper indexed columns.

---

## 8. Multi-tenancy via row-level filtering

**What we did:** Every table has a `tenant_id` foreign key. Every database query automatically filters on the logged-in user's company. This is enforced in middleware, not in individual views.

**Why:** It is the simplest multi-tenant approach that works on a single database deployment. The alternative — separate database schemas per tenant — would require schema migration tooling and significantly more complexity.

---

## 9. Three flag severity levels

**What we did:** Flags are classified as `info`, `warning`, or `critical`. The most severe flag on a record determines its visual treatment in the UI.

**Why:** Not all anomalies are equal. "Missing cost center" is worth noting but does not block review. "Negative fuel quantity" is a data error that must be resolved before sign-off. Treating all flags the same would bury critical issues in noise. Critical flags show a pulsing red dot; warnings show amber — analysts see the difference immediately.

---

## 10. Four-state review lifecycle: pending → approved / rejected → locked

**What we did:** Records move through `pending`, then `approved` or `rejected`, then optionally `locked`. Every transition is recorded in the `ReviewAction` table.

**Why:** `locked` represents a record that has been formally signed off and is ready for external auditors. Making locked records immutable prevents accidental changes after sign-off. The `ReviewAction` log means every state change has a timestamp, an actor, and an optional comment — exactly what auditors require.
