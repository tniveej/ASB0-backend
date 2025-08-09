## AI4MY: Healthcare Reimagined - Proactive Public Health Shield Backend API

This repository contains a foundational Python backend API for a system that acts as a "Proactive Public Health Shield". It ingests health-related information from news outlets (via RSS scraping) and mocked social media submissions, stores them in Supabase (PostgreSQL), and exposes endpoints for retrieval, filtering, and verification workflows.

The API is designed with FastAPI for the main HTTP interface and includes an optional Flask-based worker that can run scheduled scraping tasks. The solution targets the workflow needs of public health analysts (e.g., "Siti, The Analyst") who need rapid, automated, and trustworthy insights to spot emerging threats and counter misinformation early.

### Features
- FastAPI backend with organized routes and Pydantic schemas
- Supabase (PostgreSQL) integration for data persistence
- Health mentions ingestion from Malaysian news outlets via RSS (e.g., The Star, Malay Mail)
- Mock social media ingestion endpoint
- Keyword management endpoints (add/list)
- Retrieval of mentions with filtering and pagination
- Status update endpoint for verification workflow
- Optional Flask worker for scheduled scraping (using APScheduler)
- Environment-based configuration and structured logging

---

## Project Structure

```
ASB0-backend/
  app/
    __init__.py
    main.py                   # FastAPI app entrypoint
    config.py                 # Env config and settings
    logging_config.py         # Logging setup
    scheduler.py              # Optional APScheduler integrated with FastAPI
    db/
      __init__.py
      supabase_client.py      # Supabase client init and helpers
      repositories.py         # Data access methods
    models/
      __init__.py
      schemas.py              # Pydantic models
    routes/
      __init__.py
      keywords.py
      mentions.py
      # ingestion.py (removed)
      scraping.py
    scrapers/
      __init__.py
      rss_scraper.py          # RSS-based scrapers for selected news outlets
  database/
    schema.sql                # SQL DDL for required tables
  pyproject.toml
  README.md
```

---

## Prerequisites

- Python 3.10+
- Supabase project with access keys

Set the following environment variables (e.g., in your shell or a `.env` file you load manually):

```
SUPABASE_URL=<your-supabase-url>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
```

Notes:
- Service role key is recommended for server-side upserts and to bypass RLS when appropriate. If you use RLS, ensure policies allow the intended operations.

---

## Install Dependencies (with uv)

1) Install uv (see docs at `https://docs.astral.sh/uv/`):

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2) Resolve and sync dependencies from `pyproject.toml`:

```
uv lock
uv sync
```

3) Run the app (uv ensures the right environment):

```
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

<!-- Using uv; no requirements.txt needed. -->

---

## Database Schema

Apply `database/schema.sql` in your Supabase SQL editor or psql connection:

```
-- Enables gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS health_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    data_source TEXT NOT NULL,
    headline TEXT,
    summary TEXT,
    image_url TEXT,
    link TEXT UNIQUE NOT NULL,
    media_type TEXT,
    media_outlet TEXT,
    media_name TEXT,
    status TEXT DEFAULT 'unverified',
    keywords TEXT[],
    engagement INT
);

CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## Run the FastAPI App

```
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

FastAPI docs available at: `http://localhost:8000/docs`

---

## Optional: Enable Scheduled Scraping

The API includes a background scheduler (APScheduler) that can run the scraping job automatically every 30 minutes. To enable it, set an environment variable before starting the app:

```
export ENABLE_SCHEDULER=true
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Without `ENABLE_SCHEDULER=true`, the scheduler is disabled by default.

---

## API Endpoints

Base URL: `http://localhost:8000`

### Keyword Management

- POST `/keywords`
  - Body: `{ "keyword": "demam denggi" }`
  - Response: saved keyword

- GET `/keywords`
  - Response: list of keywords

### News Scraping & Ingestion

- POST `/scrape-news`
  - Triggers background RSS scraping for configured outlets using active keywords.
  - Response: `{ "message": "scrape started" }`

### Social Media Data Ingestion

Removed for now to focus on RSS and Exa-based ingestion. 

### Health Mentions Retrieval

- GET `/health-mentions`
  - Query params: `start_date`, `end_date`, `data_source`, `status`, `keywords` (comma-separated), `page` (default 1), `page_size` (default 20)
  - Response: `{ items: [...], page: 1, page_size: 20, total: 123 }`

### Mention Status Update

- PUT `/health-mentions/{id}/status`
  - Body: `{ "status": "verified" }`
  - Response: updated mention

---

## Curl Examples

Add a keyword:
```
curl -X POST http://localhost:8000/keywords -H 'Content-Type: application/json' -d '{"keyword":"demam denggi"}'
```

List keywords:
```
curl http://localhost:8000/keywords
```

Trigger scraping:
```
curl -X POST http://localhost:8000/scrape-news
```

Ingest social media (mock):
```
curl -X POST http://localhost:8000/ingest-social-media -H 'Content-Type: application/json' -d '{
  "date":"2025-08-01",
  "headline":"Dengue outbreak concern in PJ",
  "summary":"Multiple reports of dengue cases in several neighborhoods.",
  "image_url":null,
  "link":"https://social.example/post/123",
  "keywords":["dengue","Petaling Jaya"],
  "engagement":120,
  "media_name":"X (Twitter)"
}'
```

Fetch mentions:
```
curl 'http://localhost:8000/health-mentions?page=1&page_size=10&status=unverified'
```

Update status:
```
curl -X PUT http://localhost:8000/health-mentions/<id>/status -H 'Content-Type: application/json' -d '{"status":"verified"}'
```

---

## Notes on Scraping

This implementation uses RSS feeds from Malaysian outlets (e.g., The Star, Malay Mail) to reliably parse and filter articles by keywords. It extracts metadata (title, summary, link, published date) and stores them with `data_source='News Outlet'`, `media_type='news article'`, and appropriate `media_outlet`/`media_name` values. Link uniqueness prevents duplicate entries.

For production use, consider:
- Expanding outlets and feeds
- Better NLP keyword matching, entity/location extraction
- Rate limiting and retries
- Persistent job scheduler / queue

---

## License

MIT

