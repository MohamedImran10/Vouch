# Vouch Backend

Real-time Trust Network API powered by Graph Theory (BFS, DFS, Hash Maps).

## Features

- **BFS Search**: Find service providers by social proximity (1st/2nd degree connections)
- **DFS Path Tracing**: Verify trust paths from user to provider
- **Hash Map Adjacency List**: O(1) edge additions and category lookups
- **Firebase Integration**: Cloud Firestore persistence with local mock data fallback
- **Zero-Config Local Development**: Works out-of-the-box without Firebase credentials

## Quick Start

### Local Development

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload

# Server starts at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Run Tests

```bash
pytest tests/ -v
```

## API Endpoints

### Health Check
```
GET /health
```

### Search Providers (BFS)
```
GET /api/search?user_id=alice&category=plumber&max_degree=2
```

### Trust Path (DFS)
```
GET /api/trust-path?from_id=alice&to_id=bob_plumber
```

### Full Graph Export
```
GET /api/graph/full
```

### Create Vouch
```
POST /api/vouch
{
  "from_user": "alice",
  "to_provider": "bob_plumber",
  "category": "plumber",
  "timestamp": "2024-01-15"
}
```

### Get Categories
```
GET /api/categories
```

## Firebase Setup (Optional)

1. Create a Firebase project at https://console.firebase.google.com
2. Download service account credentials JSON
3. Set environment variable:
   ```bash
   export FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
   ```

Without Firebase credentials, the app uses realistic mock data automatically.

## Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect repository in Render dashboard
3. Render auto-detects `render.yaml` configuration
4. Set `FIREBASE_CREDENTIALS_PATH` environment variable (optional)

### Deploy with Docker

```bash
docker build -t vouch-backend .
docker run -p 8000:8000 vouch-backend
```

## Architecture

```
┌─────────────────┐
│   Flutter App   │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Server │
│                 │
│  ┌───────────┐  │
│  │Graph      │  │
│  │Engine     │  │
│  │(BFS/DFS)  │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Firebase  │  │
│  │ Service   │  │
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Firestore DB  │
│   (Optional)    │
└─────────────────┘
```

## Tech Stack

- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation
- **firebase-admin**: Cloud Firestore SDK
- **pytest**: Testing framework

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI endpoints
│   ├── graph_engine.py      # BFS/DFS/Hash Map implementation
│   └── firebase_service.py  # Firestore integration + mock data
├── tests/
│   ├── __init__.py
│   ├── test_graph.py        # Graph engine tests
│   └── test_api.py          # API endpoint tests
├── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

## License

MIT
