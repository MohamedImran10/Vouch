// Models for Vouch Flutter App

class User {
  final String id;
  final String name;
  final String email;
  final String? avatar;

  User({
    required this.id,
    required this.name,
    required this.email,
    this.avatar,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      avatar: json['avatar'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'avatar': avatar,
    };
  }
}

class Provider {
  final String id;
  final String name;
  final String category;
  final double rating;
  final String? description;
  final String? phone;
  final String? avatar;

  Provider({
    required this.id,
    required this.name,
    required this.category,
    required this.rating,
    this.description,
    this.phone,
    this.avatar,
  });

  factory Provider.fromJson(Map<String, dynamic> json) {
    return Provider(
      id: json['provider_id'] as String,
      name: json['provider_name'] as String? ?? json['name'] as String? ?? 'Unknown',
      category: json['category'] as String,
      rating: (json['provider_rating'] ?? json['rating'] ?? 0.0).toDouble(),
      description: json['description'] as String?,
      phone: json['phone'] as String?,
      avatar: json['avatar'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'category': category,
      'rating': rating,
      'description': description,
      'phone': phone,
      'avatar': avatar,
    };
  }
}

class SearchResult {
  final String providerId;
  final String providerName;
  final int degree;
  final List<String> path;
  final String category;
  final double rating;

  SearchResult({
    required this.providerId,
    required this.providerName,
    required this.degree,
    required this.path,
    required this.category,
    required this.rating,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      providerId: json['provider_id'] as String,
      providerName: json['provider_name'] as String? ?? 'Unknown Provider',
      degree: json['degree'] as int,
      path: List<String>.from(json['path'] as List),
      category: json['category'] as String,
      rating: (json['provider_rating'] ?? 0.0).toDouble(),
    );
  }

  bool get isFirstDegree => degree == 1;
  bool get isSecondDegree => degree == 2;

  String get degreeLabel {
    if (degree == 1) return '1st Degree';
    if (degree == 2) return '2nd Degree';
    return '${degree}th Degree';
  }
}

class TrustPath {
  final List<String> path;
  final bool valid;
  final bool cycleDetected;

  TrustPath({
    required this.path,
    required this.valid,
    required this.cycleDetected,
  });

  factory TrustPath.fromJson(Map<String, dynamic> json) {
    return TrustPath(
      path: List<String>.from(json['path'] as List),
      valid: json['valid'] as bool,
      cycleDetected: json['cycle_detected'] as bool,
    );
  }

  String get displayPath => path.join(' ➔ ');
}

class VouchEdge {
  final String fromUser;
  final String toProvider;
  final String category;
  final String? timestamp;

  VouchEdge({
    required this.fromUser,
    required this.toProvider,
    required this.category,
    this.timestamp,
  });

  Map<String, dynamic> toJson() {
    return {
      'from_user': fromUser,
      'to_provider': toProvider,
      'category': category,
      'timestamp': timestamp,
    };
  }
}

class GraphNode {
  final String id;
  final String label;
  final NodeType type;

  GraphNode({
    required this.id,
    required this.label,
    required this.type,
  });
}

enum NodeType {
  user,
  friend,
  provider,
}

class GraphEdge {
  final String from;
  final String to;
  final String category;

  GraphEdge({
    required this.from,
    required this.to,
    required this.category,
  });
}

class ServiceCategory {
  final String id;
  final String name;
  final String icon;

  ServiceCategory({
    required this.id,
    required this.name,
    required this.icon,
  });

  factory ServiceCategory.fromJson(Map<String, dynamic> json) {
    return ServiceCategory(
      id: json['id'] as String,
      name: json['name'] as String,
      icon: json['icon'] as String,
    );
  }
}

class ChatMessage {
  final String id;
  final String senderId;
  final String receiverId;
  final String message;
  final DateTime timestamp;
  final bool isRead;

  ChatMessage({
    required this.id,
    required this.senderId,
    required this.receiverId,
    required this.message,
    required this.timestamp,
    this.isRead = false,
  });

  factory ChatMessage.fromFirestore(Map<String, dynamic> data) {
    return ChatMessage(
      id: data['id'] as String,
      senderId: data['sender_id'] as String,
      receiverId: data['receiver_id'] as String,
      message: data['message'] as String,
      timestamp: DateTime.parse(data['timestamp'] as String),
      isRead: data['is_read'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'id': id,
      'sender_id': senderId,
      'receiver_id': receiverId,
      'message': message,
      'timestamp': timestamp.toIso8601String(),
      'is_read': isRead,
    };
  }
}
