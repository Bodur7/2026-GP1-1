import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../models/scan_result.dart';

class AllergenScannerService {
  String baseUrl;
  final http.Client _client;
  static const List<String> candidateBaseUrls = [
    'http://127.0.0.1:8000', // Physical Android device over ADB reverse or desktop
    'http://192.168.68.100:8000', // Mac LAN IP
    'http://192.168.1.85:8000', // Alternative router LAN IP
    'http://10.0.2.2:8000', // Android emulator loopback
  ];

  AllergenScannerService({String? baseUrl, http.Client? client})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8000',
        _client = client ?? http.Client();

  Future<ScanResult> scanImageBytes(
    Uint8List imageBytes, {
    String? userId,
    String? authToken,
    List<String>? userAllergens,
  }) async {
    // Endpoints to attempt: preferred baseUrl first, followed by fallbacks
    final endpoints = <String>[
      baseUrl,
      ...candidateBaseUrls.where((url) => url != baseUrl),
    ];

    Object? lastError;

    for (final host in endpoints) {
      try {
        final uri = Uri.parse('$host/scan/image');
        final request = http.MultipartRequest('POST', uri);

        request.files.add(
          http.MultipartFile.fromBytes(
            'file',
            imageBytes,
            filename: 'label.jpg',
            contentType: MediaType('image', 'jpeg'),
          ),
        );

        if (userId != null && userId.isNotEmpty) {
          request.fields['user_id'] = userId;
        }
        if (authToken != null && authToken.isNotEmpty) {
          request.fields['auth_token'] = authToken;
          request.headers['Authorization'] = 'Bearer $authToken';
        }
        if (userAllergens != null && userAllergens.isNotEmpty) {
          request.fields['user_allergens'] = jsonEncode(userAllergens);
        }

        final streamedResponse = await _client.send(request).timeout(
              const Duration(seconds: 15),
            );
        final response = await http.Response.fromStream(streamedResponse);

        if (response.statusCode >= 200 && response.statusCode < 300) {
          baseUrl = host; // Remember working endpoint for future scans
          return await compute(parseScanResult, response.body);
        } else {
          throw HttpException(
            'Server error (${response.statusCode}): ${response.body}',
            uri: uri,
          );
        }
      } catch (e) {
        lastError = e;
        debugPrint('[AllergenScannerService] Failed to connect to $host: $e');
        if (e is HttpException) {
          // If server actually responded with an error, do not retry other hosts
          rethrow;
        }
      }
    }

    throw lastError ??
        const SocketException('Could not connect to allergen scanner server.');
  }

  void dispose() => _client.close();
}