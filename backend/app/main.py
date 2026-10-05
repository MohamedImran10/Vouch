"""
FastAPI Backend for Vouch Trust Network
Provides graph search, CRUD operations, and authentication
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.graph_engine import SearchResult, TrustPath
from app.services import firebase_service, graph_engine
from app.auth import get_current_user, get_optional_user
from app.routers import auth, users, providers, reviews, connections
from app.routers import vouches as vouch_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Vouch API",
    description="Real-time Trust Network API powered by Graph Theory with Authentication",
    version="1.0.0"
)

# CORS middleware for Flutter web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Include Routers
# ============================================================================

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(providers.router)
app.include_router(reviews.router)
app.include_router(connections.router)
app.include_router(vouch_router.router)


# Pydantic models for legacy endpoints
class VouchRequest(BaseModel):
    from_user: str
    to_provider: str
    category: str
    timestamp: Optional[str] = None


class SearchResponse(BaseModel):
    provider_id: str
    degree: int
    path: List[str]
    category: str
    provider_name: Optional[str] = None
    provider_rating: Optional[float] = None


class TrustPathResponse(BaseModel):
    path: List[str]
    valid: bool
    cycle_detected: bool
    reachable: bool = True
    reason: Optional[str] = None


class GraphNode(BaseModel):
    to: str
    category: str
    timestamp: str


class FullGraphResponse(BaseModel):
    nodes: dict[str, List[GraphNode]]
    node_count: int
    edge_count: int


class HealthResponse(BaseModel):
    status: str
    graph_nodes: int
    graph_edges: int


@app.on_event("startup")
async def startup_event():
    """Initialize graph from Firebase or mock data on startup."""
    print("🚀 Starting Vouch Backend...")

    # Load graph data from Firebase or use mock data
    vouches = firebase_service.load_vouches()

    for vouch in vouches:
        graph_engine.add_edge(
            from_user=vouch.get("from_user_id", vouch.get("from_user", "")),
            to_provider=vouch.get("to_provider_id", vouch.get("to_provider", "")),
            category=vouch["category"],
            timestamp=vouch.get("timestamp", "")
        )

    if firebase_service.use_mock and vouches:
        primary_user_id = vouches[0].get("from_user_id", vouches[0].get("from_user"))
        if primary_user_id:
            graph_engine.ensure_connected(primary_user_id)

    print(f"✅ Loaded {len(vouches)} vouches into graph")
    print(f"📊 Graph: {graph_engine.get_node_count()} nodes, {graph_engine.get_edge_count()} edges")


# ============================================================================
# Public Endpoints (No Auth Required)
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "app": "Vouch Trust Network API",
        "version": "1.0.0",
        "description": "Graph Theory-powered social proximity search with Authentication",
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "search": "/api/search",
            "trust_path": "/api/trust-path",
            "graph": "/api/graph/full",
            "vouch": "/api/vouch",
            "categories": "/api/categories",
            "auth_register": "/api/auth/register",
            "auth_login": "/api/auth/login",
            "auth_logout": "/api/auth/logout",
            "auth_me": "/api/auth/me",
            "users": "/api/users",
            "providers": "/api/providers",
            "reviews": "/api/reviews"
        },
        "graph_stats": {
            "nodes": graph_engine.get_node_count(),
            "edges": graph_engine.get_edge_count()
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and preventing cold starts.
    """
    return {
        "status": "ok",
        "graph_nodes": graph_engine.get_node_count(),
        "graph_edges": graph_engine.get_edge_count()
    }


# ============================================================================
# Graph Search Endpoints (Original Features)
# ============================================================================

@app.get("/api/search", response_model=List[SearchResponse])
async def search_providers(
    user_id: str = Query(..., description="User ID to search from"),
    category: str = Query(..., description="Service category (e.g., plumber, mechanic)"),
    max_degree: int = Query(2, ge=1, le=3, description="Maximum degrees of separation")
):
    """
    BFS-powered social proximity search.
    Returns providers ranked by degrees of separation from the user.
    """
    if not user_id or not category:
        raise HTTPException(status_code=400, detail="user_id and category are required")

    # Execute BFS search
    results = graph_engine.bfs_search(user_id, category.lower(), max_degree)

    # Enhance results with provider metadata from Firebase
    enhanced_results = []
    for result in results:
        provider_data = firebase_service.get_provider(result.provider_id)
        enhanced_results.append({
            "provider_id": result.provider_id,
            "degree": result.degree,
            "path": result.path,
            "category": result.category,
            "provider_name": provider_data.get("name", "Unknown Provider"),
            "provider_rating": provider_data.get("rating", 0.0)
        })

    return enhanced_results


@app.get("/api/trust-path", response_model=TrustPathResponse)
async def get_trust_path(
    from_id: str = Query(..., description="Starting user ID"),
    to_id: str = Query(..., description="Target provider ID"),
    category: Optional[str] = Query(None, description="Optional service category filter")
):
    """
    DFS-powered trust path verification.
    Traces the exact line of trust from user to provider.
    """
    if not from_id or not to_id:
        raise HTTPException(status_code=400, detail="from_id and to_id are required")

    # Execute DFS path tracing
    trust_path = graph_engine.dfs_trust_path(from_id, to_id, category)

    return {
        "path": trust_path.path,
        "valid": trust_path.valid,
        "cycle_detected": trust_path.cycle_detected,
        "reachable": trust_path.reachable,
        "reason": trust_path.reason,
    }


@app.get("/api/graph/full")
async def get_full_graph(current_user: Optional[dict] = Depends(get_optional_user)):
    """
    Export full graph structure for client-side visualization.
    Returns nodes with explicit types/degrees and edges list.
    """
    graph_data = graph_engine.get_full_graph()

    # graph_data is {"nodes": [...], "edges": [...]}
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Merge the seeded root and signed-in user's mock edges under the active account ID.
    user_id = current_user.get("user_id") if current_user else None
    if firebase_service.use_mock and user_id and user_id != "alice":
        remapped_nodes = {}
        for node in nodes:
            node_id = user_id if node["id"] == "alice" else node["id"]
            if node_id in remapped_nodes:
                remapped_nodes[node_id]["degree"] += node.get("degree", 0)
            else:
                remapped_nodes[node_id] = {**node, "id": node_id}
        nodes = list(remapped_nodes.values())

        remapped_edges = {}
        for edge in edges:
            source = user_id if edge["source"] == "alice" else edge["source"]
            target = user_id if edge["target"] == "alice" else edge["target"]
            if source == target:
                continue
            remapped_edges[(source, target, edge.get("category"))] = {
                **edge,
                "source": source,
                "target": target,
            }
        edges = list(remapped_edges.values())

    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


# ============================================================================
# Legacy vouch endpoint - backward compatibility
# ============================================================================

@app.post("/api/vouch")
async def create_vouch_legacy(vouch: VouchRequest):
    """
    Legacy vouch endpoint for backward compatibility.
    Submit a new vouch (endorsement).
    """
    # Add to graph
    graph_engine.add_edge(
        from_user=vouch.from_user,
        to_provider=vouch.to_provider,
        category=vouch.category.lower(),
        timestamp=vouch.timestamp
    )

    # Persist to Firebase
    vouch_id = firebase_service.save_vouch({
        "from_user": vouch.from_user,
        "to_provider": vouch.to_provider,
        "category": vouch.category.lower(),
        "timestamp": vouch.timestamp
    })

    return {
        "status": "success",
        "vouch_id": vouch_id,
        "message": "Vouch added successfully"
    }


# ============================================================================
# Categories Endpoint
# ============================================================================

@app.get("/api/categories")
async def get_categories():
    """
    Get list of available service categories.
    """
    return {
        "categories": [
            {"id": "plumber", "name": "Plumbers", "icon": "🔧"},
            {"id": "mechanic", "name": "Mechanics", "icon": "🔩"},
            {"id": "babysitter", "name": "Babysitters", "icon": "👶"},
            {"id": "electrician", "name": "Electricians", "icon": "⚡"},
            {"id": "cleaner", "name": "Cleaners", "icon": "🧹"}
        ]
    }


# ============================================================================
# Error Handlers
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
