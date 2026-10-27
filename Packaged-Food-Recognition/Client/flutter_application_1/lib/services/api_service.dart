import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../models/scan_result.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  final Uri? uri;

  ApiException(this.statusCode, this.message, {this.uri});

  @override
  String toString() => 'ApiException ($statusCode): $message';
}

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  String baseUrl;
  final http.Client _client;

  static const List<String> candidateBaseUrls = [
    'http://0.0.0.0:8000 ',
    'http://127.0.0.1:8000', // Physical Android device over ADB reverse or desktop
    'http://192.168.68.100:8000', // Mac LAN IP
    'http://10.0.2.2:8000', // Android emulator loopback
  ];

  ApiService._internal({String? baseUrl, http.Client? client})
      : baseUrl = baseUrl ?? 'http://192.168.0.152:8000',
        _client = client ?? http.Client();

  /// Retrieves the current Firebase ID token, optionally forcing a refresh.
  Future<String> _getAuthToken({bool forceRefresh = false}) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw const SocketException('User is not authenticated. Please log in.');
    }
    final token = await user.getIdToken(forceRefresh);
    if (token == null || token.isEmpty) {
      throw const SocketException('Could not retrieve authentication token.');
    }
    return token;
  }

  /// Returns candidate host endpoints to attempt in order
  List<String> _getEndpoints() {
    return <String>[
      baseUrl,
      ...candidateBaseUrls.where((url) => url != baseUrl),
    ];
  }

  // ==========================================================================
  // User Profile Endpoints
  // ==========================================================================

  /// GET /users/me
  /// Fetches authenticated user profile and saved allergies from FastAPI.
  Future<Map<String, dynamic>> getProfile() async {
    return _sendWithRetry((host, token) async {
      final uri = Uri.parse('$host/users/me');
      final response = await _client.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        baseUrl = host;
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw ApiException(response.statusCode, response.body, uri: uri);
      }
    });
  }

  /// POST /users/profile
  /// Initializes or updates the user profile record on the server.
  Future<Map<String, dynamic>> updateProfile({
    String? name,
    String? email,
  }) async {
    return _sendWithRetry((host, token) async {
      final uri = Uri.parse('$host/users/profile');
      final response = await _client.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          if (name != null) 'name': name,
          if (email != null) 'email': email,
        }),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        baseUrl = host;
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw ApiException(response.statusCode, response.body, uri: uri);
      }
    });
  }

  // ==========================================================================
  // User Allergies Database Endpoints
  // ==========================================================================

  /// GET /users/me/allergies
  /// Fetches user's saved allergies from the database via FastAPI.
  Future<List<String>> getUserAllergies() async {
    return _sendWithRetry((host, token) async {
      final uri = Uri.parse('$host/users/me/allergies');
      final response = await _client.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        baseUrl = host;
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final rawList = data['allergies'] as List<dynamic>?;
        return rawList?.map((e) => e.toString()).toList() ?? <String>[];
      } else {
        throw ApiException(response.statusCode, response.body, uri: uri);
      }
    });
  }

  /// PUT /users/me/allergies
  /// Updates user's saved allergies in the database via FastAPI.
  Future<List<String>> saveUserAllergies(List<String> allergies) async {
    return _sendWithRetry((host, token) async {
      final uri = Uri.parse('$host/users/me/allergies');
      final response = await _client.put(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'allergies': allergies}),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        baseUrl = host;
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final rawList = data['allergies'] as List<dynamic>?;
        return rawList?.map((e) => e.toString()).toList() ?? allergies;
      } else {
        throw ApiException(response.statusCode, response.body, uri: uri);
      }
    });
  }

  // ==========================================================================
  // Scanner Endpoints
  // ==========================================================================

  /// POST /scan/image
  /// Uploads product label photo with Bearer token for server-side processing.
  /// Note: Never supplies user_allergens; the server reads user allergies directly from Firestore.
  Future<ScanResult> scanImageBytes(Uint8List imageBytes) async {
    return _sendWithRetry((host, token) async {
      final uri = Uri.parse('$host/scan/image');
      final request = http.MultipartRequest('POST', uri);

      request.headers['Authorization'] = 'Bearer $token';
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          imageBytes,
          filename: 'label.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      final streamedResponse = await _client.send(request).timeout(
            const Duration(seconds: 25),
          );
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        baseUrl = host;
        return await compute(parseScanResult, response.body);
      } else {
        throw ApiException(response.statusCode, response.body, uri: uri);
      }
    });
  }

  /// POST /scan/text
  /// Analyzes text with Bearer token for server-side processing.
  /// Note: Never supplies user_allergens; the server reads user allergies directly from Firestore.
  Future<ScanResult> scanText(String text) async {
    return _sendWithRetry((host, token) async {
      final uri = Uri.parse('$host/scan/text');
      final body = <String, dynamic>{
        'text': text,
      };
      final response = await _client.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        baseUrl = host;
        return await compute(parseScanResult, response.body);
      } else {
        throw ApiException(response.statusCode, response.body, uri: uri);
      }
    });
  }

  // ==========================================================================
  // Helper for Endpoint Failover and Token Refresh
  // ==========================================================================

  Future<T> _sendWithRetry<T>(
    Future<T> Function(String host, String token) executeRequest,
  ) async {
    String token = await _getAuthToken();
    Object? lastError;

    for (final host in _getEndpoints()) {
      try {
        return await executeRequest(host, token);
      } on ApiException catch (e) {
        if (e.statusCode == 401) {
          debugPrint('[ApiService] Received 401 Unauthorized from $host. Refreshing token...');
          try {
            token = await _getAuthToken(forceRefresh: true);
            return await executeRequest(host, token);
          } catch (refreshErr) {
            debugPrint('[ApiService] Token refresh failed: $refreshErr');
            rethrow;
          }
        }
        // Don't retry other hosts for non-network errors
        rethrow;
      } catch (e) {
        lastError = e;
        debugPrint('[ApiService] Failed request to $host: $e');
      }
    }

    throw lastError ??
        const SocketException('Could not connect to FastAPI backend.');
  }

  void dispose() => _client.close();
}
