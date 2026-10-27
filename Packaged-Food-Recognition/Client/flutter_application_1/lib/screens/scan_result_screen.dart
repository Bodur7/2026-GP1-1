import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_colors.dart';
import '../widgets/app_header.dart';
import '../models/scan_result.dart';
import '../services/allergen_scanner_service.dart';
import '../services/allergy_service.dart';
import 'scanning_screen.dart';
import 'image_capture_screen.dart';

class _IngredientBannerItem {
  final String ingredient;
  final String category;

  const _IngredientBannerItem({
    required this.ingredient,
    required this.category,
  });
}

class ScanResultScreen extends StatelessWidget {
  final ScanResult result;
  final Uint8List imageBytes;
  final List<String> userAllergens;
  final String? userId;
  final AllergenScannerService scannerService;

  static const MethodChannel _channel =
      MethodChannel('com.example.misbar/image_capture');

  const ScanResultScreen({
    super.key,
    required this.result,
    required this.imageBytes,
    required this.userAllergens,
    this.userId,
    required this.scannerService,
  });

  static const Map<String, String> _allergenCategoryMap = {
    'milk': 'Dairy',
    'dairy': 'Dairy',
    'tree nuts': 'Nuts',
    'tree nut': 'Nuts',
    'nuts': 'Nuts',
    'peanut': 'Peanuts',
    'peanuts': 'Peanuts',
    'cereals containing gluten': 'Gluten',
    'gluten': 'Gluten',
    'wheat': 'Gluten',
    'egg': 'Eggs',
    'eggs': 'Eggs',
    'soybean': 'Soy',
    'soy': 'Soy',
    'soya': 'Soy',
    'crustaceans': 'Shellfish',
    'molluscs': 'Shellfish',
    'shellfish': 'Shellfish',
    'fish': 'Fish',
    'sesame': 'Sesame',
    'mustard': 'Mustard',
    'celery': 'Celery',
    'lupin': 'Lupin',
    'sulphur dioxide and sulphites': 'Sulphites',
    'sulphites': 'Sulphites',
    'sulfites': 'Sulphites',
  };

  static String formatCategory(String allergen) {
    final cleaned = allergen
        .trim()
        .replaceAll(RegExp(r'\ballergy\b', caseSensitive: false), '')
        .trim()
        .toLowerCase();

    if (_allergenCategoryMap.containsKey(cleaned)) {
      return _allergenCategoryMap[cleaned]!;
    }

    if (cleaned.contains('gluten') || cleaned.contains('cereal')) {
      return 'Gluten';
    }
    if (cleaned.contains('sulph') || cleaned.contains('sulf')) {
      return 'Sulphites';
    }
    if (cleaned.contains('crustacean') || cleaned.contains('mollusc')) {
      return 'Shellfish';
    }
    if (cleaned.contains('tree nut')) {
      return 'Nuts';
    }
    if (cleaned.contains('milk') || cleaned.contains('dairy')) {
      return 'Dairy';
    }

    if (cleaned.isEmpty) return 'Allergen';

    return cleaned.split(' ').where((w) => w.isNotEmpty).map((word) {
      return word[0].toUpperCase() + word.substring(1).toLowerCase();
    }).join(' ');
  }

  static String capitalize(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return trimmed;
    return trimmed[0].toUpperCase() + trimmed.substring(1);
  }

  Future<void> _scanAnother(BuildContext context) async {
    final activeAllergens =
        AllergyService().currentAllergies ?? userAllergens;

    try {
      final String? tempPath =
          await _channel.invokeMethod<String>('openImageCapture');

      if (tempPath != null && tempPath.isNotEmpty) {
        final file = File(tempPath);
        if (await file.exists()) {
          final bytes = await file.readAsBytes();
          try {
            await file.delete();
          } catch (_) {}

          if (!context.mounted) return;
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
              builder: (_) => ScanningScreen(
                imageBytes: bytes,
                userId: userId,
                userAllergens: activeAllergens,
                scannerService: scannerService,
              ),
            ),
          );
          return;
        }
      }
    } catch (_) {}

    if (!context.mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => ImageCaptureScreen(
          userId: userId,
          userAllergens: activeAllergens,
          scannerService: scannerService,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final userAllergenDetections =
        result.allergensDetected.where((e) => e.isUserAllergen).toList();
    final hasUserAllergens = userAllergenDetections.isNotEmpty;
    final isSafe = result.isSafe || (!hasUserAllergens && result.allergensDetected.isEmpty);

    final categories = userAllergenDetections
        .map((e) => formatCategory(e.allergen))
        .where((name) => name.isNotEmpty)
        .toSet()
        .toList();

    final List<_IngredientBannerItem> bannerItems = [];
    for (final item in userAllergenDetections) {
      final cat = formatCategory(item.allergen);
      if (item.matchedIngredients.isNotEmpty) {
        for (final ing in item.matchedIngredients) {
          final parts = ing
              .split(',')
              .map((s) => s.trim())
              .where((s) => s.isNotEmpty);
          for (final part in parts) {
            bannerItems.add(_IngredientBannerItem(
              ingredient: part,
              category: cat,
            ));
          }
        }
      } else {
        bannerItems.add(_IngredientBannerItem(
          ingredient: cat,
          category: cat,
        ));
      }
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            AppHeader(onBack: () => Navigator.of(context).pop()),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Status Banner
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: isSafe ? AppColors.safeGreenBg : AppColors.alertBg,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            isSafe ? 'Safe for You!' : 'Allergens Detected!',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: isSafe
                                  ? AppColors.safeGreen
                                  : AppColors.alertSoftRed,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            isSafe
                                ? 'No matching allergens detected from your profile.'
                                : (categories.isNotEmpty
                                    ? 'Contains ${categories.join(', ')}'
                                    : (result.allergensDetected.isNotEmpty
                                        ? 'Contains ${result.allergensDetected.map((e) => formatCategory(e.allergen)).toSet().join(', ')}'
                                        : 'No matching allergens detected from your profile.')),
                            style: TextStyle(
                              fontSize: 13,
                              color: isSafe
                                  ? AppColors.safeGreen
                                  : AppColors.alertSoftRed,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Detected Ingredients Section
                    if (bannerItems.isNotEmpty) ...[
                      const Text(
                        'Detected Ingredients',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textDark,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ...bannerItems.map((item) {
                        final isDirectCategory = item.ingredient.trim().toLowerCase() ==
                            item.category.trim().toLowerCase();
                        return Container(
                          width: double.infinity,
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 12),
                          decoration: BoxDecoration(
                            color: AppColors.alertBg,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              Expanded(
                                child: Text(
                                  capitalize(item.ingredient),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                    color: AppColors.alertSoftRed,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.alertSoftRed.withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  isDirectCategory ? 'Allergen' : item.category,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 12,
                                    color: AppColors.alertSoftRed,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                      const SizedBox(height: 16),
                    ],

                    const SizedBox(height: 8),

                    // Disclaimer
                    const Center(
                      child: Text(
                        'Misbar may make mistakes or miss allergens',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.textMuted,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Primary Button: Scan another packed label
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: () => _scanAnother(context),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primaryGreen,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          elevation: 0,
                        ),
                        child: const Text(
                          'Scan another packed label',
                          style: TextStyle(
                              fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Secondary: Back to Home
                    Center(
                      child: TextButton(
                        onPressed: () =>
                            Navigator.of(context).popUntil((route) => route.isFirst),
                        child: const Text(
                          'Back to Home',
                          style: TextStyle(
                            color: AppColors.primaryGreen,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
