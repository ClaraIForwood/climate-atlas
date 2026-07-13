# Climate Atlas

[![CI](https://github.com/ClaraIForwood/climate-atlas/actions/workflows/ci.yml/badge.svg)](https://github.com/ClaraIForwood/climate-atlas/actions/workflows/ci.yml)

**[Live demo →](https://claraforwood.com/climate-atlas)**

An interactive map of projected temperature and precipitation change across ~17,000 land grid cells worldwide, through 2080 — built on real CMIP6 climate model output, layered with country-level climate vulnerability and readiness scores.

<!-- Screenshot/GIF here — a wide shot of the map mid-interaction (year slider partway, a layer toggled on) is the single highest-value addition to this README. -->

## What this is

A personal data engineering project exploring how climate projections and vulnerability data can be combined into something explorable rather than buried in a PDF. It's also a demonstration project: the interesting engineering problems here are a real scientific data pipeline (fetch → transform → validate), not just a frontend map.

Two things this project explicitly does **not** do: it doesn't project city-level or hyperlocal outcomes (data is grid- and country-level only), and it doesn't attribute regional patterns to specific physical mechanisms beyond what a single climate model's surface variables can support — see [Methodology](#methodology--honest-limitations) below.

## Key features

- **Real CMIP6 data**, not synthetic or illustrative — MRI-ESM2-0 model output under the SSP2-4.5 ("middle of the road") emissions scenario
- **Temperature and precipitation anomalies** for ~17,000 land-only grid cells, across 6 decades (2030–2080), each expressed relative to a 1990–2014 historical baseline
- **Country-level climate vulnerability & readiness scores** (ND-GAIN index) for 164 of 177 countries, joined via ISO_A3 country codes
- **Fully static architecture** — no backend, no live API calls at runtime; everything is pre-computed offline and served as static GeoJSON
- **CI pipeline** (GitHub Actions) validating both the data pipeline's output and the frontend build on every push

## Architecture

Data flows through four stages, each handing off to the next:

1. **Fetch** (manual) — pulls raw CMIP6 NetCDF from the Copernicus CDS API, plus ND-GAIN country scores and Natural Earth boundaries
2. **Transform** (`process.py`) — joins, computes temperature/precipitation anomalies, land-masks, converts units → `public/data/*.geojson` (14 files, ~17k cells × 6 decades)
3. **Validate** (`check.py`) — CI gate, runs in GitHub Actions on every push
4. **Serve** — MapLibre GL JS reads the static files directly; no server-side compute at request time

The pipeline runs offline/locally, not at request time — see [Methodology](#methodology--honest-limitations) for why static pre-processing is the deliberate choice here, not a shortcut.

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | React 18, Vite, MapLibre GL JS, Zustand, Tailwind CSS |
| Data pipeline | Python, xarray, geopandas, scipy (KDTree spatial joins), Copernicus CDS API |
| CI/CD | GitHub Actions (pipeline validation + frontend build) |
| Hosting | Vercel (static deploy) |

## Methodology & honest limitations

- Projections come from a **single climate model** (MRI-ESM2-0) under **one emissions scenario** (SSP2-4.5) — not a multi-model ensemble. Regional patterns (e.g. spatial gradients within a country) reflect that one model's internal variability and should be read as illustrative of *a* plausible trajectory, not a consensus forecast.
- The pipeline uses **surface variables only** (temperature, precipitation) — it does not model, and this project does not claim to explain, underlying physical drivers like ocean circulation.
- ND-GAIN vulnerability/readiness scores are a **composite index** with inherent weighting choices, following the same precedent as indices like the UN HDI.
- Full methodology detail is available in-app via the "i" panel next to the map.

## Getting started

**Frontend** (uses the pre-built data already committed to `public/data/` — no pipeline run required):
```bash
npm install
npm run dev
```

**Data pipeline** (only needed if you want to regenerate the data yourself):
```bash
cd pipeline
pip install -r requirements.txt
pip install xarray cdsapi netCDF4 pip-system-certs   # CMIP6 fetch dependencies
# Requires a free Copernicus CDS API key — see fetch_cmip6_fixed.py docstring
python fetch_cmip6_fixed.py   # temperature
python fetch_cmip6_pr.py      # precipitation
python process.py
python check.py               # validates output before deploy
```

## Project structure

- **`pipeline/`** — data pipeline: fetch → process → validate
- **`public/data/`** — pre-computed GeoJSON served to the frontend
- **`src/components/`** — map, controls, legend, info panel
- **`src/hooks/`** — data loading, URL state sync
- **`src/store/`** — Zustand global state
- **`src/services/`** — static data fetching

## Roadmap

- SQL-based joins and window-function analytics (DuckDB)
- Vector tile performance optimization
- TypeScript migration
- Architecture Decision Records for key design choices

## License

[MIT](LICENSE) <!-- add a LICENSE file if you haven't yet — this line currently references one that doesn't exist --
