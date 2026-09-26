# Vouch - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Start the Backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend will start at: **http://localhost:8000**

### Step 2: Verify Backend

Open another terminal:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","graph_nodes":11,"graph_edges":10}
```

### Step 3: Run Tests (Optional)

```bash
pytest tests/ -v
# Should see: 24 passed ✅
```

### Step 4: Start Flutter App

```bash
cd ../frontend
flutter pub get
flutter run -d chrome  # For web
# OR
flutter run           # For Android/iOS
```

## 📱 Demo Flow

1. **Home Screen** → Click "Plumbers" 🔧
2. **Search Results** → See providers with green "1st Degree" badges
3. **Click "View Path"** → See trust chain: You → Friend → Provider
4. **Toggle Graph View** → See interactive network visualization

## 🧪 Test the API

```bash
# Search for plumbers
curl "http://localhost:8000/api/search?user_id=alice&category=plumber"

# Get trust path
curl "http://localhost:8000/api/trust-path?from_id=alice&to_id=bob_plumber"

# Get full graph
curl "http://localhost:8000/api/graph/full"
```

## 🎓 For Academic Demo

1. Show `PROJECT_SUMMARY.txt` - explains all algorithms
2. Run `pytest -v` - show 24 passing tests
3. Start backend + frontend - live demo
4. Show code: `backend/app/graph_engine.py` (BFS/DFS)
5. Q&A

## 🐛 Troubleshooting

**Backend won't start?**
- Check Python version: `python3.12 --version`
- Activate venv: `source venv/bin/activate`

**Flutter errors?**
- Run: `flutter doctor`
- Clear: `flutter clean && flutter pub get`

**Port already in use?**
- Change port: `uvicorn app.main:app --port 8001`
- Update `frontend/lib/services/api_service.dart` baseUrl

## 📚 Documentation

- Full details: `README.md`
- Backend: `backend/README.md`
- Frontend: `frontend/README.md`
- Project summary: `PROJECT_SUMMARY.txt`

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Health check returns OK
- [ ] 24 tests passing
- [ ] Flutter app launches
- [ ] Can search for providers
- [ ] Trust path modal works
- [ ] Graph view displays

**All working? You're ready to demo! 🎉**
