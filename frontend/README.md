# Vouch - Trust Network Mobile App

A real-time Trust Network mobile and web application built with Flutter that uses Graph Theory (BFS, DFS) to help users find trusted service providers through their social connections.

## Features

- **BFS Social Search**: Find providers ranked by degrees of separation (1st/2nd degree connections)
- **DFS Trust Path Visualization**: See the exact chain of trust from you to any provider
- **Interactive Network Graph**: 2D visualization of your trust network with zoom/pan
- **Category-Based Search**: Browse plumbers, mechanics, babysitters, electricians, and more
- **Dual View Modes**: Switch between list view and graph visualization
- **Clean Material Design 3 UI**: Modern, accessible interface with light/dark theme support

## Tech Stack

- **Flutter 3.47+** (Dart 3.13+)
- **State Management**: Provider
- **Graph Visualization**: graphview package
- **Backend**: FastAPI Python server with Graph Engine
- **Database**: Cloud Firestore (optional)

## Quick Start

### Prerequisites

- Flutter SDK 3.x or higher
- Python 3.12+ (for backend)
- Android Studio / Xcode (for mobile)

### Run the Backend

```bash
cd ../backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Run the Flutter App

```bash
# Get dependencies
flutter pub get

# Run on Chrome (Web)
flutter run -d chrome

# Run on Android
flutter run -d android

# Run on iOS
flutter run -d ios
```

### Configure Backend URL

For production, update the API base URL in `lib/services/api_service.dart`:

```dart
static const String baseUrl = 'https://your-backend-url.com';
```

## Project Structure

```
lib/
├── main.dart                          # App entry point
├── models/
│   └── models.dart                    # Data models
├── services/
│   └── api_service.dart              # Backend API client
└── screens/
    ├── home_screen.dart              # Category browser
    ├── search_results_screen.dart    # BFS search results
    ├── network_graph_screen.dart     # Interactive graph view
    └── trust_path_modal.dart         # DFS path visualization
```

## Build for Production

### Android APK

```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### iOS

```bash
flutter build ios --release
```

### Web

```bash
flutter build web
# Output: build/web/
# Deploy to Firebase Hosting, Netlify, or any static host
```

## Features in Detail

### Home Screen
- Browse service categories with emoji icons
- Toggle between List View and Graph View modes
- Educational info cards explaining trust degrees

### Search Results
- Provider cards with star ratings
- Prominent 1st/2nd degree badges
- Trust path previews
- "Get Intro" warm introduction messaging
- "View Path" button for full DFS visualization

### Network Graph
- Interactive 2D node-and-edge visualization
- Color-coded nodes (You=Blue, Friends=Orange, Providers=Green)
- Pinch-to-zoom and pan gestures
- Legend and info overlay

### Trust Path Modal
- Vertical timeline showing exact trust chain
- Visual connectors with "vouched for" labels
- Profile info for each connection
- Degree of separation counter

## Architecture

```
Flutter App
    │
    ├─ ApiService (HTTP Client)
    │       │
    │       ▼
    │  FastAPI Backend
    │       │
    │       ├─ GraphEngine (BFS/DFS/HashMap)
    │       └─ FirebaseService (Optional)
    │              │
    │              ▼
    │         Cloud Firestore
    │
    └─ Provider (State Management)
```

## Testing

```bash
# Run unit tests
flutter test

# Run integration tests
flutter test integration_test/
```

## Known Limitations

- Firebase integration is optional (mock data works out-of-the-box)
- Chat feature requires Firebase Firestore setup
- Graph visualization performance degrades with >100 nodes

## Deployment

See `../backend/README.md` for backend deployment instructions.

For Flutter web, deploy `build/web/` to:
- Firebase Hosting: `firebase deploy`
- Netlify: Drag & drop `build/web` folder
- Vercel: Connect GitHub repo

## License

MIT

## Academic Project

This is a mini-project demonstrating Graph Theory algorithms (BFS, DFS, Hash Maps) in a real-world social trust network application.
