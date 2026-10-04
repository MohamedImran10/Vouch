class AppConfig {
  static String get apiBaseUrl {
    // In production, this could come from environment variables or a config file
    // For now, using localhost for development
    return 'http://localhost:8001';
  }

  static String get imageBaseUrl {
    return '${apiBaseUrl}/images';
  }
}