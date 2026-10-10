import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'models/scan_result.dart';

/// Service for communicating with the FastAPI Allergen Scanner backend.
class AllergenScannerService {
  final String baseUrl;
  final http.Client _client;

  AllergenScannerService({
    String? baseUrl,
    http.Client? client,
  })  : baseUrl = baseUrl ?? defaultBaseUrl,
        _client = client ?? http.Client();

  /// Automatically picks the correct localhost URL based on target platform:
  /// - Android Emulator: 10.0.2.2 points to host machine
  /// - iOS Simulator / macOS / Web: 127.0.0.1 points to host machine
  /// For physical devices on Wi-Fi, pass your computer's local IP (e.g. http://192.168.1.100:8000).
  static String get defaultBaseUrl {
    if (!kIsWeb && Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  /// Uploads an image of a food package label to the FastAPI server.
  /// 
  /// The server:
  /// 1. Extracts OCR text using Google Cloud Vision / EasyOCR.
  /// 2. Isolates the ingredient list using the Open Food Facts AI model.
  /// 3. Cross-references against the allergen dataset and returns structured results.
  Future<ScanResult> scanImage(
    File imageFile, {
    List<String>? userAllergens,
  }) async {
    final uri = Uri.parse('$baseUrl/scan/image');
    final request = http.MultipartRequest('POST', uri);

    // Attach image file
    final multipartFile = await http.MultipartFile.fromPath(
      'file',
      imageFile.path,
    );
    request.files.add(multipartFile);

    // Optional user allergen profile (passed as comma-separated or JSON)
    if (userAllergens != null && userAllergens.isNotEmpty) {
      request.fields['user_allergens'] = jsonEncode(userAllergens);
    }

    final streamedResponse = await _client.send(request);
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      // Offload JSON decoding to a background isolate to prevent UI frame drops
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

  /// Sends raw packaging text to the FastAPI backend for analysis.
  /// Ideal if your Flutter app performs on-device OCR using Google ML Kit.
  Future<ScanResult> scanText(
    String rawText, {
    List<String>? userAllergens,
  }) async {
    final uri = Uri.parse('$baseUrl/scan/text');
    final response = await _client.post(
      uri,
      headers: {
        HttpHeaders.contentTypeHeader: 'application/json; charset=UTF-8',
        HttpHeaders.acceptHeader: 'application/json',
      },
      body: jsonEncode({
        'text': rawText,
        if (userAllergens != null) 'user_allergens': userAllergens,
      }),
    );

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

  /// Fetches the list of all available allergen categories from the server.
  Future<List<String>> fetchAllergens() async {
    final uri = Uri.parse('$baseUrl/allergens');
    final response = await _client.get(
      uri,
      headers: {HttpHeaders.acceptHeader: 'application/json'},
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final list = (data['categories'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [];
      return list;
    } else {
      throw HttpException('Failed to load allergens (${response.statusCode})', uri: uri);
    }
  }

  /// Verifies connectivity to the FastAPI server.
  Future<bool> checkHealth() async {
    try {
      final uri = Uri.parse('$baseUrl/health');
      final response = await _client.get(uri).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  void dispose() {
    _client.close();
  }
}
