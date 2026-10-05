"""
Firebase Firestore Service
Handles data persistence with fallback to mock data for local development.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ModuleNotFoundError:  # Firebase is optional; use mock mode when unavailable
    firebase_admin = None
    credentials = None
    firestore = None


class FirebaseService:
    """
    Service for interacting with Firebase Firestore.
    Falls back to mock data when Firebase credentials are not available.
    """

    def __init__(self):
        self.use_mock = True
        self.db = None

        # Mock data for local development must always be available.
        self.mock_vouches = self._generate_mock_vouches()
        for index, vouch in enumerate(self.mock_vouches, start=1):
            vouch.setdefault("id", f"mock_vouch_{index}")
        self.mock_providers = self._generate_mock_providers()
        self.mock_connections = {}

        # Try to initialize Firebase only when the optional dependency is installed.
        if firebase_admin is None:
            print("📦 Firebase admin SDK not installed - using mock data")
            return

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

    def _generate_mock_vouches(self) -> List[Dict]:
        """Generate realistic mock vouch data for testing."""
        return [
            # Alice's network
            {"from_user": "alice", "to_provider": "carol", "category": "friend", "timestamp": "2024-01-02"},
            {"from_user": "alice", "to_provider": "bob_plumber", "category": "plumber", "timestamp": "2024-01-01"},

            # Carol's network
            {"from_user": "carol", "to_provider": "dave_mechanic", "category": "mechanic", "timestamp": "2024-01-03"},
            {"from_user": "carol", "to_provider": "eve_plumber", "category": "plumber", "timestamp": "2024-01-04"},
            {"from_user": "eve_plumber", "to_provider": "nanny_babysitters", "category": "babysitter", "timestamp": "2024-01-04T18:00:00"},
            {"from_user": "carol", "to_provider": "grace_electrician", "category": "electrician", "timestamp": "2024-01-04T12:00:00"},
            {"from_user": "carol", "to_provider": "frank", "category": "friend", "timestamp": "2024-01-05"},
            {"from_user": "carol", "to_provider": "bob_plumber", "category": "plumber", "timestamp": "2024-01-05T12:00:00"},

            # Bob's network
            {"from_user": "bob_plumber", "to_provider": "grace_electrician", "category": "electrician", "timestamp": "2024-01-06"},

            # Alice also has a direct route to Grace; DFS reaches Grace through Carol first.
            {"from_user": "alice", "to_provider": "grace_electrician", "category": "electrician", "timestamp": "2024-01-06T12:00:00"},

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
            "nanny_babysitters": {"name": "Nanny Babysitters", "rating": 4.8, "category": "babysitter"},
            "dave_mechanic": {"name": "Dave's Auto", "rating": 4.9, "category": "mechanic"},
            "jack_mechanic": {"name": "Jack's Garage", "rating": 4.6, "category": "mechanic"},
            "grace_electrician": {"name": "Grace Electric", "rating": 4.7, "category": "electrician"},
            "henry_babysitter": {"name": "Henry's Childcare", "rating": 5.0, "category": "babysitter"},
            "iris_cleaner": {"name": "Iris Cleaning Co", "rating": 4.4, "category": "cleaner"},
            "kate_plumber": {"name": "Kate's Plumbing", "rating": 4.3, "category": "plumber"},
        }

    def load_vouches(
        self,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Load all vouches from Firebase or return mock data.
        """
        if self.use_mock:
            vouches = [dict(vouch) for vouch in self.mock_vouches]
        else:
            try:
                docs = self.db.collection('vouches').stream()
                vouches = []
                for doc in docs:
                    data = doc.to_dict() or {}
                    data.setdefault("id", doc.id)
                    vouches.append(data)
            except Exception as e:
                print(f"Error loading vouches from Firebase: {e}")
                raise

        if category is not None:
            category_filter = category.lower()
            vouches = [
                vouch for vouch in vouches
                if str(vouch.get("category", "")).lower() == category_filter
            ]
        if user_id is not None:
            vouches = [
                vouch for vouch in vouches
                if vouch.get("from_user_id", vouch.get("from_user")) == user_id
            ]
        if limit is not None:
            vouches = vouches[:limit]
        return vouches

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
            vouch_id = f"vouch_{uuid4().hex}"
            stored_vouch = dict(vouch_data)
            stored_vouch["id"] = vouch_id
            self.mock_vouches.append(stored_vouch)
            print(f"📝 Mock vouch saved: {vouch_id}")
            return vouch_id

        try:
            stored_vouch = dict(vouch_data)
            stored_vouch["created_at"] = datetime.now()
            vouches_ref = self.db.collection('vouches')
            doc_ref = vouches_ref.add(stored_vouch)[1]
            doc_ref.update({"id": doc_ref.id})
            return doc_ref.id
        except Exception as e:
            print(f"Error saving vouch: {e}")
            raise

    def load_vouch_by_id(self, vouch_id: str) -> Optional[Dict]:
        """Load a vouch by its document ID."""
        if self.use_mock:
            return next(
                (
                    dict(vouch)
                    for vouch in self.mock_vouches
                    if vouch.get("id", vouch.get("vouch_id")) == vouch_id
                ),
                None,
            )

        try:
            doc = self.db.collection('vouches').document(vouch_id).get()
            if not doc.exists:
                return None
            vouch = doc.to_dict() or {}
            vouch.setdefault("id", doc.id)
            return vouch
        except Exception as e:
            print(f"Error loading vouch: {e}")
            raise

    def update_vouch(self, vouch_id: str, updates: Dict) -> bool:
        """Update an existing vouch."""
        if self.use_mock:
            for vouch in self.mock_vouches:
                if vouch.get("id", vouch.get("vouch_id")) == vouch_id:
                    vouch.update(updates)
                    return True
            return False

        try:
            self.db.collection('vouches').document(vouch_id).update(updates)
            return True
        except Exception as e:
            print(f"Error updating vouch: {e}")
            raise

    def delete_vouch(self, vouch_id: str) -> bool:
        """Delete an existing vouch."""
        if self.use_mock:
            initial_count = len(self.mock_vouches)
            self.mock_vouches = [
                vouch for vouch in self.mock_vouches
                if vouch.get("id", vouch.get("vouch_id")) != vouch_id
            ]
            return len(self.mock_vouches) != initial_count

        try:
            doc_ref = self.db.collection('vouches').document(vouch_id)
            if not doc_ref.get().exists:
                return False
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting vouch: {e}")
            raise

    # ============================================================================
    # User Management
    # ============================================================================

    def create_user(self, user_data: Dict) -> str:
        """
        Create a new user in Firestore.
        Returns the user ID.
        """
        if self.use_mock:
            user_id = f"user_{len([k for k in self.mock_providers.keys()]) + 1}"
            user_data["id"] = user_id
            self.mock_providers[user_id] = user_data
            print(f"📝 Mock user created: {user_id}")
            return user_id

        try:
            users_ref = self.db.collection('users')
            doc_ref = users_ref.add(user_data)
            user_id = doc_ref[1].id
            # Update document with its own ID
            doc_ref[1].update({"id": user_id})
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[Dict]:
        """
        Get user by ID.
        """
        if self.use_mock:
            user = self.mock_providers.get(user_id)
            if user and "hashed_password" in user:
                return user
            return None

        try:
            user_ref = self.db.collection('users').document(user_id)
            doc = user_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Get user by email address.
        """
        if self.use_mock:
            for user in self.mock_providers.values():
                if isinstance(user, dict) and user.get("email") == email:
                    return user
            return None

        try:
            users_ref = self.db.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            docs = query.stream()

            for doc in docs:
                return doc.to_dict()

            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def update_user(self, user_id: str, updates: Dict) -> bool:
        """
        Update user profile.
        Returns True if successful.
        """
        if self.use_mock:
            if user_id in self.mock_providers:
                self.mock_providers[user_id].update(updates)
                self.mock_providers[user_id]["updated_at"] = datetime.now().isoformat()
                print(f"📝 Mock user updated: {user_id}")
                return True
            return False

        try:
            updates["updated_at"] = datetime.now()
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update(updates)
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Delete user account.
        Returns True if successful.
        """
        if self.use_mock:
            if user_id in self.mock_providers:
                del self.mock_providers[user_id]
                print(f"🗑️  Mock user deleted: {user_id}")
                return True
            return False

        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    # ============================================================================
    # Provider Management
    # ============================================================================

    def create_provider(self, provider_data: Dict) -> str:
        """
        Create a new provider profile.
        Returns the provider ID.
        """
        if self.use_mock:
            provider_id = f"provider_{len(self.mock_providers) + 1}"
            provider_data["id"] = provider_id
            provider_data["rating"] = 0.0
            provider_data["review_count"] = 0
            provider_data["vouch_count"] = 0
            self.mock_providers[provider_id] = provider_data
            print(f"📝 Mock provider created: {provider_id}")
            return provider_id

        try:
            providers_ref = self.db.collection('providers')
            provider_data["rating"] = 0.0
            provider_data["review_count"] = 0
            provider_data["vouch_count"] = 0
            doc_ref = providers_ref.add(provider_data)
            provider_id = doc_ref[1].id
            doc_ref[1].update({"id": provider_id})
            return provider_id
        except Exception as e:
            print(f"Error creating provider: {e}")
            raise

    def get_provider_details(self, provider_id: str) -> Optional[Dict]:
        """
        Get detailed provider information (different from get_provider).
        """
        if self.use_mock:
            return self.mock_providers.get(provider_id)

        try:
            provider_ref = self.db.collection('providers').document(provider_id)
            doc = provider_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting provider details: {e}")
            return None

    def update_provider(self, provider_id: str, updates: Dict) -> bool:
        """
        Update provider profile.
        """
        if self.use_mock:
            if provider_id in self.mock_providers:
                self.mock_providers[provider_id].update(updates)
                self.mock_providers[provider_id]["updated_at"] = datetime.now().isoformat()
                return True
            return False

        try:
            updates["updated_at"] = datetime.now()
            provider_ref = self.db.collection('providers').document(provider_id)
            provider_ref.update(updates)
            return True
        except Exception as e:
            print(f"Error updating provider: {e}")
            return False

    def delete_provider(self, provider_id: str) -> bool:
        """
        Delete provider profile.
        """
        if self.use_mock:
            if provider_id in self.mock_providers:
                del self.mock_providers[provider_id]
                return True
            return False

        try:
            provider_ref = self.db.collection('providers').document(provider_id)
            provider_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting provider: {e}")
            return False

    def list_providers(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        List providers with optional category filter.
        """
        if self.use_mock:
            providers = [
                {**provider, "id": provider_id}
                for provider_id, provider in self.mock_providers.items()
                if isinstance(provider, dict) and "category" in provider
            ]
            if category:
                providers = [p for p in providers if p.get("category") == category]
            return providers[:limit]

        try:
            providers_ref = self.db.collection('providers')

            if category:
                query = providers_ref.where('category', '==', category).limit(limit)
            else:
                query = providers_ref.limit(limit)

            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error listing providers: {e}")
            return []

    # ============================================================================
    # Connection Management
    # ============================================================================

    def create_connection(self, connection_data: Dict) -> str:
        """Create a category-based connection record."""
        if self.use_mock:
            connection_id = f"connection_{len(self.mock_connections) + 1}"
            connection_data["id"] = connection_id
            connection_data["created_at"] = connection_data.get("created_at") or datetime.now().isoformat()
            connection_data["updated_at"] = connection_data.get("updated_at") or connection_data["created_at"]
            self.mock_connections[connection_id] = connection_data
            return connection_id

        try:
            conn_ref = self.db.collection('connections')
            doc_ref = conn_ref.add(connection_data)
            connection_id = doc_ref[1].id
            doc_ref[1].update({"id": connection_id})
            return connection_id
        except Exception as e:
            print(f"Error creating connection: {e}")
            raise

    def get_connection(self, connection_id: str) -> Optional[Dict]:
        """Get a connection by ID."""
        if self.use_mock:
            return self.mock_connections.get(connection_id)

        try:
            conn_ref = self.db.collection('connections').document(connection_id)
            doc = conn_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting connection: {e}")
            return None

    def list_connections(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List all category-based connections, optionally filtered by category."""
        if self.use_mock:
            connections = list(self.mock_connections.values())
            if category:
                connections = [c for c in connections if c.get("category") == category.lower()]
            return connections[:limit]

        try:
            conn_ref = self.db.collection('connections')
            if category:
                query = conn_ref.where('category', '==', category.lower()).limit(limit)
            else:
                query = conn_ref.limit(limit)
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error listing connections: {e}")
            return []

    def update_connection(self, connection_id: str, updates: Dict) -> bool:
        """Update a connection record."""
        if self.use_mock:
            if connection_id in self.mock_connections:
                self.mock_connections[connection_id].update(updates)
                self.mock_connections[connection_id]["updated_at"] = datetime.now().isoformat()
                return True
            return False

        try:
            updates["updated_at"] = datetime.now()
            conn_ref = self.db.collection('connections').document(connection_id)
            conn_ref.update(updates)
            return True
        except Exception as e:
            print(f"Error updating connection: {e}")
            return False

    def delete_connection(self, connection_id: str) -> bool:
        """Delete a connection record."""
        if self.use_mock:
            if connection_id in self.mock_connections:
                del self.mock_connections[connection_id]
                return True
            return False

        try:
            conn_ref = self.db.collection('connections').document(connection_id)
            conn_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting connection: {e}")
            return False

    # ============================================================================
    # Review Management
    # ============================================================================

    def create_review(self, review_data: Dict) -> str:
        """
        Create a new review.
        """
        if self.use_mock:
            review_id = f"review_{len(self.mock_vouches) + 1}"
            review_data["id"] = review_id
            self.mock_vouches.append(review_data)
            print(f"📝 Mock review created: {review_id}")
            return review_id

        try:
            reviews_ref = self.db.collection('reviews')
            doc_ref = reviews_ref.add(review_data)
            review_id = doc_ref[1].id
            doc_ref[1].update({"id": review_id})

            # Update provider rating
            self._update_provider_rating(review_data["provider_id"])

            return review_id
        except Exception as e:
            print(f"Error creating review: {e}")
            raise

    def get_review(self, review_id: str) -> Optional[Dict]:
        """
        Get review by ID.
        """
        if self.use_mock:
            for review in self.mock_vouches:
                if isinstance(review, dict) and review.get("id") == review_id:
                    return review
            return None

        try:
            review_ref = self.db.collection('reviews').document(review_id)
            doc = review_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting review: {e}")
            return None

    def update_review(self, review_id: str, updates: Dict) -> bool:
        """
        Update a review.
        """
        if self.use_mock:
            for review in self.mock_vouches:
                if isinstance(review, dict) and review.get("id") == review_id:
                    review.update(updates)
                    review["updated_at"] = datetime.now().isoformat()
                    return True
            return False

        try:
            updates["updated_at"] = datetime.now()
            review_ref = self.db.collection('reviews').document(review_id)
            review_ref.update(updates)

            # Recalculate provider rating
            review = self.get_review(review_id)
            if review:
                self._update_provider_rating(review["provider_id"])

            return True
        except Exception as e:
            print(f"Error updating review: {e}")
            return False

    def delete_review(self, review_id: str) -> bool:
        """
        Delete a review.
        """
        review = self.get_review(review_id)
        provider_id = review.get("provider_id") if review else None

        if self.use_mock:
            self.mock_vouches = [r for r in self.mock_vouches if r.get("id") != review_id]
            return True

        try:
            review_ref = self.db.collection('reviews').document(review_id)
            review_ref.delete()

            # Recalculate provider rating
            if provider_id:
                self._update_provider_rating(provider_id)

            return True
        except Exception as e:
            print(f"Error deleting review: {e}")
            return False

    def get_provider_reviews(self, provider_id: str) -> List[Dict]:
        """
        Get all reviews for a provider.
        """
        if self.use_mock:
            return [r for r in self.mock_vouches
                    if isinstance(r, dict) and r.get("provider_id") == provider_id]

        try:
            reviews_ref = self.db.collection('reviews')
            query = reviews_ref.where('provider_id', '==', provider_id)
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error getting provider reviews: {e}")
            return []

    def _update_provider_rating(self, provider_id: str):
        """
        Recalculate and update provider's average rating.
        """
        reviews = self.get_provider_reviews(provider_id)

        if not reviews:
            avg_rating = 0.0
            count = 0
        else:
            total = sum(r.get("rating", 0) for r in reviews)
            count = len(reviews)
            avg_rating = round(total / count, 1) if count > 0 else 0.0

        self.update_provider(provider_id, {
            "rating": avg_rating,
            "review_count": count
        })
