"""
API endpoint tests for Vouch backend.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app, graph_engine


@pytest.fixture
def client():
    """Create a test client and initialize graph."""
    with TestClient(app) as test_client:
        # Manually trigger startup to populate graph
        from app.firebase_service import FirebaseService
        firebase_svc = FirebaseService()
        vouches = firebase_svc.load_vouches()

        for vouch in vouches:
            graph_engine.add_edge(
                from_user=vouch["from_user"],
                to_provider=vouch["to_provider"],
                category=vouch["category"],
                timestamp=vouch.get("timestamp", "")
            )

        yield test_client

        # Reset graph after tests
        graph_engine.adjacency.clear()
        graph_engine.providers.clear()
        graph_engine.category_map.clear()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "graph_nodes" in data
    assert "graph_edges" in data


def test_search_providers_plumber(client):
    """Test BFS search for plumbers."""
    response = client.get("/api/search?user_id=alice&category=plumber")
    assert response.status_code == 200
    results = response.json()

    # Should find at least bob_plumber (1st degree)
    assert len(results) >= 1

    # Verify structure
    first_result = results[0]
    assert "provider_id" in first_result
    assert "degree" in first_result
    assert "path" in first_result
    assert "category" in first_result
    assert first_result["category"] == "plumber"


def test_search_providers_mechanic(client):
    """Test BFS search for mechanics."""
    response = client.get("/api/search?user_id=alice&category=mechanic")
    assert response.status_code == 200
    results = response.json()

    # Should find mechanics in Alice's network
    assert len(results) >= 1

    # Check that results are sorted by degree
    degrees = [r["degree"] for r in results]
    assert degrees == sorted(degrees)


def test_search_missing_params(client):
    """Test search with missing parameters."""
    response = client.get("/api/search?user_id=alice")
    assert response.status_code == 422  # Validation error

    response = client.get("/api/search?category=plumber")
    assert response.status_code == 422


def test_trust_path_valid(client):
    """Test DFS trust path for valid connection."""
    response = client.get("/api/trust-path?from_id=alice&to_id=bob_plumber")
    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert data["cycle_detected"] is False
    assert "alice" in data["path"]
    assert "bob_plumber" in data["path"]


def test_trust_path_second_degree(client):
    """Test DFS trust path for 2nd degree connection."""
    response = client.get("/api/trust-path?from_id=alice&to_id=dave_mechanic")
    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is True
    assert len(data["path"]) == 3  # alice -> carol -> dave_mechanic


def test_trust_path_invalid(client):
    """Test DFS trust path for non-existent connection."""
    response = client.get("/api/trust-path?from_id=alice&to_id=nonexistent")
    assert response.status_code == 200
    data = response.json()

    assert data["valid"] is False
    assert len(data["path"]) == 0


def test_get_full_graph(client):
    """Test full graph export."""
    response = client.get("/api/graph/full")
    assert response.status_code == 200
    data = response.json()

    assert "nodes" in data
    assert "node_count" in data
    assert "edge_count" in data
    assert data["node_count"] > 0
    assert data["edge_count"] > 0


def test_create_vouch(client):
    """Test vouch creation endpoint."""
    vouch_data = {
        "from_user": "test_user",
        "to_provider": "test_provider",
        "category": "plumber",
        "timestamp": "2024-01-15"
    }

    response = client.post("/api/vouch", json=vouch_data)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "vouch_id" in data


def test_get_categories(client):
    """Test categories endpoint."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()

    assert "categories" in data
    assert len(data["categories"]) > 0

    # Verify structure
    first_category = data["categories"][0]
    assert "id" in first_category
    assert "name" in first_category
    assert "icon" in first_category
