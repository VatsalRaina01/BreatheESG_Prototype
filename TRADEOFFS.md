# Trade-offs — Breathe ESG

This document honestly lists what I chose not to build, why I made that call, and what adding it in production would look like. Being clear about scope is not a weakness — it is engineering judgment.

---

## 1. No background task queue (no Celery / Redis)

**What exists:** Processing happens synchronously — the user uploads a file and waits for a response.

**What production needs:** A task queue (Celery) and message broker (Redis) so large file processing runs in the background. The UI would show a progress indicator and notify the user when done.

**Why I skipped it:** For files under 10MB, synchronous processing takes under 5 seconds. That covers the vast majority of real client exports. The pipeline is already a single isolated class (`IngestionPipeline.process()`) — wrapping it in a background task requires minimal restructuring.

---

## 2. No permanent file storage

**What exists:** Files are read into memory, parsed, and discarded. Only the row data is saved (as `RawRecord` in the database).

**What production needs:** Object storage (S3 or GCS) to keep the original file permanently. This allows re-parsing with updated logic, regulatory compliance, and forensic review of the exact file a client submitted.

**Why I skipped it:** Cloud storage adds an external dependency and billing. For a prototype, the `RawRecord` table preserves the original row data, which is sufficient. Adding S3 storage is an isolated change to the upload endpoint.

---

## 3. No CO2 calculation

**What exists:** Records are classified into scopes (1, 2, 3) and categories (diesel fuel, electricity, flight). The CO2 figure is not computed.

**What production needs:** An emission factor database (DEFRA, EPA, IEA by country and fuel type). The calculation is: `CO2e = quantity × emission_factor`. Factors must be versioned because they change year to year. Some clients need custom factors.

**Why I skipped it:** Emission factor management is a domain specialization and a product decision, not a data engineering problem. The data model already supports it — adding `emission_factor` and `co2e_kg` columns to `NormalizedRecord` and populating them after parsing is a well-defined next step.

---

## 4. Desktop-only layout

**What exists:** The UI is designed for wide screens — data tables, sidebar navigation, detail panels.

**What production needs:** Responsive breakpoints for tablets and phones. Card-based table views on mobile. Touch-friendly controls.

**Why I skipped it:** ESG analyst work — reviewing hundreds of rows, approving records, examining raw data — happens on desktop. Mobile is a future convenience, not a day-one requirement.

---

## 5. No real-time updates

**What exists:** Data is loaded when the page loads. The user refreshes manually to see changes.

**What production needs:** WebSocket connections (Django Channels) so the dashboard updates live when new data is processed. Push notifications when a job completes.

**Why I skipped it:** Adds Django Channels and Redis as dependencies. The current workflow — one analyst uploads, processes, reviews — is sequential and does not require live updates for a prototype.

---

## 6. Basic filtering only

**What exists:** Filter dropdowns for source type, scope, and review status. A text search field.

**What production needs:** Date range pickers, quantity range sliders, multi-value filters, full-text search with ranking, saved filter presets.

**Why I skipped it:** The basic filters demonstrate the core capability and are sufficient to navigate realistic data volumes. The backend already accepts all these as query parameters — extending the UI is a front-end task.

---

## 7. Simple role system — no fine-grained permissions

**What exists:** Two roles: `admin` and `analyst`. Admins manage sources; analysts review records.

**What production needs:** Per-source-type permissions, per-company admin delegation, SSO/SAML integration, password reset flow, multi-factor authentication.

**Why I skipped it:** The role architecture is correctly modelled and enforced. Extending to fine-grained permissions is a configuration expansion, not a structural change. SSO and MFA are infrastructure decisions made at the company level and are out of scope for a prototype.

---

## 8. No row-level retry for failed rows

**What exists:** Rows that fail to parse are skipped and logged with their row number and error reason in `IngestionJob.error_log`. The job completes for all other rows.

**What production needs:** An error correction UI where analysts can fix a bad row and resubmit it. Partial re-upload for corrected files.

**Why I skipped it:** The error log provides enough information to fix the source file and re-upload. File-level deduplication (via SHA-256 hash) prevents double-counting on re-upload.

---

## 9. No automated tests

**What exists:** A `test_upload.py` script for manual API testing. The API was validated by hand during development.

**What production needs:** Unit tests for each parser covering edge cases (German decimals, estimated reads, unknown airport codes). Integration tests for the full pipeline. Frontend component tests.

**Why I skipped it:** Time constraint. The parsers are the highest-value testing target because they have clean input/output contracts and cover the most complex logic. This is the first thing to add after the prototype is validated.

---

## 10. API access only — no data export

**What exists:** All record data is available through the REST API. Analysts view records in the browser.

**What production needs:** CSV and Excel export from the review table. Audit-ready PDF reports. Integration with GHG reporting tools like Persefoni or Watershed.

**Why I skipped it:** The API already returns all the data needed for export. A CSV download endpoint is roughly 20 lines of Django code. The harder problem — formatted audit reports — is a product design question, not a data problem.
