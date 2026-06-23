# Price Hunter

Personal shopping price-comparison scout for Dublin Northside (Santry / Swords / Malahide / Baldoyle / Portmarnock).

Compares a basket of products across Tesco, SuperValu, Dunnes, Aldi, Lidl, Londis, Boots (in-store) and Amazon.ie / Boots.ie / etc. (online). Member pricing applied where configured. Own-brand alternatives scored against brand products via Open Food Facts ingredients data. Receipt OCR via Telegram photo upload.

## Quick start

```bash
git clone git@github.com:BOB-12321/price-hunter.git
cd price-hunter
cp .env.example .env       # edit DATABASE_URL if needed
docker compose up -d --build
curl http://localhost:3016/healthz
```

## Architecture

- **FastAPI** service (`app/`)
- **Postgres 16** for products, stores, prices, receipts, hunts
- **Mobile-first web UI** at `/` (Tailwind via CDN, no build step)
- **Telegram bot** at `/api/telegram/webhook` for chat-driven control
- **Store adapters** in `app/stores/` — one per retailer, all implementing a common `StoreAdapter` interface
- **Open Food Facts** for ingredient data + brand/own-brand matching
- Tailscale-only deployment, port 3016

## Phases

1. Skeleton (this commit) — repo, Docker, FastAPI, healthcheck, mobile landing page
2. Basket CRUD — products, stores, memberships APIs + UI
3. Tesco IE adapter — real price pulls, Clubcard pricing
4. More store adapters (Dunnes, Lidl IE, Boots IE, SuperValu, Aldi, online)
5. Ingredients + alternatives — Open Food Facts client, similarity scoring
6. Receipts — Telegram photo OCR + basket matching
7. Watchlist + daily digest

## License

MIT
