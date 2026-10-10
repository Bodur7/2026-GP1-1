import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../models/scan_result.dart';

/// Service for communicating with the FastAPI Allergen Scanner backend in "Label Scanning".
class AllergenScannerService {
  String baseUrl;
  final http.Client _client;

  AllergenScannerService({String? baseUrl, http.Client? client})
    : baseUrl = baseUrl ?? defaultBaseUrl,
      _client = client ?? http.Client();

  /// Default local server URL:
  /// - Physical device via adb reverse / iOS / Desktop: 127.0.0.1:8000
  /// - Android Emulator: 10.0.2.2:8000
  static String get defaultBaseUrl {
    return 'http://192.168.1.85:8000';
  }

  /// Sends image bytes directly from memory without saving to device storage.
  /// Automatically tries alternative endpoints (127.0.0.1, 10.0.2.2, LAN IP) if connection fails.
  Future<ScanResult> scanImageBytes(
    Uint8List imageBytes, {
    String filename = 'label.jpg',
    List<String>? userAllergens,
  }) async {
    try {
      return await _postScan(baseUrl, imageBytes, filename, userAllergens);
    } on SocketException {
      // Auto-fallback candidates for physical device vs emulator
      final alternatives = [
        'http://127.0.0.1:8000',
        'http://192.168.1.78:8000',
        'http://10.0.2.2:8000',
      ].where((url) => url != baseUrl).toList();

      for (final altUrl in alternatives) {
        try {
          final res = await _postScan(
            altUrl,
            imageBytes,
            filename,
            userAllergens,
          );
          baseUrl = altUrl; // Remember the functional URL
          return res;
        } catch (_) {}
      }
      rethrow;
    }
  }

  Future<ScanResult> _postScan(
    String targetUrl,
    Uint8List imageBytes,
    String filename,
    List<String>? userAllergens,
  ) async {
    final uri = Uri.parse('$targetUrl/scan/image');
    final request = http.MultipartRequest('POST', uri);

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: filename,
        contentType: MediaType('image', 'jpeg'),
      ),
    );

    if (userAllergens != null && userAllergens.isNotEmpty) {
      request.fields['user_allergens'] = jsonEncode(userAllergens);
    }

    final streamedResponse = await _client.send(request);
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return compute(parseScanResult, response.body);
    } else {
      String errorMessage = 'Server error (${response.statusCode})';
      try {
        final decoded = jsonDecode(response.body);
        if (decoded is Map && decoded.containsKey('detail')) {
          errorMessage = decoded['detail'].toString();
        }
      } catch (_) {}
      throw HttpException(errorMessage, uri: uri);
    }
  }

  /// Fetches the list of supported allergen categories from the server.
  Future<List<String>> fetchAllergens() async {
    final uri = Uri.parse('$baseUrl/allergens');
    final response = await _client.get(
      uri,
      headers: {HttpHeaders.acceptHeader: 'application/json'},
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final list =
          (data['categories'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [];
      return list;
    } else {
      throw HttpException(
        'Failed to load allergens (${response.statusCode})',
        uri: uri,
      );
    }
  }

  /// Checks if the backend server in "Label Scanning" is active.
  Future<bool> checkHealth() async {
    try {
      final uri = Uri.parse('$baseUrl/health');
      final response = await _client
          .get(uri)
          .timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  void dispose() {
    _client.close();
  }
}
