"""
Firebase Firestore Service
Handles data persistence with fallback to mock data for local development.
"""
import os
from typing import List, Dict, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime


class FirebaseService:
    """
    Service for interacting with Firebase Firestore.
    Falls back to mock data when Firebase credentials are not available.
    """

    def __init__(self):
        self.use_mock = True
        self.db = None

        # Try to initialize Firebase
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if creds_path and os.path.exists(creds_path):
            try:
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.use_mock = False
                print("✅ Firebase initialized successfully")
            except Exception as e:
                print(f"⚠️  Firebase initialization failed: {e}")
                print("📦 Using mock data instead")
        else:
            print("📦 No Firebase credentials found - using mock data")

        # Mock data for local development
        self.mock_vouches = self._generate_mock_vouches()
        self.mock_providers = self._generate_mock_providers()

    def _generate_mock_vouches(self) -> List[Dict]:
        """Generate realistic mock vouch data for testing."""
        return [
            # Alice's network
            {"from_user": "alice", "to_provider": "bob_plumber", "category": "plumber", "timestamp": "2024-01-01"},
            {"from_user": "alice", "to_provider": "carol", "category": "friend", "timestamp": "2024-01-02"},

            # Carol's network
            {"from_user": "carol", "to_provider": "dave_mechanic", "category": "mechanic", "timestamp": "2024-01-03"},
            {"from_user": "carol", "to_provider": "eve_plumber", "category": "plumber", "timestamp": "2024-01-04"},
            {"from_user": "carol", "to_provider": "frank", "category": "friend", "timestamp": "2024-01-05"},

            # Bob's network
            {"from_user": "bob_plumber", "to_provider": "grace_electrician", "category": "electrician", "timestamp": "2024-01-06"},

            # Frank's network
            {"from_user": "frank", "to_provider": "henry_babysitter", "category": "babysitter", "timestamp": "2024-01-07"},
            {"from_user": "frank", "to_provider": "iris_cleaner", "category": "cleaner", "timestamp": "2024-01-08"},

            # Additional realistic connections
            {"from_user": "alice", "to_provider": "jack_mechanic", "category": "mechanic", "timestamp": "2024-01-09"},
            {"from_user": "dave_mechanic", "to_provider": "kate_plumber", "category": "plumber", "timestamp": "2024-01-10"},
        ]

    def _generate_mock_providers(self) -> Dict[str, Dict]:
        """Generate mock provider metadata."""
        return {
            "bob_plumber": {"name": "Bob's Plumbing", "rating": 4.8, "category": "plumber"},
            "eve_plumber": {"name": "Eve's Pipes", "rating": 4.5, "category": "plumber"},
            "dave_mechanic": {"name": "Dave's Auto", "rating": 4.9, "category": "mechanic"},
            "jack_mechanic": {"name": "Jack's Garage", "rating": 4.6, "category": "mechanic"},
            "grace_electrician": {"name": "Grace Electric", "rating": 4.7, "category": "electrician"},
            "henry_babysitter": {"name": "Henry's Childcare", "rating": 5.0, "category": "babysitter"},
            "iris_cleaner": {"name": "Iris Cleaning Co", "rating": 4.4, "category": "cleaner"},
            "kate_plumber": {"name": "Kate's Plumbing", "rating": 4.3, "category": "plumber"},
        }

    def load_vouches(self) -> List[Dict]:
        """
        Load all vouches from Firebase or return mock data.
        """
        if self.use_mock:
            return self.mock_vouches

        try:
            vouches_ref = self.db.collection('vouches')
            docs = vouches_ref.stream()

            vouches = []
            for doc in docs:
                data = doc.to_dict()
                vouches.append(data)

            return vouches if vouches else self.mock_vouches
        except Exception as e:
            print(f"Error loading vouches from Firebase: {e}")
            return self.mock_vouches

    def get_provider(self, provider_id: str) -> Dict:
        """
        Get provider metadata by ID.
        """
        if self.use_mock:
            return self.mock_providers.get(provider_id, {
                "name": provider_id.replace("_", " ").title(),
                "rating": 4.0,
                "category": "unknown"
            })

        try:
            provider_ref = self.db.collection('providers').document(provider_id)
            doc = provider_ref.get()

            if doc.exists:
                return doc.to_dict()
            else:
                return self.mock_providers.get(provider_id, {"name": "Unknown", "rating": 0.0})
        except Exception as e:
            print(f"Error fetching provider: {e}")
            return {"name": "Unknown", "rating": 0.0}

    def save_vouch(self, vouch_data: Dict) -> str:
        """
        Save a new vouch to Firebase.
        Returns the vouch ID.
        """
        if self.use_mock:
            # Just add to mock data and return a fake ID
            vouch_id = f"vouch_{len(self.mock_vouches) + 1}"
            self.mock_vouches.append(vouch_data)
            print(f"📝 Mock vouch saved: {vouch_id}")
            return vouch_id

        try:
            vouch_data["created_at"] = datetime.now()
            vouches_ref = self.db.collection('vouches')
            doc_ref = vouches_ref.add(vouch_data)
            return doc_ref[1].id
        except Exception as e:
            print(f"Error saving vouch: {e}")
            raise
