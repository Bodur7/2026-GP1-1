import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../theme/app_colors.dart';
import '../widgets/app_header.dart';
import '../services/allergen_scanner_service.dart';
import 'scan_result_screen.dart';
import 'error_screen.dart';

class ScanningScreen extends StatefulWidget {
  final Uint8List imageBytes;
  final List<String> userAllergens;
  final String? userId;
  final AllergenScannerService scannerService;

  const ScanningScreen({
    super.key,
    required this.imageBytes,
    required this.userAllergens,
    this.userId,
    required this.scannerService,
  });

  @override
  State<ScanningScreen> createState() => _ScanningScreenState();
}

class _ScanningScreenState extends State<ScanningScreen> {
  int _step = 1; // 1: Image received, 2: Extracting text, 3: Checking allergens
  bool _cancelled = false;

  @override
  void initState() {
    super.initState();
    _startScan();
  }

  Future<void> _startScan() async {
    // Animate through checklist stages
    Future.delayed(const Duration(milliseconds: 700), () {
      if (mounted && !_cancelled) setState(() => _step = 2);
    });
    Future.delayed(const Duration(milliseconds: 1400), () {
      if (mounted && !_cancelled) setState(() => _step = 3);
    });

    try {
      final user = FirebaseAuth.instance.currentUser;
      final uid = widget.userId ?? user?.uid;
      final token = await user?.getIdToken(true);

      final result = await widget.scannerService.scanImageBytes(
        widget.imageBytes,
        userId: uid,
        authToken: token,
        userAllergens: widget.userAllergens,
      );

      if (!mounted || _cancelled) return;

      if (result.hasContentError) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => ErrorScreen(
              type: ErrorType.labelUnreadable,
              imageBytes: widget.imageBytes,
              userId: widget.userId,
              userAllergens: widget.userAllergens,
              scannerService: widget.scannerService,
            ),
          ),
        );
      } else {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => ScanResultScreen(
              result: result,
              imageBytes: widget.imageBytes,
              userId: widget.userId,
              userAllergens: widget.userAllergens,
              scannerService: widget.scannerService,
            ),
          ),
        );
      }
    } catch (e, stack) {
      debugPrint('[ScanningScreen] Scan failed: $e\n$stack');
      if (!mounted || _cancelled) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ErrorScreen(
            type: ErrorType.connectionError,
            imageBytes: widget.imageBytes,
            userId: widget.userId,
            userAllergens: widget.userAllergens,
            scannerService: widget.scannerService,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            AppHeader(
              onBack: () {
                _cancelled = true;
                Navigator.of(context).pop();
              },
            ),
            const Spacer(),

            // Scanner Icon Circle
            Container(
              width: 80,
              height: 80,
              decoration: const BoxDecoration(
                color: AppColors.sageBg,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.crop_free,
                size: 38,
                color: AppColors.primaryGreen,
              ),
            ),
            const SizedBox(height: 24),

            const Text(
              'Reading the label...',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Detecting ingredients and checking your allergies',
              style: TextStyle(fontSize: 14, color: AppColors.textMuted),
            ),
            const SizedBox(height: 32),

            // Checklist Card
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 24),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
              decoration: BoxDecoration(
                color: AppColors.chipUnselectedBg,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildCheckItem(
                    label: 'Image received',
                    isDone: _step >= 1,
                    isActive: _step == 1,
                  ),
                  const SizedBox(height: 12),
                  _buildCheckItem(
                    label: 'Extracting text...',
                    isDone: _step >= 2,
                    isActive: _step == 2,
                  ),
                  const SizedBox(height: 12),
                  _buildCheckItem(
                    label: 'Checking allergens',
                    isDone: _step >= 3,
                    isActive: _step == 3,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 32),

            TextButton(
              onPressed: () {
                _cancelled = true;
                Navigator.of(context).pop();
              },
              child: const Text(
                'Cancel',
                style: TextStyle(
                  color: AppColors.textDark,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),

            const Spacer(),

            // Bottom Green Progress Bar
            Container(
              margin: const EdgeInsets.only(bottom: 24),
              width: 140,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.primaryGreen,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCheckItem({
    required String label,
    required bool isDone,
    required bool isActive,
  }) {
    return Row(
      children: [
        if (isDone)
          const Text('✓ ',
              style: TextStyle(
                  color: AppColors.primaryGreen, fontWeight: FontWeight.bold))
        else
          const SizedBox(width: 16),
        Text(
          label,
          style: TextStyle(
            fontSize: 14,
            fontWeight: isDone ? FontWeight.w600 : FontWeight.normal,
            color: isDone ? AppColors.textDark : AppColors.textMuted,
          ),
        ),
      ],
    );
  }
}