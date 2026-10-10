import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_colors.dart';
import '../widgets/app_header.dart';
import '../services/allergen_scanner_service.dart';
import 'scanning_screen.dart';
import 'image_capture_screen.dart';

enum ErrorType { labelUnreadable, connectionError }

class ErrorScreen extends StatelessWidget {
  final ErrorType type;
  final Uint8List imageBytes;
  final List<String> userAllergens;
  final AllergenScannerService scannerService;

  static const MethodChannel _channel =
      MethodChannel('com.example.misbar/image_capture');

  const ErrorScreen({
    super.key,
    required this.type,
    required this.imageBytes,
    required this.userAllergens,
    required this.scannerService,
  });

  Future<void> _handleRetry(BuildContext context) async {
    if (type == ErrorType.connectionError) {
      // Re-send the same in-memory image without retaking
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ScanningScreen(
            imageBytes: imageBytes,
            userAllergens: userAllergens,
            scannerService: scannerService,
          ),
        ),
      );
    } else {
      // Re-open camera to take a clearer picture
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
            userAllergens: userAllergens,
            scannerService: scannerService,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isUnreadable = type == ErrorType.labelUnreadable;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            AppHeader(onBack: () => Navigator.of(context).pop()),
            const Spacer(),

            // Centered Circular Icon Badge
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: isUnreadable ? AppColors.tagBeigeBg : AppColors.alertBg,
                shape: BoxShape.circle,
              ),
              child: Icon(
                isUnreadable ? Icons.local_offer_outlined : Icons.wifi_off,
                size: 36,
                color: isUnreadable ? AppColors.tagOrange : AppColors.alertSoftRed,
              ),
            ),
            const SizedBox(height: 24),

            // Title
            Text(
              isUnreadable ? 'Label Could Not Be Read' : 'Connection Error',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: AppColors.textDark,
              ),
            ),
            const SizedBox(height: 12),

            // Subtitle
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 40),
              child: Text(
                isUnreadable
                    ? 'Ensure even lighting, move closer to the text and keep your camera steady.'
                    : 'We could not complete the analysis. Check your connection and try again.',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.4,
                  color: AppColors.textMuted,
                ),
              ),
            ),
            const SizedBox(height: 32),

            // Primary Try Again Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: () => _handleRetry(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryGreen,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 0,
                  ),
                  child: const Text(
                    'Try Again',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Back to Home
            TextButton(
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

            const Spacer(),
          ],
        ),
      ),
    );
  }
}