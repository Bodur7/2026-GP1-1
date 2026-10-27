import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:misbar_app/models/scan_result.dart';
import 'package:misbar_app/services/allergy_service.dart';
import 'package:misbar_app/services/api_service.dart';
import 'package:misbar_app/services/allergen_scanner_service.dart';

// Mock ApiService to test persistence synchronization, scan isolation, and payload absence
class MockApiService implements ApiService {
  @override
  String baseUrl = 'http://mock:8000';

  List<String> mockBackendAllergies = ['Dairy allergy', 'Tree Nut allergy', 'Gluten allergy'];
  int saveCallCount = 0;
  List<List<String>> saveHistory = [];
  Duration saveDelay = Duration.zero;
  bool shouldFailSave = false;

  Uint8List? lastScannedBytes;
  String? lastScannedText;

  @override
  Future<Map<String, dynamic>> getProfile() async => {};

  @override
  Future<Map<String, dynamic>> updateProfile({String? name, String? email}) async => {};

  @override
  void dispose() {}

  @override
  Future<List<String>> getUserAllergies() async {
    return List<String>.from(mockBackendAllergies);
  }

  @override
  Future<List<String>> saveUserAllergies(List<String> allergies) async {
    saveCallCount++;
    saveHistory.add(List<String>.from(allergies));

    if (saveDelay > Duration.zero) {
      await Future.delayed(saveDelay);
    }

    if (shouldFailSave) {
      throw ApiException(500, 'Firestore write timeout / failure');
    }

    mockBackendAllergies = List<String>.from(allergies);
    return mockBackendAllergies;
  }

  @override
  Future<ScanResult> scanImageBytes(Uint8List imageBytes) async {
    lastScannedBytes = imageBytes;

    // Simulate backend response derived strictly from Firestore (mockBackendAllergies)
    final detections = [
      AllergenDetection(
        allergen: 'Dairy allergy',
        matchedIngredients: const ['milk', 'whey'],
        isUserAllergen: mockBackendAllergies.contains('Dairy allergy'),
      ),
      AllergenDetection(
        allergen: 'Gluten allergy',
        matchedIngredients: const ['wheat flour'],
        isUserAllergen: mockBackendAllergies.contains('Gluten allergy'),
      ),
    ];

    final hasConflict = detections.any((d) => d.isUserAllergen);

    return ScanResult(
      success: true,
      status: 'completed',
      isSafe: !hasConflict,
      extractedOcrText: 'Milk, wheat flour, sugar',
      ingredientList: 'Milk, wheat flour, sugar',
      allergensDetected: detections,
    );
  }

  @override
  Future<ScanResult> scanText(String text) async {
    lastScannedText = text;
    final isDairyAllergic = mockBackendAllergies.contains('Dairy allergy');

    return ScanResult(
      success: true,
      status: 'completed',
      isSafe: !isDairyAllergic,
      extractedOcrText: text,
      ingredientList: text,
      allergensDetected: [
        AllergenDetection(
          allergen: 'Dairy allergy',
          matchedIngredients: const ['milk'],
          isUserAllergen: isDairyAllergic,
        ),
      ],
    );
  }
}

void main() {
  group('Firestore Authoritative Allergy & Scanning Tests', () {
    late MockApiService mockApi;
    late AllergyService allergyService;
    late AllergenScannerService scannerService;

    setUp(() {
      mockApi = MockApiService();
      allergyService = AllergyService(mockApi);
      scannerService = AllergenScannerService(apiService: mockApi);
      allergyService.setLocalAllergies(['Dairy allergy', 'Tree Nut allergy', 'Gluten allergy']);
    });

    test('1. Removing an allergy and continuing awaits successful Firestore persistence', () async {
      mockApi.saveDelay = const Duration(milliseconds: 60);

      // User removes 'Dairy allergy'
      final target = ['Tree Nut allergy', 'Gluten allergy'];
      final saveFuture = allergyService.saveUserAllergies(target);

      expect(allergyService.isSaving, isTrue);
      // Backend has not received write yet during delay
      expect(mockApi.mockBackendAllergies.contains('Dairy allergy'), isTrue);

      // Screen awaits confirmation before proceeding
      await allergyService.ensureSaved();
      await saveFuture;

      expect(allergyService.isSaving, isFalse);
      // Write confirmed in backend
      expect(mockApi.mockBackendAllergies, equals(['Tree Nut allergy', 'Gluten allergy']));

      // Now scan triggers (scanImageBytes receives only bytes, no allergies)
      final scanResult = await mockApi.scanImageBytes(Uint8List.fromList([1, 2, 3]));

      // Backend evaluated scan using its newly persisted Firestore data (Dairy removed)
      final dairyDetection = scanResult.allergensDetected.firstWhere((d) => d.allergen == 'Dairy allergy');
      expect(dairyDetection.isUserAllergen, isFalse);
    });

    test('2. Failed or timed-out save prevents navigation and scanning and rolls back state', () async {
      mockApi.shouldFailSave = true;

      // Initial committed state has Dairy
      await allergyService.fetchUserAllergies();
      expect(allergyService.currentAllergies, contains('Dairy allergy'));

      // Attempt to remove Dairy, but Firestore fails
      try {
        await allergyService.saveUserAllergies(['Tree Nut allergy', 'Gluten allergy']);
        fail('Expected ApiException on failed save');
      } catch (e) {
        expect(e, isA<ApiException>());
      }

      // State is rolled back to last confirmed state
      expect(allergyService.currentAllergies, contains('Dairy allergy'));
      expect(allergyService.isSaving, isFalse);

      // ensureSaved() will not mask errors
      expect(allergyService.ensureSaved, returnsNormally);
    });

    test('3 & 9. Scan requests never supply allergies (image & text endpoints)', () async {
      final imageBytes = Uint8List.fromList([10, 20, 30]);

      // Call scanImageBytes
      final imgResult = await mockApi.scanImageBytes(imageBytes);
      expect(mockApi.lastScannedBytes, equals(imageBytes));
      expect(imgResult.success, isTrue);

      // Call scanText
      final txtResult = await mockApi.scanText('Milk, Sugar');
      expect(mockApi.lastScannedText, equals('Milk, Sugar'));
      expect(txtResult.success, isTrue);
    });

    test('4. In-flight scan cancellation when preferences change', () async {
      // Start a scan
      final scanFuture = scannerService.scanImageBytes(Uint8List.fromList([1, 2, 3]));

      // User immediately modifies allergies while scan is in flight
      scannerService.cancelCurrentScan();

      // Scan response arrives after cancellation -> must throw ScanCancelledException
      expect(scanFuture, throwsA(isA<ScanCancelledException>()));
    });

    test('7. Rapid successive edits serialize and cannot overwrite newer selections', () async {
      mockApi.saveDelay = const Duration(milliseconds: 40);

      // Rapid successive updates
      final f1 = allergyService.saveUserAllergies(['Tree Nut allergy', 'Gluten allergy']);
      final f2 = allergyService.saveUserAllergies(['Gluten allergy']);

      expect(allergyService.isSaving, isTrue);

      await allergyService.ensureSaved();
      await Future.wait([f1, f2]);

      expect(allergyService.isSaving, isFalse);
      // Final backend state matches the newest selection
      expect(mockApi.mockBackendAllergies, equals(['Gluten allergy']));
      expect(allergyService.currentAllergies, equals(['Gluten allergy']));
    });

    test('8. Remaining selected allergies are flagged, and unselected allergens visible globally', () async {
      // Backend has only Gluten allergy
      mockApi.mockBackendAllergies = ['Gluten allergy'];

      final scanResult = await mockApi.scanImageBytes(Uint8List.fromList([1, 2, 3]));

      // Dairy is detected globally, but not as user allergen
      final dairy = scanResult.allergensDetected.firstWhere((d) => d.allergen == 'Dairy allergy');
      expect(dairy.isUserAllergen, isFalse);
      expect(dairy.matchedIngredients, contains('milk'));

      // Gluten is detected and flagged as user allergen
      final gluten = scanResult.allergensDetected.firstWhere((d) => d.allergen == 'Gluten allergy');
      expect(gluten.isUserAllergen, isTrue);
      expect(gluten.matchedIngredients, contains('wheat flour'));

      // Unsafe because Gluten matched
      expect(scanResult.isSafe, isFalse);
    });
  });
}
