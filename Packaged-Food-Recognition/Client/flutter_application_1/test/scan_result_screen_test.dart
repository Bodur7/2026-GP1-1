import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:misbar_app/models/scan_result.dart';
import 'package:misbar_app/screens/scan_result_screen.dart';
import 'package:misbar_app/services/allergen_scanner_service.dart';

void main() {
  group('ScanResultScreen Category & Ingredient Formatting', () {
    test('formatCategory maps backend dataset categories to user-friendly categories', () {
      expect(ScanResultScreen.formatCategory('Milk'), 'Dairy');
      expect(ScanResultScreen.formatCategory('dairy'), 'Dairy');
      expect(ScanResultScreen.formatCategory('Dairy allergy'), 'Dairy');
      expect(ScanResultScreen.formatCategory('Tree nuts'), 'Nuts');
      expect(ScanResultScreen.formatCategory('Tree Nut allergy'), 'Nuts');
      expect(ScanResultScreen.formatCategory('Cereals containing gluten'), 'Gluten');
      expect(ScanResultScreen.formatCategory('Gluten allergy'), 'Gluten');
      expect(ScanResultScreen.formatCategory('Soybean'), 'Soy');
      expect(ScanResultScreen.formatCategory('Soy allergy'), 'Soy');
      expect(ScanResultScreen.formatCategory('Egg'), 'Eggs');
      expect(ScanResultScreen.formatCategory('Egg allergy'), 'Eggs');
      expect(ScanResultScreen.formatCategory('Peanut'), 'Peanuts');
      expect(ScanResultScreen.formatCategory('Peanuts'), 'Peanuts');
      expect(ScanResultScreen.formatCategory('Crustaceans'), 'Shellfish');
      expect(ScanResultScreen.formatCategory('Molluscs'), 'Shellfish');
      expect(ScanResultScreen.formatCategory('Sulphur dioxide and sulphites'), 'Sulphites');
      expect(ScanResultScreen.formatCategory('Fish'), 'Fish');
      expect(ScanResultScreen.formatCategory('Sesame'), 'Sesame');
      expect(ScanResultScreen.formatCategory('Mustard'), 'Mustard');
      expect(ScanResultScreen.formatCategory('Celery'), 'Celery');
      expect(ScanResultScreen.formatCategory('Lupin'), 'Lupin');
    });

    test('capitalize handles lowercase strings and empty strings gracefully', () {
      expect(ScanResultScreen.capitalize('milk'), 'Milk');
      expect(ScanResultScreen.capitalize('whey powder'), 'Whey powder');
      expect(ScanResultScreen.capitalize(''), '');
      expect(ScanResultScreen.capitalize('  almonds  '), 'Almonds');
    });

    testWidgets('Renders detected ingredient and mapped category badge when allergy conflict exists', (WidgetTester tester) async {
      final result = ScanResult(
        success: true,
        isSafe: false,
        extractedOcrText: 'Ingredients: milk, whey, sugar',
        ingredientList: 'milk, whey, sugar',
        allergensDetected: const [
          AllergenDetection(
            allergen: 'Milk',
            matchedIngredients: ['milk', 'whey'],
            isUserAllergen: true,
          ),
        ],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ScanResultScreen(
            result: result,
            imageBytes: Uint8List(0),
            userAllergens: const ['Dairy allergy'],
            scannerService: AllergenScannerService(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Top banner shows Contains Dairy
      expect(find.text('Allergens Detected!'), findsOneWidget);
      expect(find.text('Contains Dairy'), findsOneWidget);

      // Section header
      expect(find.text('Detected Ingredients'), findsOneWidget);

      // Ingredients displayed with capitalized text
      expect(find.text('Milk'), findsOneWidget);
      expect(find.text('Whey'), findsOneWidget);

      // Category badge 'Dairy' is displayed (2 badges, one for each ingredient)
      expect(find.text('Dairy'), findsNWidgets(2));
    });

    testWidgets('Renders Safe for You when no user allergies match', (WidgetTester tester) async {
      final result = const ScanResult(
        success: true,
        isSafe: true,
        extractedOcrText: 'Ingredients: sugar, water',
        ingredientList: 'sugar, water',
        allergensDetected: [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ScanResultScreen(
            result: result,
            imageBytes: Uint8List(0),
            userAllergens: const ['Dairy allergy'],
            scannerService: AllergenScannerService(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Safe for You!'), findsOneWidget);
      expect(find.text('No matching allergens detected from your profile.'), findsOneWidget);
      expect(find.text('Detected Ingredients'), findsNothing);
    });

    test('ScanResult correctly flags low_quality as hasContentError', () {
      final json = {
        'success': false,
        'status': 'low_quality',
        'is_safe': false,
        'extracted_ocr_text': '',
        'ingredient_list': '',
        'allergens_detected': [],
        'total_allergens_count': 0,
        'error_title': 'Image Not Clear / الصورة غير واضحة',
        'message': 'Please retake the label photo in good lighting and keep the camera steady.'
      };

      final result = ScanResult.fromJson(json);
      expect(result.success, false);
      expect(result.status, 'low_quality');
      expect(result.isLowQuality, true);
      expect(result.hasContentError, true);
      expect(result.errorTitle, 'Image Not Clear / الصورة غير واضحة');
    });

    testWidgets('ScanResultScreen does not show Allergen Detected if allergensDetected is empty', (WidgetTester tester) async {
      // Even if a malformed result had isSafe: false with empty detections, it must not display false allergen warning
      final result = const ScanResult(
        success: false,
        isSafe: false,
        status: 'low_quality',
        extractedOcrText: '',
        ingredientList: '',
        allergensDetected: [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ScanResultScreen(
            result: result,
            imageBytes: Uint8List(0),
            userAllergens: const ['Dairy allergy'],
            scannerService: AllergenScannerService(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Allergens Detected!'), findsNothing);
      expect(find.text('Contains allergens matching your profile.'), findsNothing);
      expect(find.text('Safe for You!'), findsOneWidget);
    });
  });
}
