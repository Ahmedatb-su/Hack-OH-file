# BuckeyeQueue frontend

Responsive React + Vite frontend for the BuckeyeQueue FastAPI backend. Features: browse/search campus buses and food courts; live occupancy, threshold color/status; per-location 12-hour forecast; WebSocket live updates, 30-second fallback refresh; automatic sample-data preview if backend is offline.

## Start

```bash
cd buckeyequeue-frontend
npm install
cp .env.example .env
npm run dev
```
Open http://localhost:5173. Run your FastAPI server at http://localhost:8000 in another terminal. Vite proxies `/locations` (including websocket upgrades) to FastAPI automatically.

For a hosted API, put `VITE_API_URL=https://api.example.com` in `.env` and enable CORS on the FastAPI server for your frontend origin. To force preview data, set `VITE_DEMO_MODE=true`.

## Backend integration notes

- `GET /locations`: expected to return an array or `{locations:[...]}`. Each location should include `id`, `name`, `kind` (`bus` or `food_court`), `capacity`.
- `GET /locations/{id}/occupancy`: typical payload `{count,capacity,percentage,level}`; alternate `current_count`/`percent_full` fields supported.
- `GET /locations/{id}/forecast?hours=12&weeks=4`: expected array or `{forecast:[...]}`, each with an hourly timestamp and percentage. Other common names are supported by the adapter in `src/api.js`.
- `WS /locations/{id}/live`: should push JSON payloads with current occupancy. If the payload shape differs, revise `src/api.js` and the `onUpdate` callback in `src/main.jsx`.
- `POST /swipes` and `POST /locations` are intentionally not called by the public student dashboard because they require privileged API keys. Never ship those keys in frontend code.

Your actual Pydantic response shapes were not provided. Update `src/api.js` field aliases if they differ. Failed forecast requests display sample forecast values; label these appropriately before production. Sample occupancy is **not real campus data**.

## Production notes

- Run `npm run build` to produce `dist/`.
- Ensure university and transit operator permissions before using real ID-card reader data.
- Do not assume card-reader swipe counts represent perfectly accurate headcounts. Present them as estimates, disclose stale data, and incorporate privacy review and retention limits.
- The current frontend intentionally has no account or admin interface.
