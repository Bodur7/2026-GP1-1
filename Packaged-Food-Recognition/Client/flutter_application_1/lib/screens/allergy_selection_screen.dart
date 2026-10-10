import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_colors.dart';
import '../widgets/app_header.dart';
import '../services/allergen_scanner_service.dart';
import 'scanning_screen.dart';
import 'image_capture_screen.dart';

class AllergySelectionScreen extends StatefulWidget {
  const AllergySelectionScreen({super.key});

  @override
  State<AllergySelectionScreen> createState() => _AllergySelectionScreenState();
}

class _AllergyItem {
  final String name;
  final String emoji;
  final String apiKey;
  const _AllergyItem(this.name, this.emoji, this.apiKey);
}

class _AllergySelectionScreenState extends State<AllergySelectionScreen> {
  static const MethodChannel _channel =
      MethodChannel('com.example.misbar/image_capture');
  late final AllergenScannerService _scannerService;

  final List<_AllergyItem> _allergens = const [
    _AllergyItem('Dairy', '🥛', 'Dairy allergy'),
    _AllergyItem('Nuts', '🥜', 'Tree Nut allergy'),
    _AllergyItem('Gluten', '🌾', 'Gluten allergy'),
    _AllergyItem('Shellfish', '🦀', 'Shellfish allergy'),
    _AllergyItem('Eggs', '🥚', 'Egg allergy'),
    _AllergyItem('Soy', '🫘', 'Soy allergy'),
    _AllergyItem('Wheat', '🌾', 'Wheat allergy'),
    _AllergyItem('Fish', '🐟', 'Fish allergy'),
    _AllergyItem('Sesame', '🌱', 'Sesame allergy'),
    _AllergyItem('Peanuts', '🥜', 'Peanut allergy'),
    _AllergyItem('Mustard', '🌼', 'Mustard allergy'),
    _AllergyItem('Celery', '🥬', 'Celery allergy'),
    _AllergyItem('Sulphites', '🍇', 'Sulphites allergy'),
    _AllergyItem('Lupin', '🌿', 'Lupin allergy'),
  ];

  late final Set<String> _selectedAllergens = {
    'Dairy allergy',
    'Tree Nut allergy',
    'Gluten allergy',
    'Egg allergy',
  };

  @override
  void initState() {
    super.initState();
    _scannerService = AllergenScannerService();
  }

  Future<void> _proceedToScanner() async {
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

          if (!mounted) return;

          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => ScanningScreen(
                imageBytes: bytes,
                userAllergens: _selectedAllergens.toList(),
                scannerService: _scannerService,
              ),
            ),
          );
          return;
        }
      }
    } catch (_) {}

    if (!mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ImageCaptureScreen(
          userAllergens: _selectedAllergens.toList(),
          scannerService: _scannerService,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _scannerService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            const AppHeader(showBack: false),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Select Your Allergies',
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      "We'll warn you when these allergens are detected",
                      style: TextStyle(fontSize: 14, color: AppColors.textMuted),
                    ),
                    const SizedBox(height: 24),

                    // Allergy Chips Grid
                    Wrap(
                      spacing: 10,
                      runSpacing: 12,
                      children: _allergens.map((item) {
                        final isSelected =
                            _selectedAllergens.contains(item.apiKey);
                        return GestureDetector(
                          onTap: () {
                            setState(() {
                              if (isSelected) {
                                _selectedAllergens.remove(item.apiKey);
                              } else {
                                _selectedAllergens.add(item.apiKey);
                              }
                            });
                          },
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 180),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 10),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? AppColors.primaryGreen
                                  : AppColors.chipUnselectedBg,
                              borderRadius: BorderRadius.circular(22),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(item.emoji,
                                    style: const TextStyle(fontSize: 16)),
                                const SizedBox(width: 8),
                                Text(
                                  item.name,
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                    color: isSelected
                                        ? Colors.white
                                        : AppColors.chipUnselectedText,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ),
              ),
            ),

            // Continue Button
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: _proceedToScanner,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryGreen,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 0,
                  ),
                  child: const Text(
                    'Continue',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
