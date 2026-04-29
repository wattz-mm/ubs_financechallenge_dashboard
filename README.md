# Energy Intelligence Dashboard

Real-time AI-powered energy intelligence dashboard for the long-short thesis:

- **LONG:** Dongfang Electric (DEC)
- **SHORT:** Shanghai Electric (SHE)

The app combines live news ingestion, energy market signals, sentiment and narrative detection, macro-to-company scoring, risk alerts, and PPT-ready visual export.

## Architecture

```text
backend/   FastAPI API, ingestion, AI scoring, forecasts, alerts
frontend/  React + TypeScript + Tailwind + Mapbox GL + Recharts
```

The backend attempts live public feeds first, especially GDELT news and Yahoo chart endpoints for commodities. If a live call fails, it uses institutional-style mock data so the dashboard remains demoable.

## Quick Start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

## Optional Environment Variables

```bash
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/energy_intel
export OPENAI_API_KEY=...
export NEWS_API_KEY=...
export EIA_API_KEY=...
```

Mapbox:

```bash
cd frontend
echo "VITE_MAPBOX_TOKEN=your_public_mapbox_token" > .env.local
```

Without a Mapbox token, the dashboard falls back to a data-rich geographic canvas so the demo still works.

## Main API Routes

- `GET /api/dashboard` complete dashboard payload
- `POST /api/ingest/run` trigger live ingestion
- `GET /api/news` latest normalized headlines
- `GET /api/sentiment` time-series and regional sentiment
- `GET /api/company-signals` macro-to-company score engine
- `GET /api/forecast` electricity demand and renewable share forecast
- `GET /api/export/ppt-ready` PPT-ready chart/commentary payload

