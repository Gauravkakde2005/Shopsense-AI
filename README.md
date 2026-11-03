# ShopSense AI

ShopSense AI is a source-attributed shopping assistant that parses buyer requests, retrieves current product listings through an authorized shopping-search provider, computes transparent ranking scores, and compares offers without inventing prices, reviews, or links.

## Stack

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + Pydantic
- Workflow: LangGraph intent, discovery, review-metadata, ranking, verification, and explanation stages
- Data: live provider results only in production; offline fixtures are used only by tests

## Project structure

- `frontend/` – React UI and API integration
- `backend/` – FastAPI application, live provider adapter, LLM adapter, and ranking logic
- `backend/.env.example` – environment template

## Run locally

### 1) Backend

```powershell
cd shopsense-ai\backend
Copy-Item .env.example .env
# Add a SerpApi key to .env before searching.
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2) Frontend

```powershell
cd shopsense-ai\frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173` in the browser.

## API

- `POST /api/search` – natural-language product search
- `GET /api/products/{product_id}` – normalized product details
- `POST /api/compare` – side-by-side comparison
- `POST /api/recommendations/rerank` – rescore products using weights
- `GET /api/providers` – configured product sources
- `GET /api/health` – backend health check
- `GET /api/search-history` – saved history for the current session
- `POST /api/saved-products` – save product
- `DELETE /api/saved-products/{product_id}` – remove product

## Live data and AI configuration

The default provider is SerpApi's Google Shopping API. It returns product titles, prices, merchants, links, ratings, review counts, and thumbnails when the source provides them. Results are marked `live_web` and include retrieval timestamps and source links.

Set `SERPAPI_KEY` in `backend/.env`. Without it, search returns a clear configuration error and does not fall back to the old demo catalog.

`GROQ_API_KEY` powers the Product Assistant through Groq's OpenAI-compatible chat-completions API. The prompt restricts answers to retrieved product facts. Set `GROQ_MODEL` to an available Groq model such as `openai/gpt-oss-120b`.

Voice input uses the browser Web Speech API and read-aloud uses `speechSynthesis`; Chrome and Edge provide the best support.

Retailer review text is not scraped. The provider's returned rating and review-count metadata are shown only when supplied. Full review text requires an authorized retailer or review API and can be added as another provider adapter without weakening source attribution.

## Tests

```powershell
cd shopsense-ai\backend
..\.venv\Scripts\python.exe -m pytest -q
```

```powershell
cd shopsense-ai\frontend
npm run build
```

## Notes

The application intentionally fails closed when live retrieval is unavailable. This keeps recommendations auditable and prevents fabricated prices, reviews, or shopping links.
