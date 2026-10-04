"""Shared application services used by API routes."""

from app.firebase_service import FirebaseService
from app.graph_engine import GraphEngine

firebase_service = FirebaseService()
graph_engine = GraphEngine()