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


def test_register_user_returns_timestamps(client):
    """Registration should include created_at and updated_at in the nested user payload."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new_user@example.com",
            "name": "New User",
            "password": "StrongPass1!",
            "phone": "1234567890"
        }
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "new_user@example.com"
    assert "created_at" in data["user"]
    assert "updated_at" in data["user"]
    assert data["user"]["created_at"]
    assert data["user"]["updated_at"]


def test_login_accepts_any_email_and_password(client):
    """Local development mode should allow any email/password combination to sign in."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "any-email@example.com",
            "password": "anything"
        }
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "any-email@example.com"


def test_connection_crud_by_category(client):
    """Connections can be created, listed, updated, and deleted by category."""
    payload = {
        "name": "Metro Electric",
        "category": "electrician",
        "email": "metro@example.com",
        "phone": "555-0101",
        "description": "24/7 electrical repair"
    }

    created = client.post("/api/connections", json=payload)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["name"] == payload["name"]
    assert data["category"] == payload["category"]
    connection_id = data["id"]

    listed = client.get("/api/connections?category=electrician")
    assert listed.status_code == 200, listed.text
    items = listed.json()
    assert any(item["id"] == connection_id for item in items)

    updated = client.put(
        f"/api/connections/{connection_id}",
        json={"name": "Metro Electric Plus", "description": "Updated details"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Metro Electric Plus"

    deleted = client.delete(f"/api/connections/{connection_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["success"] is True


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


def test_trust_path_reports_disconnected_component(client):
    graph_engine.add_edge("isolated_person", "isolated_provider", "plumber")

    response = client.get("/api/trust-path?from_id=alice&to_id=isolated_provider")

    assert response.status_code == 200
    assert response.json()["reachable"] is False
    assert response.json()["reason"] == "DISCONNECTED_COMPONENT"
    assert response.json()["path"] == []


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


def test_full_graph_uses_signed_in_user_as_mock_root(client):
    """The seeded Alice network should be rooted at the signed-in demo account."""
    login = client.post(
        "/api/auth/login",
        json={"email": "imran@example.com", "password": "anything"},
    )
    token = login.json()["access_token"]
    graph_engine.add_edge("imran", "new_provider", "babysitter")

    response = client.get(
        "/api/graph/full",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    node_ids = {node["id"] for node in data["nodes"]}

    assert "imran" in node_ids
    assert "alice" not in node_ids
    assert any(edge["source"] == "imran" and edge["target"] == "carol" for edge in data["edges"])
    assert any(edge["source"] == "imran" and edge["target"] == "new_provider" for edge in data["edges"])


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


def test_vouch_persistence_crud_and_filters():
    """Mock persistence supports the complete vouch CRUD lifecycle."""
    from app.firebase_service import FirebaseService

    service = FirebaseService()
    service.use_mock = True
    service.mock_vouches = []

    vouch_id = service.save_vouch({
        "from_user_id": "test_user",
        "to_provider_id": "test_provider",
        "category": "plumber",
        "message": "Reliable work",
        "rating": 5,
    })

    created = service.load_vouch_by_id(vouch_id)
    assert created is not None
    assert created["to_provider_id"] == "test_provider"
    assert service.load_vouches(category="plumber", user_id="test_user") == [created]
    assert service.load_vouches(category="electrician") == []

    assert service.update_vouch(vouch_id, {"message": "Updated note", "rating": 4})
    updated = service.load_vouch_by_id(vouch_id)
    assert updated is not None
    assert updated["message"] == "Updated note"
    assert updated["rating"] == 4

    assert service.delete_vouch(vouch_id)
    assert service.load_vouch_by_id(vouch_id) is None
    assert not service.delete_vouch(vouch_id)


def test_vouch_routes_support_provider_rating_note_and_graph_crud(client):
    login = client.post(
        "/api/auth/login",
        json={"email": "react-crud@example.com", "password": "demo"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    plumber = client.post(
        "/api/providers",
        headers=headers,
        json={"name": "Route Test Plumbing", "category": "plumber"},
    )
    mechanic = client.post(
        "/api/providers",
        headers=headers,
        json={"name": "Route Test Garage", "category": "mechanic"},
    )
    assert plumber.status_code == 201, plumber.text
    assert mechanic.status_code == 201, mechanic.text

    created = client.post(
        "/api/vouches",
        headers=headers,
        json={
            "to_provider_id": plumber.json()["id"],
            "category": "plumber",
            "rating": 5,
            "message": "Clear estimate and careful work.",
        },
    )
    assert created.status_code == 201, created.text
    vouch_id = created.json()["id"]
    assert created.json()["rating"] == 5
    nanny_path = graph_engine.dfs_trust_path("react-crud", "nanny_babysitters")
    assert nanny_path.valid is True

    plumber_list = client.get("/api/vouches?user_id=react-crud&category=plumber")
    assert plumber_list.status_code == 200, plumber_list.text
    assert [item["id"] for item in plumber_list.json()] == [vouch_id]
    assert plumber_list.json()[0]["message"] == "Clear estimate and careful work."

    updated = client.put(
        f"/api/vouches/{vouch_id}",
        headers=headers,
        json={
            "to_provider_id": mechanic.json()["id"],
            "category": "mechanic",
            "rating": 4,
            "message": "Updated recommendation.",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["to_provider_id"] == mechanic.json()["id"]
    assert updated.json()["rating"] == 4

    graph_edges = client.get("/api/graph/full").json()["edges"]
    assert not any(edge["target"] == plumber.json()["id"] for edge in graph_edges)
    assert any(
        edge["source"] == "react-crud" and edge["target"] == mechanic.json()["id"]
        for edge in graph_edges
    )

    deleted = client.delete(f"/api/vouches/{vouch_id}", headers=headers)
    assert deleted.status_code == 200, deleted.text
    mechanic_list = client.get("/api/vouches?user_id=react-crud&category=mechanic")
    assert mechanic_list.status_code == 200, mechanic_list.text
    assert mechanic_list.json() == []

    for provider in (plumber.json(), mechanic.json()):
        response = client.delete(f"/api/providers/{provider['id']}", headers=headers)
        assert response.status_code == 200, response.text


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
