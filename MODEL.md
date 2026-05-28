# Data Model — Breathe ESG

## Design Philosophy

The data model follows a **separation of concerns** principle: raw data is stored immutably, normalized data is where business logic lives, and review actions form an append-only audit log. This means an auditor can trace any number back to the exact row in the original file.

## Entity Relationship

```
Tenant (1) ──→ (N) User
Tenant (1) ──→ (N) DataSource
Tenant (1) ──→ (N) IngestionJob
DataSource (1) ──→ (N) IngestionJob
IngestionJob (1) ──→ (N) RawRecord
RawRecord (1) ──→ (1) NormalizedRecord
NormalizedRecord (1) ──→ (N) ReviewAction
```

## Tables

### Tenant
Multi-tenancy boundary. All data is isolated by `tenant_id` — every query filters on it. This is a deliberate choice for a prototype: we use row-level isolation rather than schema-per-tenant because it's simpler to deploy on a single database.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| name | varchar(255) | e.g., "Acme Corporation" |
| slug | slug (unique) | URL-safe identifier |
| is_active | boolean | Soft-disable capability |
| created_at | timestamp | |

### User
Extends Django's AbstractUser. Uses email as the login identifier.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| tenant | FK → Tenant | Multi-tenant isolation |
| role | enum | admin, analyst, viewer |
| email | email | Used for login |
| username | varchar | Set to email by seed command |

### DataSource
Represents a configured data feed (e.g., "SAP Munich Plant", "ComEd Portal").

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| tenant | FK → Tenant | |
| source_type | enum | sap, utility, travel |
| name | varchar(255) | Human-readable label |
| config | JSON | Extensible configuration |
| created_by | FK → User | Who set it up |

### IngestionJob
Tracks a single file upload + processing run.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| tenant | FK → Tenant | |
| data_source | FK → DataSource | Which source |
| file_name | varchar(500) | Original filename |
| file_hash | varchar(64) | SHA-256 for dedup |
| status | enum | processing, completed, failed |
| total_rows | int | Rows in file |
| parsed_rows | int | Successfully parsed |
| failed_rows | int | Parse errors |
| flagged_rows | int | Anomalies detected |
| error_log | JSON | Detailed error messages |

### RawRecord
**Immutable**. Stores the original row exactly as it appeared in the file. Never modified after creation. This is the audit trail anchor.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| tenant | FK → Tenant | |
| ingestion_job | FK → IngestionJob | |
| row_number | int | Position in file |
| raw_data | JSON | The original row dict |
| parse_status | enum | success, error |
| parse_errors | JSON | What went wrong |

### NormalizedRecord
The "working copy" — cleaned, validated, and classified. This is what analysts review. One-to-one with RawRecord.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| tenant | FK → Tenant | |
| raw_record | OneToOne → RawRecord | Back-reference to original |
| source_type | enum | sap, utility, travel |
| scope | enum | scope_1, scope_2, scope_3 |
| category | varchar | diesel_fuel, electricity, flight, etc. |
| activity_date | date | When the activity occurred |
| description | text | Human-readable description |
| quantity | decimal(18,4) | Numeric value |
| unit | varchar | Normalized unit name |
| original_unit | varchar | Unit from source file |
| amount | decimal(18,2) | Monetary value |
| currency | varchar | ISO currency code |
| source_metadata | JSON | Source-specific fields |
| is_flagged | boolean | Has anomalies |
| flag_reasons | JSON | List of flag descriptions |
| flag_severity | enum | info, warning, critical |
| review_status | enum | pending, approved, rejected, locked |
| reviewed_by | FK → User | Who reviewed |
| reviewed_at | timestamp | When reviewed |
| review_comment | text | Reviewer's note |

### ReviewAction
**Append-only audit log**. Every status change, flag, or lock is recorded here. Never modified or deleted.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| normalized_record | FK → NormalizedRecord | |
| action | enum | approved, rejected, flagged, locked, etc. |
| previous_status | varchar | Status before action |
| new_status | varchar | Status after action |
| comment | text | Reviewer's note |
| performed_by | FK → User | Who did it |
| performed_at | timestamp | When |

## Key Design Decisions

1. **RawRecord is immutable** — we never modify it. This is critical for auditability: you can always compare normalized data back to what was uploaded.

2. **UUID primary keys** — no auto-increment leakage. UUIDs don't reveal record counts and work well across distributed systems.

3. **JSON fields for metadata** — each source type has different fields (SAP has plant_code, utility has meter_number, travel has airport codes). Rather than 50+ nullable columns, we store source-specific data in a JSON field. The normalized fields (quantity, unit, date, scope) are proper columns for filtering.

4. **Review status lifecycle**: `pending → approved → locked` or `pending → rejected`. Locked records cannot be modified — they're audit-ready.

5. **Tenant isolation via FK** — every query filters on `tenant_id`. This is enforced by the `TenantMiddleware` + `TenantAccessPermission`.
