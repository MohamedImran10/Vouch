import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  // Update this to your deployed backend URL in production
  static const String baseUrl = 'http://localhost:8001';

  /// Search for providers using BFS
  Future<List<SearchResult>> searchProviders({
    required String userId,
    required String category,
    int maxDegree = 2,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/api/search').replace(queryParameters: {
        'user_id': userId,
        'category': category,
        'max_degree': maxDegree.toString(),
      });

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
      final uri = Uri.parse('$baseUrl/api/trust-path').replace(queryParameters: {
        'from_id': fromId,
        'to_id': toId,
      });

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
        return categories.map((json) => ServiceCategory.fromJson(json)).toList();
      } else {
        throw Exception('Failed to get categories: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting categories: $e');
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
}
