# Trade-offs — Breathe ESG

## What We Built vs. What Production Needs

This document honestly outlines what we deliberately didn't build and why.

### 1. Asynchronous Processing

**What we did**: Synchronous pipeline — upload blocks until processing completes.

**What production needs**: Celery + Redis for background processing. WebSocket notifications for completion. Progress bars for large files.

**Why we skipped it**: Adds 2 infrastructure dependencies (Redis, Celery worker). For <10MB files, synchronous is fast enough. The pipeline architecture is already structured for easy async extraction — `IngestionPipeline.process()` can be wrapped in a `@shared_task` with ~5 lines of code.

### 2. File Storage

**What we did**: Files are parsed in-memory and only the row data is persisted (as JSON in RawRecord).

**What production needs**: S3/GCS object storage. Store the original file for re-processing. Virus scanning. Presigned upload URLs.

**Why we skipped it**: In-memory parsing is simpler and avoids cloud storage dependency. The RawRecord JSON preserves the original data.

### 3. Emission Factor Calculation

**What we did**: Classify activity into scopes and categories. Don't compute CO2e.

**What production needs**: Emission factor database (DEFRA, EPA, IEA). CO2e = activity data × emission factor. Custom factors per tenant. Factor versioning.

**Why we skipped it**: Emission factors are a domain specialization, not a data engineering problem. The data model supports this — just add an `emission_factor` and `co2e_kg` column to NormalizedRecord.

### 4. Responsive Mobile Layout

**What we did**: Desktop-optimized layout.

**What production needs**: Responsive breakpoints. Mobile-first table views (card layout). Touch-friendly interactions.

**Why we skipped it**: Analyst review is a desktop workflow. Mobile is nice-to-have, not critical for the prototype.

### 5. Real-Time Updates

**What we did**: Manual page refresh to see new data.

**What production needs**: WebSocket subscriptions (Django Channels). Real-time dashboard counters. Push notifications.

**Why we skipped it**: Adds Django Channels + Redis dependency. Not needed for a prototype where one analyst uploads and reviews sequentially.

### 6. Advanced Search & Filtering

**What we did**: Basic filter dropdowns (source, scope, status) + text search.

**What production needs**: Date range picker. Quantity range filters. Full-text search with ranking. Saved filter presets.

**Why we skipped it**: The basic filters demonstrate the capability. The Django backend already supports all these filters via query parameters.

### 7. User Management & RBAC

**What we did**: Two roles (admin, analyst) with hardcoded permissions.

**What production needs**: Fine-grained permissions (per source type, per action). User invitation flow. SSO/SAML. Password reset. Multi-factor auth.

**Why we skipped it**: Auth is infrastructure, not the interesting part of this assignment. JWT + role field demonstrates the concept.

### 8. Error Recovery & Retries

**What we did**: Failed rows are skipped and logged. No retry mechanism.

**What production needs**: Row-level retry. Partial re-upload. Error correction UI. Duplicate detection via file hash.

**Why we skipped it**: We do log all errors with row numbers. We do compute file hashes. We just don't expose a retry UI.

### 9. Automated Testing

**What we did**: Manual testing via test_upload.py script and API exploration.

**What production needs**: Unit tests for each parser. Integration tests for the pipeline. E2E tests for the API. Frontend component tests.

**Why we skipped it**: Time constraint. The parsers are the most testable components — each has a clean input/output contract that maps well to pytest parametrize.

### 10. Data Export

**What we did**: API-only access to records.

**What production needs**: CSV/Excel export. PDF reports. Audit-ready report generation. Integration with GHG reporting tools.

**Why we skipped it**: The API returns all data needed for export. A CSV export endpoint would be ~20 lines of code.
