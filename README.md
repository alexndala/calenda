# Calenda — Earnings & Corporate Actions Research Cockpit

A free Bloomberg-style research cockpit for quant/algo traders. Shows earnings, dividends, splits, and IPOs with deep per-event analytics: beat/miss history, historical ±5-day price reaction, and EPS trend.

## Stack

- **Backend**: Python FastAPI + yfinance + Alpha Vantage (free tier, IPOs only)
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + FullCalendar + Recharts

## Setup

### Backend

```bash
cd backend

# Create venv (Linux filesystem — avoids Windows/WSL issues)
uv venv ~/.cache/calenda-venv
uv pip install --python ~/.cache/calenda-venv/bin/python -r requirements.txt

# Optional: Alpha Vantage key for IPO data
cp .env.example .env
# edit .env and add your key

# Start server
~/.cache/calenda-venv/bin/uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Tests

```bash
# Backend (from backend/)
~/.cache/calenda-venv/bin/python -m pytest tests/ -v

# Frontend (from frontend/)
npm test
```

## Architecture

```
calenda/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, cache pre-warm
│   ├── models.py                # CalendarEvent + EarningsDetail (Pydantic)
│   ├── cache.py                 # Market-session-aware TTL cache
│   ├── routers/
│   │   ├── events.py            # GET /api/events, GET /api/events/{ticker}/detail
│   │   └── tickers.py           # GET /api/tickers/search, /api/indices/{index}
│   └── services/
│       ├── earnings.py          # Upcoming dates + beat/miss analytics
│       ├── price_history.py     # ±5-day price reaction (median + percentile band)
│       ├── dividends.py         # Ex-dividend dates
│       ├── splits.py            # Stock splits
│       ├── ipos.py              # Alpha Vantage IPO calendar (72h cache)
│       └── indices.py           # S&P 500 / NASDAQ 100 (Wikipedia + fallback)
└── frontend/
    ├── app/                     # Next.js app router
    ├── components/
    │   ├── CalendarView.tsx     # FullCalendar grid, max 4 chips/cell
    │   ├── AgendaView.tsx       # Sortable table
    │   ├── EventDetailPanel.tsx # 380px right-rail: beat/miss, price reaction, EPS trend
    │   ├── FilterPanel.tsx      # Universe + event type + timing filters
    │   └── TickerSearch.tsx     # Tag-style ticker autocomplete
    └── lib/
        ├── api.ts               # TanStack Query hooks
        ├── store.ts             # Zustand: universe, filters, openEventId
        └── types.ts             # Shared TypeScript types
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/events?start=&end=&index=sp500&types=earnings,dividend` | Lightweight event list |
| `GET /api/events/{ticker}/detail` | Full analytics: beat/miss, price reaction, EPS trend |
| `GET /api/indices/sp500` | S&P 500 constituent tickers |
| `GET /api/indices/nasdaq100` | NASDAQ 100 constituent tickers |
| `GET /api/tickers/search?q=AAPL` | Ticker autocomplete |
| `GET /health` | Health check |

## Notes

- **Source routing**:
  - Price/events backbone: `yfinance`
  - Fundamentals (detail endpoint only): `OpenBB` when enabled, fallback to `yfinance`
  - IPO calendar: `Alpha Vantage` (only when `ALPHA_VANTAGE_KEY` is set)
- **Provider health**: call `GET /api/sources/health` to verify active providers and key presence.
- **yfinance reliability**: ~10-15% of tickers return empty earnings history. UI shows "Insufficient history" gracefully.
- **Cold start**: ~45-60s to pre-warm S&P 500 cache on first server start. Requests hit cache after that.
- **Rate limiting**: 60 req/min on `/api/events`, 30 req/min on detail endpoint.
- **S&P 500 source**: Wikipedia `pd.read_html()` with hardcoded ~503-ticker fallback. `yf.Ticker("^GSPC")` returns index price data, not constituents.
- **Cache**: Market-session-aware — 5min TTL during trading hours, expires at next open otherwise.
