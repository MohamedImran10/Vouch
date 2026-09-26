"""
Test suite for GraphEngine
Verifies BFS distance calculation and DFS path tracing.
"""
import pytest
from app.graph_engine import GraphEngine, SearchResult, TrustPath


@pytest.fixture
def sample_graph():
    """Create a sample social graph for testing."""
    engine = GraphEngine()

    # User Alice vouches for plumber Bob (1st degree)
    engine.add_edge("alice", "bob_plumber", "plumber", "2024-01-01")

    # User Alice is friends with Carol (connects to Carol's network)
    engine.add_edge("alice", "carol", "friend", "2024-01-02")

    # Carol vouches for mechanic Dave (2nd degree from Alice)
    engine.add_edge("carol", "dave_mechanic", "mechanic", "2024-01-03")

    # Carol vouches for plumber Eve (2nd degree from Alice)
    engine.add_edge("carol", "eve_plumber", "plumber", "2024-01-04")

    # Bob vouches for mechanic Frank (not reachable in 2 degrees from Alice)
    engine.add_edge("bob_plumber", "frank_mechanic", "mechanic", "2024-01-05")

    return engine


def test_graph_initialization():
    """Test that graph initializes with correct data structures."""
    engine = GraphEngine()
    assert len(engine.adjacency) == 0
    assert len(engine.providers) == 0
    assert len(engine.category_map) == 0


def test_add_edge():
    """Test adding edges to the graph."""
    engine = GraphEngine()
    engine.add_edge("user1", "provider1", "plumber", "2024-01-01")

    assert "user1" in engine.adjacency
    assert "provider1" in engine.adjacency["user1"]
    assert engine.adjacency["user1"]["provider1"]["category"] == "plumber"
    assert "user1" in engine.providers["provider1"]


def test_bfs_first_degree_search(sample_graph):
    """Test BFS finds 1st degree connections correctly."""
    results = sample_graph.bfs_search("alice", "plumber", max_degree=1)

    # Should find bob_plumber (1st degree)
    assert len(results) >= 1
    bob_result = next((r for r in results if r.provider_id == "bob_plumber"), None)
    assert bob_result is not None
    assert bob_result.degree == 1
    assert bob_result.path == ["alice", "bob_plumber"]


def test_bfs_second_degree_search(sample_graph):
    """Test BFS finds 2nd degree connections correctly."""
    results = sample_graph.bfs_search("alice", "plumber", max_degree=2)

    # Should find both bob_plumber (1st) and eve_plumber (2nd)
    provider_ids = [r.provider_id for r in results]
    assert "bob_plumber" in provider_ids
    assert "eve_plumber" in provider_ids

    # Verify eve is marked as 2nd degree
    eve_result = next((r for r in results if r.provider_id == "eve_plumber"), None)
    assert eve_result is not None
    assert eve_result.degree == 2
    assert len(eve_result.path) == 3  # alice -> carol -> eve_plumber


def test_bfs_category_filtering(sample_graph):
    """Test BFS correctly filters by category."""
    plumber_results = sample_graph.bfs_search("alice", "plumber", max_degree=2)
    mechanic_results = sample_graph.bfs_search("alice", "mechanic", max_degree=2)

    # Plumber results should not contain mechanics
    plumber_ids = [r.provider_id for r in plumber_results]
    assert "dave_mechanic" not in plumber_ids

    # Mechanic results should find dave
    mechanic_ids = [r.provider_id for r in mechanic_results]
    assert "dave_mechanic" in mechanic_ids


def test_bfs_ranking_by_degree(sample_graph):
    """Test that BFS results are sorted by degree of separation."""
    results = sample_graph.bfs_search("alice", "plumber", max_degree=2)

    # Results should be sorted by degree
    degrees = [r.degree for r in results]
    assert degrees == sorted(degrees)


def test_dfs_valid_path(sample_graph):
    """Test DFS finds valid trust paths."""
    path_result = sample_graph.dfs_trust_path("alice", "bob_plumber")

    assert path_result.valid is True
    assert path_result.cycle_detected is False
    assert "alice" in path_result.path
    assert "bob_plumber" in path_result.path
    assert path_result.path[0] == "alice"
    assert path_result.path[-1] == "bob_plumber"


def test_dfs_second_degree_path(sample_graph):
    """Test DFS traces 2nd degree paths correctly."""
    path_result = sample_graph.dfs_trust_path("alice", "dave_mechanic")

    assert path_result.valid is True
    assert len(path_result.path) == 3  # alice -> carol -> dave_mechanic
    assert path_result.path == ["alice", "carol", "dave_mechanic"]


def test_dfs_no_path(sample_graph):
    """Test DFS returns invalid when no path exists."""
    path_result = sample_graph.dfs_trust_path("alice", "nonexistent_provider")

    assert path_result.valid is False
    assert len(path_result.path) == 0


def test_dfs_cycle_detection():
    """Test DFS detects cycles correctly."""
    engine = GraphEngine()

    # Create a cycle: A -> B -> C -> A
    engine.add_edge("A", "B", "friend")
    engine.add_edge("B", "C", "friend")
    engine.add_edge("C", "A", "friend")

    # Search for a non-existent node to trigger cycle traversal
    path_result = engine.dfs_trust_path("A", "nonexistent")

    # Should not find path and should handle cycle gracefully
    assert path_result.valid is False


def test_get_full_graph(sample_graph):
    """Test full graph export for visualization."""
    graph_data = sample_graph.get_full_graph()

    assert "alice" in graph_data
    assert "carol" in graph_data
    assert len(graph_data["alice"]) >= 2  # alice has multiple edges

    # Verify edge structure
    alice_edges = graph_data["alice"]
    bob_edge = next((e for e in alice_edges if e["to"] == "bob_plumber"), None)
    assert bob_edge is not None
    assert bob_edge["category"] == "plumber"


def test_graph_statistics(sample_graph):
    """Test graph statistics methods."""
    node_count = sample_graph.get_node_count()
    edge_count = sample_graph.get_edge_count()

    assert node_count >= 5  # At least alice, carol, bob, dave, eve
    assert edge_count == 5  # 5 edges added in fixture


def test_empty_search():
    """Test search on empty graph."""
    engine = GraphEngine()
    results = engine.bfs_search("user1", "plumber")

    assert len(results) == 0


def test_multiple_paths_shortest_first(sample_graph):
    """Test that BFS returns shortest path when multiple paths exist."""
    # Add an alternate longer path
    sample_graph.add_edge("alice", "intermediate", "friend")
    sample_graph.add_edge("intermediate", "carol", "friend")

    results = sample_graph.bfs_search("alice", "mechanic", max_degree=3)

    # Should still find dave_mechanic via the shortest path
    dave_result = next((r for r in results if r.provider_id == "dave_mechanic"), None)
    assert dave_result is not None
    assert dave_result.degree == 2  # Shortest is still alice->carol->dave
