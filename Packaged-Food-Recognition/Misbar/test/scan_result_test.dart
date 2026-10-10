import 'package:flutter_test/flutter_test.dart';
import 'package:misbar/models/scan_result.dart';

void main() {
  group('ScanResult Content Error Tests', () {
    test('Correctly identifies no_text status', () {
      final result = ScanResult.fromJson({
        'success': false,
        'status': 'no_text',
        'error_title': 'No Text Detected / لم يتم العثور على نص',
        'is_safe': false,
        'extracted_ocr_text': '',
        'ingredient_list': '',
        'allergens_detected': [],
        'total_allergens_count': 0,
        'ocr_engine': 'google_vision',
        'message': 'The image does not contain readable text.',
      });

      expect(result.isNoText, isTrue);
      expect(result.isNoIngredients, isFalse);
      expect(result.hasContentError, isTrue);
      expect(result.isSafe, isFalse);
      expect(result.errorTitle, contains('No Text Detected'));
    });

    test('Correctly identifies no_ingredients status', () {
      final result = ScanResult.fromJson({
        'success': false,
        'status': 'no_ingredients',
        'error_title': 'No Ingredients Found / لم يتم العثور على قائمة المكونات',
        'is_safe': false,
        'extracted_ocr_text': 'Welcome to Riyadh Metro Station 5',
        'ingredient_list': '',
        'allergens_detected': [],
        'total_allergens_count': 0,
        'ocr_engine': 'google_vision',
        'message': 'Text was detected, but no food ingredients list was found.',
      });

      expect(result.isNoText, isFalse);
      expect(result.isNoIngredients, isTrue);
      expect(result.hasContentError, isTrue);
      expect(result.isSafe, isFalse);
      expect(result.errorTitle, contains('No Ingredients Found'));
    });

    test('Correctly identifies completed scan', () {
      final result = ScanResult.fromJson({
        'success': true,
        'status': 'completed',
        'is_safe': true,
        'extracted_ocr_text': 'Ingredients: Water, Salt',
        'ingredient_list': 'Water, Salt',
        'allergens_detected': [],
        'total_allergens_count': 0,
        'ocr_engine': 'google_vision',
      });

      expect(result.isNoText, isFalse);
      expect(result.isNoIngredients, isFalse);
      expect(result.hasContentError, isFalse);
      expect(result.isSafe, isTrue);
    });
  });
}
