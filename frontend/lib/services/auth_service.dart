import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../models/auth_models.dart';

class AuthService {
  static const String _baseUrl = 'http://localhost:8001';
  static const String _tokenKey = 'jwt_token';
  static const String _userKey = 'user_data';

  final _storage = const FlutterSecureStorage();

  AuthUser? _currentUser;

  /// Get current cached user
  AuthUser? get currentUser => _currentUser;

  /// Check if user is authenticated
  Future<bool> isAuthenticated() async {
    try {
      final token = await _storage.read(key: _tokenKey);
      if (token == null) return false;

      final userData = await _storage.read(key: _userKey);
      if (userData == null) return false;

      final user = AuthUser.fromJson(jsonDecode(userData));

      // Check if token is expired
      if (user.isTokenExpired) {
        await logout();
        return false;
      }

      _currentUser = user;
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Get stored JWT token
  Future<String?> getJwtToken() async {
    try {
      final userData = await _storage.read(key: _userKey);
      if (userData == null) return null;

      final user = AuthUser.fromJson(jsonDecode(userData));

      // Check if token needs refresh
      if (user.isTokenExpiringSoon && !user.isTokenExpired) {
        await refreshToken();
        return _currentUser?.jwtToken;
      }

      return user.jwtToken;
    } catch (e) {
      return null;
    }
  }

  /// Register with email and password
  Future<AuthUser> register({
    required String email,
    required String password,
    required String name,
    String? phone,
  }) async {
    try {
      final request = RegisterRequest(
        email: email,
        password: password,
        name: name,
        phone: phone,
      );

      final response = await http.post(
        Uri.parse('$_baseUrl/api/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final user = AuthUser.fromJson(data);

        // Store token and user data
        await _storage.write(key: _tokenKey, value: user.jwtToken);
        await _storage.write(key: _userKey, value: jsonEncode(data));

        _currentUser = user;
        return user;
      } else {
        final error = jsonDecode(response.body);
        throw AuthError.fromResponse(error);
      }
    } catch (e) {
      if (e is AuthError) rethrow;
      throw AuthError('Registration failed: ${e.toString()}');
    }
  }

  /// Login with email and password
  Future<AuthUser> login({
    required String email,
    required String password,
  }) async {
    try {
      final request = LoginRequest(
        email: email,
        password: password,
      );

      final response = await http.post(
        Uri.parse('$_baseUrl/api/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final user = AuthUser.fromJson(data);

        // Store token and user data
        await _storage.write(key: _tokenKey, value: user.jwtToken);
        await _storage.write(key: _userKey, value: jsonEncode(data));

        _currentUser = user;
        return user;
      } else {
        final error = jsonDecode(response.body);
        throw AuthError.fromResponse(error);
      }
    } catch (e) {
      if (e is AuthError) rethrow;
      throw AuthError('Login failed: ${e.toString()}');
    }
  }

  /// Refresh JWT token
  Future<AuthUser> refreshToken() async {
    try {
      final token = await _storage.read(key: _tokenKey);
      if (token == null) {
        throw AuthError('No token found');
      }

      final response = await http.post(
        Uri.parse('$_baseUrl/api/auth/refresh'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final user = AuthUser.fromJson(data);

        // Update stored token and user data
        await _storage.write(key: _tokenKey, value: user.jwtToken);
        await _storage.write(key: _userKey, value: jsonEncode(data));

        _currentUser = user;
        return user;
      } else {
        throw AuthError('Token refresh failed');
      }
    } catch (e) {
      if (e is AuthError) rethrow;
      throw AuthError('Token refresh failed: ${e.toString()}');
    }
  }

  /// Logout
  Future<void> logout() async {
    try {
      final token = await _storage.read(key: _tokenKey);

      if (token != null) {
        // Notify backend (optional)
        await http.post(
          Uri.parse('$_baseUrl/api/auth/logout'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $token',
          },
        );
      }

      // Clear stored data
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _userKey);

      _currentUser = null;
    } catch (e) {
      // Always clear local data even if backend call fails
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _userKey);
      _currentUser = null;
    }
  }

  /// Get current user profile from backend
  Future<AuthUser> getCurrentUserProfile() async {
    try {
      final token = await getJwtToken();
      if (token == null) {
        throw AuthError('Not authenticated');
      }

      final response = await http.get(
        Uri.parse('$_baseUrl/api/auth/me'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        // Update current user with fresh data
        if (_currentUser != null) {
          _currentUser = _currentUser!.copyWith(
            name: data['name'],
            phone: data['phone'],
            avatarUrl: data['avatar_url'],
          );
        }
        return _currentUser!;
      } else {
        throw AuthError('Failed to get user profile');
      }
    } catch (e) {
      if (e is AuthError) rethrow;
      throw AuthError('Failed to get user profile: ${e.toString()}');
    }
  }

}
