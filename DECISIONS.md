# Design Decisions — Breathe ESG

## 1. Monolith over Microservices

**Decision**: Single Django application with a clean app structure (core, ingestion, review, dashboard).

**Why**: For a 4-day prototype, microservices add deployment complexity (service discovery, API gateways, distributed debugging) without any benefit. The monolith lets us iterate fast and deploy as one unit. The app boundaries are clean enough that extraction would be straightforward if needed.

**Alternative considered**: Separate ingestion service. Rejected because the pipeline is synchronous and fast enough for prototype file sizes (<10MB).

## 2. Synchronous Pipeline (No Celery/Redis)

**Decision**: File upload → parse → normalize → persist all happens in one synchronous HTTP request.

**Why**: Celery + Redis adds infrastructure complexity. For files <10MB (~50k rows), synchronous processing completes in <5 seconds. This is acceptable for a prototype. The trade-off is that very large files (>100k rows) would block the request.

**What we'd add in production**: Celery task queue with Redis broker. The upload endpoint would return immediately with a `job_id`, and a background worker would process the file. We'd add WebSocket notifications for completion.

## 3. SQLite for Development, PostgreSQL-Ready

**Decision**: Use SQLite locally with `dj-database-url` for easy PostgreSQL switch in production.

**Why**: Zero setup for development. All models use standard Django fields (no Postgres-specific types). JSON fields work in both SQLite (Django 5.x) and PostgreSQL. Switch to Postgres by setting `DATABASE_URL` env var.

## 4. JWT Authentication (Not Session-Based)

**Decision**: djangorestframework-simplejwt for stateless JWT auth.

**Why**: The frontend is a React SPA making API calls. JWT works naturally with this pattern: store tokens in localStorage, attach to requests via interceptor. No server-side session storage needed.

**Security trade-off**: Tokens in localStorage are vulnerable to XSS. In production, we'd use httpOnly cookies. For a prototype, this is acceptable.

## 5. Separate RawRecord from NormalizedRecord

**Decision**: Two-table design — RawRecord stores the original CSV row as JSON, NormalizedRecord stores the cleaned/classified version.

**Why**: Auditability. If an analyst questions a normalized value, they can view the raw data and see exactly what the parser received. If a parser has a bug, we can re-process from raw records without re-uploading.

**Alternative considered**: Single table with both `raw_json` and structured columns. Rejected because it mixes concerns and makes migrations harder.

## 6. Source-Specific Parsers with a Common Interface

**Decision**: Three separate parser classes (SAPParser, UtilityParser, TravelParser) inheriting from BaseParser.

**Why**: Each source has fundamentally different challenges:
- SAP: German headers, semicolons, YYYYMMDD dates, comma decimals
- Utility: billing periods, estimated reads, meter numbers
- Travel: airport codes, Haversine distance, cabin classes

A "universal parser" would be a mess of if/else. Separate parsers keep each one focused and testable.

## 7. JSON Fields for Source Metadata

**Decision**: `source_metadata` is a JSONField rather than 30+ nullable columns.

**Why**: SAP records have `plant_code`, `po_number`, `vendor`. Utility records have `meter_number`, `read_type`, `billing_period_start`. Travel records have `origin`, `destination`, `cabin_class`. These fields are different per source type. JSON keeps the schema clean while preserving all source-specific data.

**Trade-off**: Can't filter on metadata fields via SQL indexes. For a prototype, this is fine. In production, we'd add dedicated columns for the most queried fields.

## 8. Tenant-per-Row Isolation

**Decision**: All tables have a `tenant_id` FK. Every queryset filters on `request.user.tenant`.

**Why**: Simplest multi-tenant approach. Single database, single deployment. The TenantMiddleware + TenantAccessPermission enforce this automatically.

**Alternative considered**: Schema-per-tenant (separate Postgres schemas). Too complex for a prototype.

## 9. Flag Severity Levels (Info/Warning/Critical)

**Decision**: Three severity levels for anomaly flags, with the most severe determining the row's overall severity.

**Why**: Not all flags are equal. "Missing cost center" (info) shouldn't get the same visual treatment as "Negative usage" (critical). The severity drives the UI: critical flags show red pulsing dots, warnings show amber.

## 10. Review Workflow: Pending → Approved/Rejected → Locked

**Decision**: Four-state lifecycle with "locked" as a terminal state.

**Why**: "Locked" means the record has been signed off and is ready for auditors. Locked records cannot be modified — this prevents accidental changes after sign-off. The ReviewAction table records every transition for the audit trail.
