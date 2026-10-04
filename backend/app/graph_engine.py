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

    def get_full_graph(self) -> Dict[str, any]:
        """
        Export the full graph structure for client-side visualization.
        Returns nodes with explicit types/degrees and edges list.

        Returns:
            Dictionary with 'nodes' (array of {id, label, type, degree}) and 'edges' (array of {source, target, weight})
        """
        # Build node degree map: count connections for each node
        node_degrees: Dict[str, int] = {}
        all_nodes: Set[str] = set()

        # Count degrees from adjacency
        for user_id, edges in self.adjacency.items():
            all_nodes.add(user_id)
            node_degrees[user_id] = len(edges)
            for provider_id in edges.keys():
                all_nodes.add(provider_id)
                # Also count reverse: if provider has edges coming back
                if provider_id in self.adjacency:
                    node_degrees[provider_id] = node_degrees.get(provider_id, 0) + len(
                        self.adjacency[provider_id]
                    )

        # Classify node types based on degree
        def classify_node(node_id: str) -> Tuple[str, int]:
            """Return (type_label, degree) for a node."""
            degree = node_degrees.get(node_id, 0)
            if degree == 0:
                # Isolated node - check if it's the user's own ID pattern
                label = node_id.split('_')[0].title() if '_' in node_id else node_id
                return ("user", 0)
            elif degree == 1:
                return ("user", 1)  # 1st degree connection
            elif degree == 2:
                return ("user", 2)  # 2nd degree connection
            else:
                return ("provider", degree)  # Service provider

        # Build nodes array
        nodes = []
        for node_id in all_nodes:
            node_type, degree = classify_node(node_id)
            # Determine label
            if node_id == node_id:  # Will be checked against user_id in caller
                label = "You" if False else node_id.split('_')[0].title()
            else:
                label = node_id.split('_')[0].title()
            nodes.append({
                "id": node_id,
                "label": label,
                "type": node_type,
                "degree": degree
            })

        # Build edges array
        edges = []
        seen_edges: Set[str] = set()
        for from_user, target_edges in self.adjacency.items():
            for to_provider, edge_data in target_edges.items():
                edge_key = f"{from_user}->{to_provider}"
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source": from_user,
                        "target": to_provider,
                        "weight": 1,
                        "category": edge_data.get("category", "")
                    })

        return {"nodes": nodes, "edges": edges}

    def get_node_count(self) -> int:
        """Get total number of unique nodes in the graph."""
        all_nodes = set(self.adjacency.keys())
        for edges in self.adjacency.values():
            all_nodes.update(edges.keys())
        return len(all_nodes)

    def remove_edge(self, from_user: str, to_provider: str):
        """Remove a vouch edge and rebuild indexes."""
        if from_user in self.adjacency and to_provider in self.adjacency[from_user]:
            edge_data = self.adjacency[from_user][to_provider]
            category = edge_data.get("category", "")
            del self.adjacency[from_user][to_provider]
            if not self.adjacency[from_user]:
                del self.adjacency[from_user]
            # Update provider index
            if to_provider in self.providers and from_user in self.providers[to_provider]:
                self.providers[to_provider].discard(from_user)
                if not self.providers[to_provider]:
                    del self.providers[to_provider]
            # Update category index
            if category and category in self.category_map:
                if to_provider in self.category_map[category] and from_user in self.category_map[category][to_provider]:
                    self.category_map[category][to_provider].discard(from_user)
                    if not self.category_map[category][to_provider]:
                        del self.category_map[category][to_provider]
                    if not self.category_map[category]:
                        del self.category_map[category]

    def update_edge(self, from_user: str, to_provider: str, new_category: str = None, timestamp: str = None):
        """Edit existing vouch edge in-place."""
        if from_user not in self.adjacency or to_provider not in self.adjacency[from_user]:
            return False
        old_data = self.adjacency[from_user][to_provider]
        old_category = old_data.get("category", "")
        new_data = {"category": new_category or old_category, "timestamp": timestamp or old_data.get("timestamp", "")}
        self.adjacency[from_user][to_provider] = new_data
        # Update category index if changed
        if new_category and new_category != old_category:
            if old_category and old_category in self.category_map:
                if to_provider in self.category_map[old_category] and from_user in self.category_map[old_category][to_provider]:
                    self.category_map[old_category][to_provider].discard(from_user)
            if new_category not in self.category_map:
                self.category_map[new_category] = defaultdict(set)
            self.category_map[new_category][to_provider].add(from_user)
        return True

    def get_edge_count(self) -> int:
        """Get total number of edges in the graph."""
        return sum(len(edges) for edges in self.adjacency.values())
