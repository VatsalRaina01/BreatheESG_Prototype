# Data Model — Breathe ESG

## Core Idea

Every uploaded file goes through three stages in the database:

1. **Store it raw** — exactly as the client sent it, never touched again
2. **Clean and classify it** — produce a normalized record that analysts actually review
3. **Record every decision** — an append-only log of who approved or rejected what, and when

This means an auditor can always trace a final carbon figure back to the exact row in the original file.

---

## How the Tables Relate

```
Company (1) ──→ (many) Users
Company (1) ──→ (many) DataSources
Company (1) ──→ (many) IngestionJobs
DataSource  (1) ──→ (many) IngestionJobs
IngestionJob (1) ──→ (many) RawRecords
RawRecord    (1) ──→ (1)   NormalizedRecord
NormalizedRecord (1) ──→ (many) ReviewActions
```

---

## The Tables

### Company (Tenant)
One row per client company. Every other table has a `company_id` column so data from different companies never mixes.

| Field | What it stores |
|-------|----------------|
| id | Unique identifier (random UUID, not 1-2-3) |
| name | "Acme Corp" |
| slug | URL-safe short name, e.g. `acme-corp` |
| is_active | Lets us disable a company without deleting data |

---

### User
Standard login record. Email is the username.

| Field | What it stores |
|-------|----------------|
| id | UUID |
| company | Which company this user belongs to |
| role | `admin`, `analyst`, or `viewer` |
| email | Used for login |

---

### DataSource
Represents a specific data feed — not just "SAP" generically, but "SAP Munich Plant" or "ComEd Chicago Portal". One company can have many sources.

| Field | What it stores |
|-------|----------------|
| id | UUID |
| company | Owner company |
| source_type | `sap`, `utility`, or `travel` |
| name | Human label set by the user |
| config | JSON for any extra config (API keys, column mappings, etc.) |

---

### IngestionJob
One row per file upload. Tracks what happened during processing.

| Field | What it stores |
|-------|----------------|
| id | UUID |
| data_source | Which source this file came from |
| file_name | Original filename |
| file_hash | SHA-256 fingerprint — used to detect duplicate uploads |
| status | `processing`, `completed`, or `failed` |
| total_rows | How many rows were in the file |
| parsed_rows | How many parsed successfully |
| failed_rows | How many had parse errors |
| flagged_rows | How many were flagged as suspicious |
| error_log | JSON list of exactly what went wrong on which row |

---

### RawRecord
**Never modified after creation.** Stores the original CSV row as-is, so there is always a ground truth to refer back to.

| Field | What it stores |
|-------|----------------|
| id | UUID |
| ingestion_job | Which upload this came from |
| row_number | Which line in the file |
| raw_data | The original row as a JSON dictionary |
| parse_status | `success` or `error` |
| parse_errors | What went wrong, if anything |

---

### NormalizedRecord
The working copy that analysts see and review. One-to-one with RawRecord — every raw row gets exactly one normalized record.

| Field | What it stores |
|-------|----------------|
| id | UUID |
| raw_record | Link back to the original raw row |
| source_type | `sap`, `utility`, or `travel` |
| scope | `scope_1`, `scope_2`, or `scope_3` |
| category | `diesel_fuel`, `electricity`, `flight`, etc. |
| activity_date | When the activity happened |
| description | Plain-English description |
| quantity | The numeric value (e.g. 500) |
| unit | Normalized unit (e.g. `kWh`, `liters`) |
| original_unit | Whatever unit the source file used |
| amount | Monetary value if present |
| currency | ISO code (USD, EUR, etc.) |
| source_metadata | JSON — stores source-specific fields (meter number, PO number, airport codes, etc.) |
| is_flagged | True if the system detected something suspicious |
| flag_reasons | List of plain-English flag descriptions |
| flag_severity | `info`, `warning`, or `critical` |
| review_status | `pending`, `approved`, `rejected`, or `locked` |
| reviewed_by | Who made the decision |
| reviewed_at | When the decision was made |
| review_comment | What they said |

---

### ReviewAction
**Append-only log.** Every status change writes a new row here. Nothing is ever updated or deleted. This is the audit trail.

| Field | What it stores |
|-------|----------------|
| id | UUID |
| normalized_record | Which record was acted on |
| action | `approved`, `rejected`, `flagged`, `locked` |
| previous_status | What the status was before |
| new_status | What it changed to |
| comment | Optional note |
| performed_by | Who did it |
| performed_at | When |

---

## Four Design Rules We Followed

**1. Never touch raw data.**  
RawRecord is written once and never modified. If a parser has a bug or a normalized value is questioned, the original file row is always there for reference.

**2. Random IDs everywhere.**  
We use UUIDs instead of auto-increment numbers. This prevents leaking how many records exist and works safely if we ever need to merge databases.

**3. JSON for source-specific fields.**  
SAP has plant codes and PO numbers. Utility has meter numbers. Travel has airport codes. Rather than adding 30+ columns that are mostly empty, we store these in a `source_metadata` JSON field. The fields that analysts filter and sort by (quantity, date, scope) are proper indexed columns.

**4. Review lifecycle: pending → approved / rejected → locked.**  
`locked` is the final state. It means the record has been signed off and is ready for external auditors. Locked records cannot be changed — this is intentional.
