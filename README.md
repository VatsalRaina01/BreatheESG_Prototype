# Breathe ESG — Emissions Data Ingestion & Review Platform

A Django REST + React application that ingests emissions data from three enterprise sources (SAP, Utility portals, Corporate Travel platforms), normalizes it, and provides an analyst review dashboard for audit-ready approval.

## Architecture

- **Backend**: Django 5 + Django REST Framework + PostgreSQL
- **Frontend**: React 18 + Vite
- **Auth**: JWT (djangorestframework-simplejwt)
- **Deployment**: Railway

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Demo Credentials
- **Admin**: admin@breatheesg.com / admin123
- **Analyst**: analyst@breatheesg.com / analyst123

## Data Sources

| Source | Format | Scope |
|--------|--------|-------|
| SAP (Fuel & Procurement) | Semicolon-delimited flat file, German headers | Scope 1 & 3 |
| Utility (Electricity) | Portal CSV export | Scope 2 |
| Corporate Travel | Concur-style CSV export | Scope 3 |

## Documentation

- [MODEL.md](MODEL.md) — Data model design and rationale
- [DECISIONS.md](DECISIONS.md) — Ambiguity resolution and design choices
- [TRADEOFFS.md](TRADEOFFS.md) — What we deliberately didn't build
- [SOURCES.md](SOURCES.md) — Research on real-world data source formats
