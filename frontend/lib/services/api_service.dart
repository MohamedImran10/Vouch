import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../models/models.dart';

class ApiService {
  // Update this to your deployed backend URL in production
  static const String baseUrl = 'http://localhost:8001';

  final FlutterSecureStorage? _storage;

  /// Create ApiService with optional storage
  ApiService([this._storage]);

  /// Get JWT token from storage
  Future<String?> _getToken() async {
    if (_storage != null) {
      return await _storage!.read(key: 'jwt_token');
    }
    return null;
  }

  Future<Map<String, String>> _authenticatedJsonHeaders() async {
    final token = await _getToken();
    if (token == null) {
      throw Exception('Not authenticated');
    }
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Search for providers using BFS
  Future<List<SearchResult>> searchProviders({
    required String userId,
    required String category,
    int maxDegree = 2,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/search').replace(
        queryParameters: {
          'user_id': userId,
          'category': category,
          'max_degree': maxDegree.toString(),
        },
      );

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => SearchResult.fromJson(json)).toList();
      } else {
        throw Exception('Failed to search providers: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error searching providers: $e');
    }
  }

  /// Get trust path using DFS
  Future<TrustPath> getTrustPath({
    required String fromId,
    required String toId,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/trust-path')
          .replace(queryParameters: {'from_id': fromId, 'to_id': toId});

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        return TrustPath.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to get trust path: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting trust path: $e');
    }
  }

  /// Get full graph for visualization
  Future<Map<String, dynamic>> getFullGraph() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/graph/full'));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get graph: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting graph: $e');
    }
  }

  /// Create a new vouch
  Future<void> createVouch(VouchEdge vouch) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/vouch'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(vouch.toJson()),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to create vouch: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error creating vouch: $e');
    }
  }

  /// Get available service categories
  Future<List<ServiceCategory>> getCategories() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/categories'));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> categories = data['categories'];
        return categories
            .map((json) => ServiceCategory.fromJson(json))
            .toList();
      } else {
        throw Exception('Failed to get categories: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting categories: $e');
    }
  }

  /// Get vouches with category/user filters (CRUD READ)
  Future<List<Map<String, dynamic>>> getVouches({
    String? category,
    String? userId,
  }) async {
    try {
      final params = <String, String>{};
      if (category != null) params['category'] = category;
      if (userId != null) params['user_id'] = userId;
      final uri = Uri.parse('$baseUrl/api/vouches')
          .replace(queryParameters: params.isNotEmpty ? params : null);
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final data = json.decode(response.body) as List<dynamic>;
        return data
            .map((vouch) => Map<String, dynamic>.from(vouch as Map))
            .toList();
      } else {
        throw Exception('Failed to get vouches: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting vouches: $e');
    }
  }

  /// Create vouch via full CRUD endpoint
  Future<Map<String, dynamic>> createVouchCrud(
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/vouches'),
        headers: await _authenticatedJsonHeaders(),
        body: json.encode(data),
      );
      if (response.statusCode == 200 || response.statusCode == 201) {
        return Map<String, dynamic>.from(json.decode(response.body) as Map);
      } else {
        throw Exception(
          'Failed to create vouch: ${response.statusCode} ${response.body}',
        );
      }
    } catch (e) {
      throw Exception('Error creating vouch: $e');
    }
  }

  /// Update vouch via full CRUD endpoint
  Future<Map<String, dynamic>> updateVouch(
    String vouchId,
    Map<String, dynamic> updates,
  ) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/api/vouches/$vouchId'),
        headers: await _authenticatedJsonHeaders(),
        body: json.encode(updates),
      );
      if (response.statusCode == 200) {
        return Map<String, dynamic>.from(json.decode(response.body) as Map);
      } else {
        throw Exception(
          'Failed to update vouch: ${response.statusCode} ${response.body}',
        );
      }
    } catch (e) {
      throw Exception('Error updating vouch: $e');
    }
  }

  /// Delete vouch via full CRUD endpoint
  Future<Map<String, dynamic>> deleteVouch(String vouchId) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/api/vouches/$vouchId'),
        headers: await _authenticatedJsonHeaders(),
      );
      if (response.statusCode == 200 || response.statusCode == 204) {
        if (response.body.isEmpty) return {};
        return Map<String, dynamic>.from(json.decode(response.body) as Map);
      } else {
        throw Exception(
          'Failed to delete vouch: ${response.statusCode} ${response.body}',
        );
      }
    } catch (e) {
      throw Exception('Error deleting vouch: $e');
    }
  }

  /// Health check
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // ============================================================================
  // Provider CRUD Operations (Authenticated)
  // ============================================================================

  /// Get list of providers
  Future<List<Provider>> getProviders({String? category}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/providers').replace(
        queryParameters: category != null ? {'category': category} : null,
      );

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => Provider.fromJson(json)).toList();
      } else {
        throw Exception('Failed to get providers: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting providers: $e');
    }
  }

  /// Get provider details
  Future<Provider> getProviderDetails(String providerId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/providers/$providerId'),
      );

      if (response.statusCode == 200) {
        return Provider.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to get provider: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting provider: $e');
    }
  }

  /// Create provider (requires authentication)
  Future<Provider> createProvider({
    required String name,
    required String category,
    String? description,
    String? phone,
    List<String>? services,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.post(
        Uri.parse('$baseUrl/api/providers'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode({
          'name': name,
          'category': category,
          'description': description,
          'phone': phone,
          'services': services ?? [],
        }),
      );

      if (response.statusCode == 201) {
        return Provider.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to create provider: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error creating provider: $e');
    }
  }

  /// Update provider (requires authentication)
  Future<Provider> updateProvider({
    required String providerId,
    String? name,
    String? category,
    String? description,
    String? phone,
    List<String>? services,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final updates = <String, dynamic>{};
      if (name != null) updates['name'] = name;
      if (category != null) updates['category'] = category;
      if (description != null) updates['description'] = description;
      if (phone != null) updates['phone'] = phone;
      if (services != null) updates['services'] = services;

      final response = await http.put(
        Uri.parse('$baseUrl/api/providers/$providerId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(updates),
      );

      if (response.statusCode == 200) {
        return Provider.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to update provider: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error updating provider: $e');
    }
  }

  /// Delete provider (requires authentication)
  Future<void> deleteProvider(String providerId) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.delete(
        Uri.parse('$baseUrl/api/providers/$providerId'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to delete provider: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error deleting provider: $e');
    }
  }

  // ============================================================================
  // Review CRUD Operations (Authenticated)
  // ============================================================================

  /// Get reviews for a provider
  Future<List<Map<String, dynamic>>> getProviderReviews(
    String providerId,
  ) async {
    try {
      final uri = Uri.parse('$baseUrl/api/reviews')
          .replace(queryParameters: {'provider_id': providerId});

      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get reviews: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting reviews: $e');
    }
  }

  /// Create review (requires authentication)
  Future<Map<String, dynamic>> createReview({
    required String providerId,
    required int rating,
    required String comment,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.post(
        Uri.parse('$baseUrl/api/reviews'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode({
          'provider_id': providerId,
          'rating': rating,
          'comment': comment,
        }),
      );

      if (response.statusCode == 201) {
        return json.decode(response.body);
      } else {
        final error = json.decode(response.body);
        throw Exception(error['detail'] ?? 'Failed to create review');
      }
    } catch (e) {
      throw Exception('Error creating review: $e');
    }
  }

  /// Update review (requires authentication)
  Future<Map<String, dynamic>> updateReview({
    required String reviewId,
    int? rating,
    String? comment,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final updates = <String, dynamic>{};
      if (rating != null) updates['rating'] = rating;
      if (comment != null) updates['comment'] = comment;

      final response = await http.put(
        Uri.parse('$baseUrl/api/reviews/$reviewId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(updates),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to update review: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error updating review: $e');
    }
  }

  /// Delete review (requires authentication)
  Future<void> deleteReview(String reviewId) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.delete(
        Uri.parse('$baseUrl/api/reviews/$reviewId'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to delete review: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error deleting review: $e');
    }
  }

  /// Get user's reviews
  Future<List<Map<String, dynamic>>> getMyReviews() async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final response = await http.get(
        Uri.parse('$baseUrl/api/reviews'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get reviews: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting reviews: $e');
    }
  }

  // ============================================================================
  // User Profile Operations (Authenticated)
  // ============================================================================

  /// Get user profile
  Future<User> getUserProfile(String userId) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/users/$userId'));

      if (response.statusCode == 200) {
        return User.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to get user profile: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting user profile: $e');
    }
  }

  /// Update user profile (requires authentication)
  Future<User> updateUserProfile({
    required String userId,
    String? name,
    String? phone,
    String? avatarUrl,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) {
        throw Exception('Not authenticated');
      }

      final updates = <String, dynamic>{};
      if (name != null) updates['name'] = name;
      if (phone != null) updates['phone'] = phone;
      if (avatarUrl != null) updates['avatar_url'] = avatarUrl;

      final response = await http.put(
        Uri.parse('$baseUrl/api/users/$userId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(updates),
      );

      if (response.statusCode == 200) {
        return User.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to update profile: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error updating profile: $e');
    }
  }
}
