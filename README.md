# BMPL Stats API

FastAPI-based microservice for player statistics, shared between production and QA environments.

## Architecture

**Three-tier stats fetching:**
1. **Redis Cache** (1-10ms) - Check cache first
2. **PostgreSQL** (10-50ms) - Fallback to database
3. **MLB Stats API** (2-3 seconds) - Background fetch if not in DB

**Tech Stack:**
- **FastAPI** - Modern Python API framework
- **SQLAlchemy** - Database ORM
- **Alembic** - Database migrations
- **Celery** - Background job processing
- **Redis** - Caching and job queue
- **PostgreSQL** - Stats database
- **pybaseball** - MLB stats fetching

## API Endpoints

### Stats Retrieval

```bash
# Get stats for a single player
GET /api/v1/stats/{bbrefid}/{year}

# Example
curl http://localhost:3001/api/v1/stats/judgeaa01/2025

# Response
{
  "PA": "679",
  "HR": "53",
  "BA": ".291",
  ...
}
```

```bash
# Batch fetch stats
POST /api/v1/stats/batch

# Body
{
  "requests": [
    {"bbrefid": "judgeaa01", "year": 2025},
    {"bbrefid": "ohtansh01", "year": 2025}
  ]
}
```

### Admin Endpoints

```bash
# Trigger stats import
POST /api/v1/admin/import?year=2025

# Warm cache from database
POST /api/v1/admin/warmup?year=2025

# Clear cache
DELETE /api/v1/admin/cache
```

### Health Check

```bash
GET /api/v1/health

# Response
{"status": "healthy", "service": "bmpl-stats-api"}
```

## Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7

### Setup

```bash
# Clone repository
cd ~/dev/players-stats

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Run migrations
alembic upgrade head

# Access API
open http://localhost:3001/docs
```

### Running Locally

```bash
# Start all services (API + worker + db + redis)
docker-compose up

# API available at: http://localhost:3001
# Interactive docs: http://localhost:3001/docs
# ReDoc: http://localhost:3001/redoc
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Background Workers

```bash
# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Or use docker-compose
docker-compose up stats-worker
```

## Deployment

### Build Docker Image

```bash
docker build -t ghcr.io/jamiepinkham/players-stats:latest .
```

### Deploy to Production

Stack file: `bmpl-stats.yml` in players-deployment repo

```yaml
services:
  stats-api:
    image: ghcr.io/jamiepinkham/players-stats:main
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
```

## Integration

### From Rails/Players App

```ruby
# app/services/stats_client.rb
class StatsClient
  include HTTParty
  base_uri ENV.fetch('STATS_API_URL', 'http://stats-api:3001')

  def self.fetch(bbrefid, year)
    response = get("/api/v1/stats/#{bbrefid}/#{year}")
    response.success? ? response.parsed_response : {}
  end
end

# In GraphQL resolver
def stats(year:)
  StatsClient.fetch(object.bbrefid, year)
end
```

### Environment Variables

```bash
# Players app .env
STATS_API_URL=http://stats-api:3001
```

## Database Schema

### player_stats Table

```sql
CREATE TABLE player_stats (
    id SERIAL PRIMARY KEY,
    bbrefid VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    stats JSONB NOT NULL DEFAULT '{}',
    UNIQUE (bbrefid, year)
);

CREATE INDEX idx_player_stats_bbrefid_year ON player_stats(bbrefid, year);
```

**No foreign keys!** This allows the stats database to be shared between prod and QA environments.

## Testing

```bash
# Run tests (when added)
pytest

# Test API endpoints
curl http://localhost:3001/api/v1/health
```

## Monitoring

```bash
# View API logs
docker-compose logs -f stats-api

# View worker logs
docker-compose logs -f stats-worker

# Check Celery tasks
celery -A app.tasks.celery_app inspect active
```

## Project Structure

```
players-stats/
├── app/
│   ├── api/
│   │   └── routes.py           # API endpoints
│   ├── models/
│   │   └── player_stat.py      # SQLAlchemy model
│   ├── services/
│   │   └── stats_fetcher.py    # MLB API integration
│   ├── tasks/
│   │   ├── celery_app.py       # Celery config
│   │   └── tasks.py            # Background jobs
│   ├── cache.py                # Redis utilities
│   ├── config.py               # Settings
│   ├── database.py             # DB connection
│   └── main.py                 # FastAPI app
├── alembic/                    # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## License

Private - Billy Martin Players League
