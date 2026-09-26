"""
Graph Engine for Vouch Trust Network
Implements BFS, DFS, and Hash Map-based adjacency list for social proximity search.
"""
from collections import defaultdict, deque
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VouchEdge:
    """Represents a trust edge in the social graph."""
    from_user: str
    to_provider: str
    category: str
    timestamp: Optional[str] = None


@dataclass
class SearchResult:
    """Result from BFS search with social proximity metadata."""
    provider_id: str
    degree: int  # 1 = 1st degree, 2 = 2nd degree
    path: List[str]  # Shortest path from user to provider
    category: str


@dataclass
class TrustPath:
    """Result from DFS trust path verification."""
    path: List[str]
    valid: bool
    cycle_detected: bool = False


class GraphEngine:
    """
    In-memory graph engine using Hash Map adjacency list.
    Optimized for O(1) edge additions and category lookups.
    """

    def __init__(self):
        # adjacency[user_id][provider_id] = {category, timestamp}
        self.adjacency: Dict[str, Dict[str, Dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
        # Reverse index: providers[provider_id] = set of user_ids who vouched
        self.providers: Dict[str, Set[str]] = defaultdict(set)
        # Category index: category_map[category][provider_id] = set of vouchers
        self.category_map: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    def add_edge(self, from_user: str, to_provider: str, category: str, timestamp: str = None):
        """
        Add a vouch edge to the graph with O(1) complexity.

        Args:
            from_user: User ID who vouched
            to_provider: Provider ID being vouched for
            category: Service category (e.g., 'plumber', 'mechanic')
            timestamp: Optional timestamp of the vouch
        """
        edge_data = {"category": category, "timestamp": timestamp or ""}
        self.adjacency[from_user][to_provider] = edge_data
        self.providers[to_provider].add(from_user)
        self.category_map[category][to_provider].add(from_user)

    def bfs_search(self, user_id: str, category: str, max_degree: int = 2) -> List[SearchResult]:
        """
        Execute Breadth-First Search to find providers by social proximity.

        Args:
            user_id: Starting user ID
            category: Service category to filter
            max_degree: Maximum degrees of separation (default: 2)

        Returns:
            List of SearchResult objects ranked by degree of separation
        """
        results = []
        visited = {user_id}
        queue = deque([(user_id, 0, [user_id])])  # (current_node, degree, path)

        # Track found providers to avoid duplicates
        found_providers = set()

        while queue:
            current, degree, path = queue.popleft()

            # Stop if we've exceeded max degree
            if degree > max_degree:
                continue

            # Check if current node has vouched for any providers in this category
            if current in self.adjacency:
                for provider_id, edge_data in self.adjacency[current].items():
                    if edge_data["category"] == category and provider_id not in found_providers:
                        found_providers.add(provider_id)
                        results.append(SearchResult(
                            provider_id=provider_id,
                            degree=degree + 1,  # +1 because the edge to provider is the next hop
                            path=path + [provider_id],
                            category=category
                        ))

            # Explore neighbors (friends of current user)
            if current in self.adjacency:
                for neighbor in self.adjacency[current].keys():
                    # Only traverse user->user edges (not user->provider edges for BFS expansion)
                    # In this simplified model, we treat all outgoing edges as potential friends
                    if neighbor not in visited and neighbor not in found_providers:
                        visited.add(neighbor)
                        queue.append((neighbor, degree + 1, path + [neighbor]))

        # Sort by degree (1st degree first, then 2nd degree)
        results.sort(key=lambda r: r.degree)
        return results

    def dfs_trust_path(self, from_user: str, to_provider: str) -> TrustPath:
        """
        Execute Depth-First Search to trace a trust path.
        Includes cycle detection.

        Args:
            from_user: Starting user ID
            to_provider: Target provider ID

        Returns:
            TrustPath object with path and validation status
        """
        visited = set()
        rec_stack = set()  # For cycle detection
        path = []

        def dfs_helper(current: str, target: str) -> bool:
            """Recursive DFS helper with cycle detection."""
            if current in rec_stack:
                return False  # Cycle detected

            if current == target:
                path.append(current)
                return True

            visited.add(current)
            rec_stack.add(current)
            path.append(current)

            # Explore neighbors
            if current in self.adjacency:
                for neighbor in self.adjacency[current].keys():
                    if neighbor not in visited or neighbor == target:
                        if dfs_helper(neighbor, target):
                            return True

            # Backtrack
            path.pop()
            rec_stack.remove(current)
            return False

        # Execute DFS
        found = dfs_helper(from_user, to_provider)
        cycle_detected = len(rec_stack) > 0 and not found

        return TrustPath(
            path=path if found else [],
            valid=found,
            cycle_detected=cycle_detected
        )

    def get_full_graph(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Export the full adjacency list for client-side visualization.

        Returns:
            Dictionary mapping node IDs to lists of edge dictionaries
        """
        graph_data = {}
        for user_id, edges in self.adjacency.items():
            graph_data[user_id] = [
                {
                    "to": provider_id,
                    "category": edge_data["category"],
                    "timestamp": edge_data.get("timestamp", "")
                }
                for provider_id, edge_data in edges.items()
            ]
        return graph_data

    def get_node_count(self) -> int:
        """Get total number of unique nodes in the graph."""
        all_nodes = set(self.adjacency.keys())
        for edges in self.adjacency.values():
            all_nodes.update(edges.keys())
        return len(all_nodes)

    def get_edge_count(self) -> int:
        """Get total number of edges in the graph."""
        return sum(len(edges) for edges in self.adjacency.values())
