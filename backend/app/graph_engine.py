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
    reachable: bool = True
    reason: Optional[str] = None


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

    def connected_components(self, category: Optional[str] = None) -> List[Set[str]]:
        """Return weakly connected components, optionally filtered by edge category."""
        normalized_category = (category or "").strip().lower()
        filter_category = normalized_category not in {"", "all", "every category"}
        neighbors: Dict[str, Set[str]] = defaultdict(set)
        for source, targets in self.adjacency.items():
            neighbors.setdefault(source, set())
            for target, edge_data in targets.items():
                edge_category = edge_data.get("category", "").lower()
                if filter_category and edge_category not in {normalized_category, "friend"}:
                    continue
                neighbors[source].add(target)
                neighbors[target].add(source)

        components = []
        unseen = set(neighbors)
        while unseen:
            start = unseen.pop()
            component = {start}
            queue = [start]
            for current in queue:
                for neighbor in neighbors[current]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
        return components

    def _adjacency_for(self, category: Optional[str] = None) -> Dict[str, List[Tuple[str, Dict[str, str]]]]:
        """Build an undirected traversal view without changing persisted edge direction."""
        normalized_category = (category or "").strip().lower()
        filter_category = normalized_category not in {"", "all", "every category"}
        adjacency: Dict[str, List[Tuple[str, Dict[str, str]]]] = defaultdict(list)
        for source, targets in self.adjacency.items():
            adjacency.setdefault(source, [])
            for target, edge_data in targets.items():
                edge_category = edge_data.get("category", "").lower()
                if filter_category and edge_category not in {normalized_category, "friend"}:
                    continue
                adjacency[source].append((target, edge_data))
                adjacency[target].append((source, edge_data))
        return adjacency

    def ensure_connected(self, root_id: Optional[str] = None) -> None:
        """Connect all existing nodes and link the root to a high-degree hub."""
        components = self.connected_components()
        if not components:
            return

        if root_id is None:
            root_id = next(iter(self.adjacency))
        degrees: Dict[str, int] = defaultdict(int)
        for component in components:
            for node_id in component:
                degrees.setdefault(node_id, 0)
        for source, targets in self.adjacency.items():
            for target in targets:
                degrees[source] += 1
                degrees[target] += 1

        candidates = [node_id for node_id in degrees if node_id != root_id]
        if not candidates:
            return
        hub_candidates = [node_id for node_id in candidates if degrees[node_id] >= 2]
        hub_id = max(hub_candidates or candidates, key=lambda node_id: degrees[node_id])
        if hub_id not in self.adjacency.get(root_id, {}):
            self.add_edge(root_id, hub_id, "friend")

        while True:
            components = self.connected_components()
            root_component = next((component for component in components if root_id in component), {root_id})
            disconnected = [component for component in components if component is not root_component]
            if not disconnected:
                break
            target_id = max(disconnected[0], key=lambda node_id: degrees.get(node_id, 0))
            self.add_edge(root_id, target_id, "friend")
            degrees[root_id] += 1
            degrees[target_id] += 1

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
        adjacency = self._adjacency_for()

        # Track found providers to avoid duplicates
        found_providers = set()

        while queue:
            current, degree, path = queue.popleft()

            # Stop if we've exceeded max degree
            if degree > max_degree:
                continue

            for neighbor, edge_data in adjacency.get(current, []):
                if edge_data["category"].lower() == category.lower() and neighbor not in found_providers and neighbor != user_id:
                    found_providers.add(neighbor)
                    results.append(SearchResult(
                        provider_id=neighbor,
                        degree=degree + 1,
                        path=path + [neighbor],
                        category=category
                    ))

            for neighbor, _ in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, degree + 1, path + [neighbor]))

        # Sort by degree (1st degree first, then 2nd degree)
        results.sort(key=lambda r: r.degree)
        return results

    def dfs_trust_path(self, from_user: str, to_provider: str, category: Optional[str] = None) -> TrustPath:
        """
        Execute Depth-First Search to trace a trust path.
        Includes cycle detection.

        Args:
            from_user: Starting user ID
            to_provider: Target provider ID
            category: Optional service category filter; all-category aliases bypass filtering

        Returns:
            TrustPath object with path and validation status
        """
        components = self.connected_components(category)
        start_component = next((component for component in components if from_user in component), set())
        target_component = next((component for component in components if to_provider in component), set())
        if not target_component:
            return TrustPath([], False, reachable=False, reason="NODE_NOT_FOUND")
        if not start_component or start_component is not target_component:
            return TrustPath([], False, reachable=False, reason="DISCONNECTED_COMPONENT")

        adjacency = self._adjacency_for(category)
        visited = set()
        rec_stack = set()  # For cycle detection
        path = []
        def dfs_helper(current: str, target: str, parent: Optional[str] = None) -> bool:
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
            for neighbor, _ in adjacency.get(current, []):
                if neighbor == parent:
                    continue
                if neighbor not in visited or neighbor == target:
                    if dfs_helper(neighbor, target, current):
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
            cycle_detected=cycle_detected,
            reachable=found,
            reason=None if found else "NO_DIRECTED_PATH",
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

        provider_ids = {
            target_id
            for source_edges in self.adjacency.values()
            for target_id, edge_data in source_edges.items()
            if edge_data.get("category", "").lower() != "friend"
        }

        # Provider identity comes from service vouches, not connection count.
        def classify_node(node_id: str) -> Tuple[str, int]:
            """Return (type_label, degree) for a node."""
            degree = node_degrees.get(node_id, 0)
            return ("provider" if node_id in provider_ids else "person", degree)

        # Build nodes array
        nodes = []
        for node_id in all_nodes:
            node_type, degree = classify_node(node_id)
            # Determine label
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
