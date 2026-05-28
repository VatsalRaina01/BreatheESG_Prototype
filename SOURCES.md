# Sources — Breathe ESG

## Research Sources for Data Format Understanding

### SAP Export Formats

1. **SAP ME2M/MB51 Transaction Exports**
   - ME2M (Purchase Orders by Material) and MB51 (Material Document List) are the most common SAP transactions for extracting procurement data
   - Exports default to semicolon-delimited flat files with German headers when the system language is DE
   - Date format varies by SAP user settings: YYYYMMDD, DD.MM.YYYY, or YYYY-MM-DD
   - German decimal format uses comma as decimal separator: `15000,000` = 15000.0
   - Material/vendor numbers have leading zeros: `000000000050001234`
   - Source: SAP documentation, SAP Community forums, direct experience with SAP exports

2. **SAP Technical Field Names (BAPI/IDoc)**
   - EBELN (Purchase Order), EBELP (Item), MENGE (Quantity), MEINS (Unit)
   - WERKS (Plant), BUDAT (Posting Date), MATNR (Material Number)
   - These short names appear in OData/RFC exports vs. the descriptive German headers in ME2M exports
   - Source: SAP BAPI documentation, SAP Field Reference

3. **Fuel Classification for Scope 1**
   - GHG Protocol Corporate Standard defines Scope 1 as direct emissions from owned/controlled sources
   - Fuel combustion (diesel, gasoline, natural gas, propane, heating oil) is Scope 1
   - Procurement of non-fuel materials is Scope 3 (purchased goods & services)
   - Source: GHG Protocol Corporate Accounting Standard, Chapter 4

### Utility Data Formats

4. **Energy Star Portfolio Manager**
   - The most widely used tool for commercial building energy tracking in the US
   - Export format includes: Property Name, Meter Type, Start Date, End Date, Usage, Cost
   - Source: energystar.gov/buildings/tools-and-resources

5. **Green Button Data Standard**
   - US DOE initiative for standardized utility data access
   - XML format (ESPI - Energy Service Provider Interface)
   - Provides interval-level data (15-minute, hourly, daily)
   - Source: greenbuttondata.org

6. **Utility Portal CSV Exports**
   - Most utilities offer monthly CSV downloads from their customer portals
   - Common fields: Account, Meter, Service Address, Billing Period, Usage (kWh), Demand (kW), Charges
   - Key challenge: billing periods don't align with calendar months
   - Estimated reads (marked 'E' or 'Estimated') are flagged for review
   - Source: Commonwealth Edison (ComEd), Pacific Gas & Electric (PG&E), ConEdison portal documentation

7. **Scope 2 Classification**
   - GHG Protocol Scope 2 Guidance: all purchased electricity, steam, heating, cooling
   - Location-based method uses grid average emission factors
   - Market-based method uses supplier-specific factors (RECs, green tariffs)
   - Source: GHG Protocol Scope 2 Guidance (2015)

### Corporate Travel Data

8. **SAP Concur API & Exports**
   - Concur expense reports export as CSV with standardized fields
   - Key fields: Report ID, Employee, Expense Type, Date, Vendor, Amount, Currency
   - For flights: Origin/Destination (IATA codes), Cabin Class
   - Concur API v4 provides programmatic access via OAuth 2.0
   - Source: developer.concur.com/api-reference

9. **IATA Airport Codes & Distance Calculation**
   - Three-letter IATA codes used globally for airport identification
   - Haversine formula calculates great-circle distance between coordinates
   - GHG Protocol classifies flights as short-haul (<3700km) or long-haul (>3700km)
   - Different emission factors apply to each class and cabin
   - Source: IATA location codes, GHG Protocol Business Travel guidance

10. **Scope 3 Category 6: Business Travel**
    - All employee business travel (flights, rail, hotels, taxis, car rentals)
    - Distance-based method: distance × emission factor per passenger-km
    - Spend-based method: expenditure × emission factor per $ spent
    - Source: GHG Protocol Technical Guidance for Calculating Scope 3 Emissions, Category 6

### General Architecture

11. **Django REST Framework**
    - Production-grade API framework for Django
    - Built-in serialization, pagination, filtering, and authentication support
    - Source: django-rest-framework.org

12. **JWT Authentication (Simple JWT)**
    - Stateless token-based authentication for SPAs
    - Access token (short-lived) + Refresh token (long-lived) pattern
    - Source: django-rest-framework-simplejwt.readthedocs.io

13. **Railway Deployment**
    - PaaS supporting Django + PostgreSQL with zero-config deployments
    - Provides DATABASE_URL environment variable automatically
    - Source: docs.railway.app
