# Sources — Breathe ESG

This document lists the real-world data formats, standards, and APIs that informed how I built each parser and how I classified emissions. Every design choice in the parsers traces back to something that exists in the real world.

---

## SAP Export Formats

### ME2M and MB51 Transaction Exports
The two most common SAP transactions for extracting procurement and materials data are ME2M (Purchase Orders by Material) and MB51 (Material Document List). When exported from a German-language SAP instance, these produce semicolon-delimited flat files with German column headers.

Key format quirks I handled:
- **Decimal separator:** German format uses a comma — `15.000,50` means fifteen thousand and fifty cents, not fifteen and a half
- **Date format:** Varies by user setting — `YYYYMMDD`, `DD.MM.YYYY`, or `YYYY-MM-DD` are all common
- **Leading zeros:** Material and vendor numbers are zero-padded to 18 digits (e.g. `000000000050001234`)
- **Header language:** Columns appear as `Menge`, `Werk`, `Buchungsdatum` rather than Quantity, Plant, Posting Date

Sources: SAP Community documentation, SAP transaction field reference, SAP Germany user forums

### SAP Technical Field Names
When accessing SAP data via BAPI or IDoc (programmatic exports), field names are short codes rather than German words:
- `EBELN` — Purchase Order number
- `MENGE` — Quantity
- `MEINS` — Unit of measure
- `WERKS` — Plant code
- `BUDAT` — Posting/booking date
- `MATNR` — Material number

Sources: SAP BAPI documentation, SAP Field Reference Catalogue

### Fuel as Scope 1 Emissions
Under the GHG Protocol Corporate Standard, direct fuel combustion from company-owned or controlled sources is classified as **Scope 1**. This includes diesel, petrol, natural gas, propane, and heating oil. Procurement of non-fuel materials (office supplies, machinery parts) is **Scope 3** (purchased goods and services).

Source: GHG Protocol Corporate Accounting and Reporting Standard, Chapter 4

---

## Utility Data Formats

### Energy Star Portfolio Manager
The most widely used tool for commercial building energy tracking in the United States. Export format includes: Property Name, Meter Type, Billing Start Date, Billing End Date, Usage (kWh), and Cost. Many enterprise clients already have their electricity data here.

Source: energystar.gov/buildings/tools-and-resources

### Green Button Data
A US Department of Energy initiative that standardizes how utilities share data with customers. Data is provided as XML (ESPI format) with interval-level readings (15-minute, hourly, or daily). Our utility parser is designed to handle both CSV exports and Green Button-style billing period data.

Source: greenbuttondata.org

### Utility Portal CSV Exports
Most US utilities — ComEd, PG&E, ConEdison — allow business customers to download billing history as CSV from their online portals. Common columns are: Account Number, Meter Number, Service Address, Billing Period Start, Billing Period End, Usage (kWh), Peak Demand (kW), Total Charges.

Key challenges I address:
- **Billing periods cross month boundaries** — a bill from Nov 14 to Dec 13 cannot be naively assigned to "November"
- **Estimated reads** — meters marked 'E' or 'Estimated' are flagged for review because they may be corrected in a later bill

Sources: ComEd business portal, PG&E commercial CSV export guide, ConEdison account data documentation

### Electricity as Scope 2 Emissions
Under the GHG Protocol Scope 2 Guidance, all purchased electricity, steam, heating, and cooling is classified as **Scope 2** (indirect energy emissions). Two accounting methods exist: the location-based method (uses grid average emission factor) and the market-based method (uses supplier-specific factors like RECs). Our parser classifies the activity correctly; the calculation method is a configuration choice for the production system.

Source: GHG Protocol Scope 2 Guidance (2015 edition)

---

## Corporate Travel Data

### SAP Concur Expense Exports
Concur is the dominant corporate travel and expense platform. Expense reports export as CSV with standardized fields: Report ID, Employee Name, Expense Type, Transaction Date, Vendor, Amount, Currency. For travel-specific records, additional fields include: Origin City, Destination City, Cabin Class.

Concur also provides a programmatic API (v4) via OAuth 2.0 for direct integration without CSV files.

Source: developer.concur.com/api-reference

### IATA Airport Codes and Distance Calculation
All flight records use three-letter IATA codes (e.g. `DEL`, `LHR`, `JFK`). Flight distance is almost never included in expense data — only the airport codes. To estimate emissions I need distance.

I use the **Haversine formula** to compute great-circle distance (the shortest path over the Earth's surface) between two airports using their latitude and longitude coordinates. The GHG Protocol classifies flights as:
- **Short-haul:** under 3,700 km — applies a lower emission factor per passenger-km
- **Long-haul:** over 3,700 km — applies a higher factor, especially in business and first class

Sources: IATA airport location database, GHG Protocol Business Travel guidance

### Business Travel as Scope 3 Emissions
All employee business travel — flights, rail, hotels, taxis, rental cars — is classified as **Scope 3, Category 6** (business travel). The GHG Protocol defines two calculation methods:
- **Distance-based:** distance × emission factor per passenger-km (more accurate)
- **Spend-based:** expenditure × emission factor per dollar spent (used when distance is unavailable)

Our parser uses the distance-based method for flights (calculated via Haversine) and the spend-based method as a fallback for ground transport.

Source: GHG Protocol Technical Guidance for Calculating Scope 3 Emissions, Category 6

---

## Technology Choices

### Django REST Framework
Production-grade API layer for Django. Provides serialization, pagination, filtering, authentication, and permission classes out of the box. I use it because it is well-documented, widely deployed in production, and eliminates boilerplate without hiding important behaviour.

Source: django-rest-framework.org

### JWT Authentication (Simple JWT)
Stateless token authentication suited to single-page applications. Access tokens are short-lived; refresh tokens are long-lived. The frontend stores the access token and attaches it to every request via an Axios interceptor. No server-side session storage required.

Source: django-rest-framework-simplejwt.readthedocs.io

### Railway Deployment
Railway is a platform-as-a-service that supports Django and PostgreSQL with minimal configuration. It injects `DATABASE_URL` automatically, which our configuration reads via `dj-database-url`. Static files are handled by WhiteNoise. The entire deployment is one `railway up` command.

Source: docs.railway.app
