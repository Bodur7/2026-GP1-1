import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/scan_result.dart';
import 'api_service.dart';

class ScanCancelledException implements Exception {
  final String message;
  ScanCancelledException([this.message = 'Scan was cancelled because newer preferences were applied.']);
  @override
  String toString() => message;
}

/// AllergenScannerService manages image and text scanning.
/// All user allergy preferences are retrieved strictly from Firestore by the backend.
/// Tracks active scan generations to cancel/discard obsolete in-flight scans.
class AllergenScannerService {
  final ApiService _apiService;
  int _activeScanId = 0;

  String get baseUrl => _apiService.baseUrl;
  set baseUrl(String url) => _apiService.baseUrl = url;

  AllergenScannerService({String? baseUrl, http.Client? client, ApiService? apiService})
      : _apiService = apiService ?? ApiService() {
    if (baseUrl != null) {
      _apiService.baseUrl = baseUrl;
    }
  }

  /// Invalidate/cancel any in-flight scan requests so their responses are discarded.
  void cancelCurrentScan() {
    _activeScanId++;
  }

  Future<ScanResult> scanImageBytes(
    Uint8List imageBytes, {
    String? userId,
    String? authToken,
  }) async {
    final currentId = ++_activeScanId;
    final result = await _apiService.scanImageBytes(imageBytes);
    if (currentId != _activeScanId) {
      throw ScanCancelledException();
    }
    return result;
  }

  Future<ScanResult> scanText(String text) async {
    final currentId = ++_activeScanId;
    final result = await _apiService.scanText(text);
    if (currentId != _activeScanId) {
      throw ScanCancelledException();
    }
    return result;
  }

  void dispose() => _apiService.dispose();
}
