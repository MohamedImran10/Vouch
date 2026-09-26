# Vouch - Trust Network Application

A real-time Trust Network mobile and web application for an academic mini-project. Vouch replaces anonymous reviews with social proximity rankings using Graph Theory algorithms (BFS, DFS, Hash Maps) over a social network.

## 🎯 Project Overview

**Problem**: Traditional review platforms rely on anonymous ratings which can be manipulated or unreliable.

**Solution**: Vouch uses your social network to find service providers (plumbers, mechanics, babysitters) who have been hired and trusted by your 1st and 2nd-degree connections.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Flutter Frontend                       │
│  (Mobile: Android/iOS, Web: Chrome/Safari)              │
│                                                          │
│  - Home Screen (Category Browser)                       │
│  - Search Results (BFS Rankings)                        │
│  - Network Graph (Interactive 2D Visualization)         │
│  - Trust Path Modal (DFS Verification)                  │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/REST API
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Python FastAPI Backend                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Graph Engine (In-Memory)                │  │
│  │                                                  │  │
│  │  • Hash Map Adjacency List (O(1) lookups)       │  │
│  │  • BFS Search (Social Proximity Ranking)        │  │
│  │  • DFS Path Tracing (Trust Verification)        │  │
│  │  • Cycle Detection                              │  │
│  └──────────────────────────────────────────────────┘  │
│                          │                              │
│  ┌──────────────────────▼──────────────────────────┐  │
│  │         Firebase Service (Optional)             │  │
│  │                                                  │  │
│  │  • Mock Data Fallback (Local Development)       │  │
│  │  • Cloud Firestore Sync (Production)            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│            Cloud Firestore (Optional)                    │
│                                                          │
│  Collections: Users, Providers, Vouches, Chats          │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Features Implemented

### Phase 1: Backend Graph Infrastructure ✅
- **GraphEngine** with Hash Map adjacency list
- **BFS Algorithm** for social proximity search
- **DFS Algorithm** with cycle detection
- **14/14 unit tests passing**

### Phase 2: FastAPI Endpoints ✅
- `/health` - Health check & monitoring
- `/api/search` - BFS-powered provider search
- `/api/trust-path` - DFS path verification
- `/api/graph/full` - Full graph export
- `/api/vouch` - Create new vouches
- `/api/categories` - Service categories
- **10/10 API tests passing**
- **Mock data fallback** for Firebase-free development
- **Deployment configs** (Render, Docker)

### Phase 3: Flutter Core Screens ✅
- **HomeScreen**: Category browser with view mode toggle
- **SearchResultsScreen**: BFS results with degree badges
- **NetworkGraphScreen**: Interactive graph visualization
- **TrustPathModal**: DFS path timeline
- **Models & Services**: Complete data layer
- **Material Design 3**: Modern, accessible UI

## 📊 Graph Theory Algorithms

### 1. Hash Map Adjacency List
```python
adjacency[user_id][provider_id] = {category, timestamp}
```
- **Time Complexity**: O(1) for edge addition/lookup
- **Space Complexity**: O(V + E) where V=vertices, E=edges

### 2. Breadth-First Search (BFS)
- Finds providers ranked by degrees of separation
- Returns shortest paths from user to providers
- Filters by category
- **Time Complexity**: O(V + E)

### 3. Depth-First Search (DFS)
- Traces exact trust path between user and provider
- Includes cycle detection
- Verifies connection validity
- **Time Complexity**: O(V + E)

## 📁 Project Structure

```
Vouch/
├── backend/                    # Python FastAPI Server
│   ├── app/
│   │   ├── main.py            # FastAPI routes
│   │   ├── graph_engine.py    # BFS/DFS/HashMap implementation
│   │   └── firebase_service.py # Firestore integration
│   ├── tests/
│   │   ├── test_graph.py      # Graph algorithm tests
│   │   └── test_api.py        # API endpoint tests
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml
│   └── README.md
│
├── frontend/                   # Flutter Mobile/Web App
│   ├── lib/
│   │   ├── main.dart          # App entry
│   │   ├── models/
│   │   │   └── models.dart    # Data models
│   │   ├── services/
│   │   │   └── api_service.dart # HTTP client
│   │   └── screens/
│   │       ├── home_screen.dart
│   │       ├── search_results_screen.dart
│   │       ├── network_graph_screen.dart
│   │       └── trust_path_modal.dart
│   ├── pubspec.yaml
│   └── README.md
│
└── README.md                   # This file
```

## 🛠️ Tech Stack

### Backend
- **Python 3.12**
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation
- **firebase-admin** - Cloud Firestore SDK
- **pytest** - Testing framework

### Frontend
- **Flutter 3.47.4** - Cross-platform framework
- **Dart 3.13** - Programming language
- **Provider** - State management
- **graphview** - Network graph visualization
- **http** - API client
- **Material Design 3** - UI components

### Database (Optional)
- **Cloud Firestore** - NoSQL cloud database

## ⚡ Quick Start

### 1. Start Backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start server
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000` with interactive docs at `/docs`

### 2. Start Frontend

```bash
cd frontend
flutter pub get

# Run on web
flutter run -d chrome

# Run on Android
flutter run

# Build release APK
flutter build apk --release
```

## 📱 Screenshots & Demo Flow

### 1. Home Screen
- Browse 5 service categories (Plumbers, Mechanics, Babysitters, Electricians, Cleaners)
- Toggle between List View and Graph View
- Educational cards explaining 1st/2nd degree connections

### 2. Search Results
- Provider cards with star ratings
- Prominent badges: "1st Degree" (green) or "2nd Degree" (orange)
- Trust path preview showing connection chain
- "View Path" and "Get Intro" action buttons

### 3. Network Graph
- Interactive 2D visualization with pinch-zoom and pan
- Color-coded nodes:
  - **Blue** = You (current user)
  - **Orange** = Friends (social connections)
  - **Green** = Providers (service providers)
- Legend overlay with instructions

### 4. Trust Path Modal
- Vertical timeline visualization
- Shows each person in the chain with role labels
- "vouched for" connectors between nodes
- Degree of separation counter

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

- **14 graph algorithm tests** (BFS, DFS, Hash Map operations)
- **10 API endpoint tests** (health, search, path, vouch)
- **All 24 tests passing** ✅

### Frontend
```bash
cd frontend
flutter test
flutter analyze
```

## 🚀 Deployment

### Backend → Render (Free Tier)

1. Push to GitHub
2. Connect repo in [Render Dashboard](https://render.com)
3. Auto-deploys using `render.yaml`
4. Optional: Add `FIREBASE_CREDENTIALS_PATH` env var

### Frontend → Web

```bash
flutter build web
```

Deploy `build/web/` to:
- **Firebase Hosting**: `firebase deploy`
- **Netlify**: Drag & drop folder
- **Vercel**: Connect GitHub repo

### Frontend → Android

```bash
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

## 🎓 Academic Requirements Met

✅ **Graph Theory Algorithms**:
- BFS for shortest-path social search
- DFS with cycle detection
- Hash Map adjacency list

✅ **Data Structures**:
- Adjacency List (Hash Map)
- Queue (BFS)
- Stack (DFS recursion)
- Hash Tables for O(1) category lookups

✅ **Real-World Application**:
- Trust network visualization
- Social proximity ranking
- Service provider recommendations

✅ **Interactive Demo**:
- Live graph visualization
- Click-through UI flow
- Working search & path tracing

## 📈 Performance Characteristics

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Add Edge | O(1) | O(1) |
| BFS Search | O(V + E) | O(V) |
| DFS Path | O(V + E) | O(V) |
| Category Lookup | O(1) | O(C×P) |

Where:
- V = number of vertices (users + providers)
- E = number of edges (vouches)
- C = number of categories
- P = providers per category

## 🔮 Future Enhancements (Phase 4 & 5)

### Phase 4: Warm Intro Chat (Planned)
- Firestore StreamBuilder for real-time chat
- Sticky trust path banner in chat UI
- Pre-filled intro message templates

### Phase 5: Advanced Features (Planned)
- Weighted edges (star ratings)
- Dijkstra's algorithm for reputation scoring
- A* pathfinding for optimal introductions
- Community detection (Louvain algorithm)
- PageRank for provider influence

## 📄 License

MIT License - This is an academic project for educational purposes.

## 👥 Contributors

Mohamed Imran M - Academic Mini-Project (2026)

## 🙏 Acknowledgments

- Graph Theory concepts from algorithm design courses
- Flutter community for excellent packages
- FastAPI for modern Python web development

---

**Status**: Phases 1-3 Complete (Backend + Core Frontend) ✅  
**Next Steps**: Firebase integration, Chat feature, Advanced algorithms
