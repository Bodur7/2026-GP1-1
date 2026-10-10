import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../models/scan_result.dart';

class AllergenScannerService {
  String baseUrl;
  final http.Client _client;
//10.0.2.2 is for android emulator only
  AllergenScannerService({String? baseUrl, http.Client? client})
      : baseUrl = baseUrl ?? 'http://192.168.1.85:8000',
        _client = client ?? http.Client();


  Future<ScanResult> scanImageBytes( //Future<ScanResult> means it eventually returns a ScanResult
    Uint8List imageBytes, {//contains the image as bytes rather than as a file path
    required List<String> userAllergens,
  }) async {
    final uri = Uri.parse('$baseUrl/scan/image');
    final request = http.MultipartRequest('POST', uri);

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: 'label.jpg',
        contentType: MediaType('image', 'jpeg'),
      ),
    );

    request.fields['user_allergens'] = jsonEncode(userAllergens);//sending user allergies as json

    final streamedResponse = await _client.send(request); 
    final response = await http.Response.fromStream(streamedResponse); 

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return compute(parseScanResult, response.body);//compute here helps with UI smoothness  
    } else {
      throw HttpException('Server error (${response.statusCode})', uri: uri);
    }
  }

  void dispose() => _client.close();
}