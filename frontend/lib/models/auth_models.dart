// Authentication Models

/// Authenticated user with JWT token
class AuthUser {
  final String id;
  final String email;
  final String name;
  final String? phone;
  final String? avatarUrl;
  final String jwtToken;
  final DateTime expiresAt;
  final bool isAdmin;

  AuthUser({
    required this.id,
    required this.email,
    required this.name,
    this.phone,
    this.avatarUrl,
    required this.jwtToken,
    required this.expiresAt,
    this.isAdmin = false,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    final user = json['user'] as Map<String, dynamic>;
    final expiresIn = json['expires_in'] as int; // seconds

    return AuthUser(
      id: user['id'] as String,
      email: user['email'] as String,
      name: user['name'] as String,
      phone: user['phone'] as String?,
      avatarUrl: user['avatar_url'] as String?,
      jwtToken: json['access_token'] as String,
      expiresAt: DateTime.now().add(Duration(seconds: expiresIn)),
      isAdmin: user['is_admin'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'phone': phone,
      'avatar_url': avatarUrl,
      'jwt_token': jwtToken,
      'expires_at': expiresAt.toIso8601String(),
      'is_admin': isAdmin,
    };
  }

  bool get isTokenExpired {
    return DateTime.now().isAfter(expiresAt);
  }

  bool get isTokenExpiringSoon {
    // Check if token expires in less than 1 hour
    return expiresAt.difference(DateTime.now()).inHours < 1;
  }

  AuthUser copyWith({
    String? id,
    String? email,
    String? name,
    String? phone,
    String? avatarUrl,
    String? jwtToken,
    DateTime? expiresAt,
    bool? isAdmin,
  }) {
    return AuthUser(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      phone: phone ?? this.phone,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      jwtToken: jwtToken ?? this.jwtToken,
      expiresAt: expiresAt ?? this.expiresAt,
      isAdmin: isAdmin ?? this.isAdmin,
    );
  }
}

/// Login request
class LoginRequest {
  final String email;
  final String password;

  LoginRequest({
    required this.email,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'password': password,
    };
  }
}

/// Registration request
class RegisterRequest {
  final String email;
  final String password;
  final String name;
  final String? phone;

  RegisterRequest({
    required this.email,
    required this.password,
    required this.name,
    this.phone,
  });

  Map<String, dynamic> toJson() {
    return {
      'email': email,
      'password': password,
      'name': name,
      'phone': phone,
    };
  }
}

/// Auth error with user-friendly messages
class AuthError implements Exception {
  final String message;
  final String? code;

  AuthError(this.message, {this.code});

  factory AuthError.fromResponse(Map<String, dynamic> json) {
    return AuthError(
      json['detail'] as String? ?? 'An error occurred',
      code: json['error_code'] as String?,
    );
  }

  @override
  String toString() => message;
}
