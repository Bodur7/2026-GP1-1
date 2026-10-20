import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_colors.dart';
import '../widgets/app_header.dart';
import '../models/scan_result.dart';
import '../services/allergen_scanner_service.dart';
import 'scanning_screen.dart';
import 'image_capture_screen.dart';

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

  Future<void> _scanAnother(BuildContext context) async {
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
                userAllergens: userAllergens,
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
          userAllergens: userAllergens,
          scannerService: scannerService,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isSafe = result.isSafe;
    final conflictCount =
        result.allergensDetected.where((e) => e.isUserAllergen).length;

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
                                : '$conflictCount ingredients match your allergy profile.',
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
                    const Text(
                      'Detected Ingredients',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Ingredient Pills
                    ...result.allergensDetected.map((item) {
                      final isConflict = item.isUserAllergen;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 12),
                        decoration: BoxDecoration(
                          color: isConflict
                              ? AppColors.alertBg
                              : AppColors.chipUnselectedBg,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Text(
                              isConflict ? '! ' : '✓ ',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: isConflict
                                    ? AppColors.alertSoftRed
                                    : AppColors.primaryGreen,
                              ),
                            ),
                            Expanded(
                              child: Text(
                                '${item.matchedIngredients.join(', ')} (${item.allergen.replaceAll(' allergy', '')})',
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14,
                                  color: isConflict
                                      ? AppColors.alertSoftRed
                                      : AppColors.textDark,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                    const SizedBox(height: 16),

                    // Full Ingredient Text Card
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.sageBg,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Full Ingredient Text',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                              color: AppColors.darkGreen,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            result.ingredientList.isNotEmpty
                                ? result.ingredientList
                                : result.extractedOcrText,
                            style: const TextStyle(
                              fontSize: 13,
                              height: 1.5,
                              color: AppColors.darkGreen,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

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
