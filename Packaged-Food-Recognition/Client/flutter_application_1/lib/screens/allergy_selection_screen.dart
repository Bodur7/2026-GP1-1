import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_colors.dart';
import '../widgets/app_header.dart';
import '../services/allergen_scanner_service.dart';
import '../services/allergy_service.dart';
import '../services/auth_service.dart';
import 'scanning_screen.dart';
import 'image_capture_screen.dart';
import 'welcome_screen.dart';

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
  final AllergyService _allergyService = AllergyService();
  final AuthService _authService = AuthService();

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

  final Set<String> _selectedAllergens = {
    'Dairy allergy',
    'Tree Nut allergy',
    'Gluten allergy',
    'Egg allergy',
  };

  bool _isLoadingAllergies = false;
  bool _isSavingAllergies = false;
  bool _isNavigatingToScanner = false;

  @override
  void initState() {
    super.initState();
    _scannerService = AllergenScannerService();
    if (_allergyService.currentAllergies != null) {
      _selectedAllergens.clear();
      _selectedAllergens.addAll(_allergyService.currentAllergies!);
    }
    _loadUserAllergiesFromFirestore();
  }

  Future<void> _loadUserAllergiesFromFirestore() async {
    final user = _authService.currentUser;
    if (user == null) return;

    setState(() => _isLoadingAllergies = true);
    try {
      final saved = await _allergyService.fetchUserAllergies(user.uid);
      if (saved != null && mounted) {
        setState(() {
          _selectedAllergens.clear();
          _selectedAllergens.addAll(saved);
        });
      }
    } catch (e) {
      debugPrint('[AllergySelectionScreen] Failed to load allergies: $e');
    } finally {
      if (mounted) {
        setState(() => _isLoadingAllergies = false);
      }
    }
  }

  Future<void> _toggleAllergen(String apiKey) async {
    // Invalidate/cancel any active or in-flight scan
    _scannerService.cancelCurrentScan();

    final willRemove = _selectedAllergens.contains(apiKey);
    setState(() {
      if (willRemove) {
        _selectedAllergens.remove(apiKey);
      } else {
        _selectedAllergens.add(apiKey);
      }
      _isSavingAllergies = true;
    });

    final user = _authService.currentUser;
    if (user != null) {
      try {
        await _allergyService.saveUserAllergies(
          user.uid,
          _selectedAllergens.toList(),
        );
      } catch (e) {
        debugPrint('[AllergySelectionScreen] Failed to persist allergy update: $e');
        if (mounted) {
          setState(() {
            _selectedAllergens.clear();
            _selectedAllergens.addAll(_allergyService.currentAllergies ?? []);
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to save allergy change ($e). Reverted.'),
              backgroundColor: AppColors.alertRed,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() => _isSavingAllergies = _allergyService.isSaving);
        }
      }
    } else {
      if (mounted) {
        setState(() => _isSavingAllergies = false);
      }
    }
  }

  Future<void> _handleSignOut() async {
    final shouldSignOut = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: const Text('Log Out', style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text('Are you sure you want to log out of Misbar?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted)),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.alertRed,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('Log Out'),
          ),
        ],
      ),
    );

    if (shouldSignOut == true) {
      await _authService.signOut();
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const WelcomeScreen()),
        (route) => false,
      );
    }
  }

  Future<void> _proceedToScanner() async {
    // Prevent concurrent/duplicate navigation attempts while saving or navigating
    if (_isNavigatingToScanner) return;
    _isNavigatingToScanner = true;

    // Ensure any in-flight or queued database save finishes and is confirmed by backend
    if (_isSavingAllergies || _allergyService.isSaving) {
      setState(() => _isSavingAllergies = true);
      try {
        await _allergyService.ensureSaved();
      } catch (e) {
        _isNavigatingToScanner = false;
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Cannot proceed to scanner: Failed to save allergies ($e). Please retry.'),
              backgroundColor: AppColors.alertRed,
              duration: const Duration(seconds: 4),
            ),
          );
        }
        return;
      } finally {
        if (mounted) {
          setState(() => _isSavingAllergies = _allergyService.isSaving);
        }
      }
    }

    final latestAllergens =
        _allergyService.currentAllergies ?? _selectedAllergens.toList();

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

          if (!mounted) {
            _isNavigatingToScanner = false;
            return;
          }

          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => ScanningScreen(
                imageBytes: bytes,
                userId: _authService.currentUser?.uid,
                userAllergens: latestAllergens,
                scannerService: _scannerService,
              ),
            ),
          ).then((_) {
            _isNavigatingToScanner = false;
          });
          return;
        }
      }
    } catch (_) {}

    if (!mounted) {
      _isNavigatingToScanner = false;
      return;
    }

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ImageCaptureScreen(
          userId: _authService.currentUser?.uid,
          userAllergens: latestAllergens,
          scannerService: _scannerService,
        ),
      ),
    ).then((_) {
      _isNavigatingToScanner = false;
    });
  }

  @override
  void dispose() {
    _scannerService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final user = _authService.currentUser;
    final displayName = user?.displayName ?? 'Friend';

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            // Header with Logout option & Misbar Logo
            AppHeader(
              showBack: false,
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  GestureDetector(
                    onTap: _handleSignOut,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: AppColors.chipUnselectedBg,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.logout_rounded,
                        size: 18,
                        color: AppColors.textMuted,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  SizedBox(
                    height: 42,
                    width: 95,
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: Image.asset(
                        'assets/images/misbar_logo.png',
                        fit: BoxFit.cover,
                        alignment: const Alignment(0.0, -0.05),
                        errorBuilder: (_, __, ___) => const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.search, color: AppColors.primaryGreen, size: 20),
                            SizedBox(width: 4),
                            Text(
                              'Misbar',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: AppColors.primaryGreen,
                                fontSize: 16,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Hello, $displayName 👋',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: AppColors.primaryGreen,
                      ),
                    ),
                    const SizedBox(height: 4),
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
                      "We'll warn you when these allergens are detected. Changes sync automatically to your account.",
                      style: TextStyle(fontSize: 14, color: AppColors.textMuted, height: 1.4),
                    ),
                    const SizedBox(height: 24),

                    // Allergy Chips Grid
                    if (_isLoadingAllergies)
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.symmetric(vertical: 24),
                          child: CircularProgressIndicator(color: AppColors.primaryGreen),
                        ),
                      )
                    else
                      Wrap(
                        spacing: 10,
                        runSpacing: 12,
                        children: _allergens.map((item) {
                          final isSelected =
                              _selectedAllergens.contains(item.apiKey);
                          return GestureDetector(
                            onTap: () => _toggleAllergen(item.apiKey),
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
                    'Continue to Scanner',
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
