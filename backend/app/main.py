"""
FastAPI Backend for Vouch Trust Network
Provides graph search endpoints powered by BFS, DFS, and Hash Maps.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.graph_engine import GraphEngine, SearchResult, TrustPath
from app.firebase_service import FirebaseService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Vouch API",
    description="Real-time Trust Network API powered by Graph Theory",
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

# Global graph engine and Firebase service
graph_engine = GraphEngine()
firebase_service = FirebaseService()


# Pydantic models for request/response
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
            from_user=vouch["from_user"],
            to_provider=vouch["to_provider"],
            category=vouch["category"],
            timestamp=vouch.get("timestamp", "")
        )

    print(f"✅ Loaded {len(vouches)} vouches into graph")
    print(f"📊 Graph: {graph_engine.get_node_count()} nodes, {graph_engine.get_edge_count()} edges")


@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "app": "Vouch Trust Network API",
        "version": "1.0.0",
        "description": "Graph Theory-powered social proximity search",
        "endpoints": {
            "health": "/health",
            "api_docs": "/docs",
            "search": "/api/search",
            "trust_path": "/api/trust-path",
            "graph": "/api/graph/full",
            "vouch": "/api/vouch",
            "categories": "/api/categories"
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
    to_id: str = Query(..., description="Target provider ID")
):
    """
    DFS-powered trust path verification.
    Traces the exact line of trust from user to provider.
    """
    if not from_id or not to_id:
        raise HTTPException(status_code=400, detail="from_id and to_id are required")

    # Execute DFS path tracing
    trust_path = graph_engine.dfs_trust_path(from_id, to_id)

    return {
        "path": trust_path.path,
        "valid": trust_path.valid,
        "cycle_detected": trust_path.cycle_detected
    }


@app.get("/api/graph/full", response_model=FullGraphResponse)
async def get_full_graph():
    """
    Export full graph structure for client-side visualization.
    Returns adjacency list with all nodes and edges.
    """
    graph_data = graph_engine.get_full_graph()

    # Convert to response format
    formatted_nodes = {}
    for node_id, edges in graph_data.items():
        formatted_nodes[node_id] = [
            GraphNode(
                to=edge["to"],
                category=edge["category"],
                timestamp=edge["timestamp"]
            )
            for edge in edges
        ]

    return {
        "nodes": formatted_nodes,
        "node_count": graph_engine.get_node_count(),
        "edge_count": graph_engine.get_edge_count()
    }


@app.post("/api/vouch")
async def create_vouch(vouch: VouchRequest):
    """
    Submit a new vouch (endorsement).
    Adds an edge to the graph and persists to Firebase.
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
