import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'models/scan_result.dart';
import 'services/allergen_scanner_service.dart';

void main() {
  runApp(const MisbarApp());
}

class MisbarApp extends StatelessWidget {
  const MisbarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Misbar - Allergen Scanner',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00796B),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF80CBC4),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const AllergenScannerHomeScreen(),
    );
  }
}

class AllergenScannerHomeScreen extends StatefulWidget {
  const AllergenScannerHomeScreen({super.key});

  @override
  State<AllergenScannerHomeScreen> createState() =>
      _AllergenScannerHomeScreenState();
}

class _AllergenScannerHomeScreenState extends State<AllergenScannerHomeScreen> {
  static const MethodChannel _channel =
      MethodChannel('com.example.misbar/image_capture');

  late final AllergenScannerService _scannerService;
  Uint8List? _inMemoryImageBytes;
  bool _isAnalyzing = false;
  String? _errorMessage;
  ScanResult? _scanResult;

  // Selected personal allergy preferences
  final List<String> _userAllergies = [
    'Dairy allergy',
    'Wheat allergy',
    'Soy allergy',
    'Peanut allergy',
  ];
  final List<String> _availableAllergens = [
    'Dairy allergy',
    'Wheat allergy',
    'Soy allergy',
    'Peanut allergy',
    'Tree Nut allergy',
    'Egg allergy',
    'Fish allergy',
    'Shellfish allergy',
    'Sesame allergy',
    'Mustard allergy',
    'Celery allergy',
    'Lupin allergy',
    'Sulphites allergy',
    
  ];

  @override
  void initState() {
    super.initState();
    _scannerService = AllergenScannerService();

    // Automatically trigger the photo taking activity first thing on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _launchPhotoTakingActivity();
    });
  }

  /// Launches the native Android photo-taking activity.
  /// When confirmed, reads bytes to memory and immediately purges the local file so it is NEVER saved.
  Future<void> _launchPhotoTakingActivity() async {
    setState(() {
      _errorMessage = null;
    });

    try {
      final String? tempFilePath =
          await _channel.invokeMethod<String>('openImageCapture');

      if (tempFilePath != null && tempFilePath.isNotEmpty) {
        final tempFile = File(tempFilePath);
        Uint8List? bytes;

        if (await tempFile.exists()) {
          // Read image directly into volatile memory
          bytes = await tempFile.readAsBytes();

          // Immediately delete the file from device storage so it won't be saved
          try {
            await tempFile.delete();
          } catch (_) {
            // Silently ignore deletion error if OS locked
          }
        }

        if (bytes != null && mounted) {
          setState(() {
            _inMemoryImageBytes = bytes;
            _scanResult = null;
          });

          // Send the in-memory image to the Label Scanning server
          await _sendImageToServer(bytes);
        }
      }
    } on PlatformException catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage =
              'Failed to launch camera/gallery activity: ${e.message}';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Error processing photo: $e';
        });
      }
    }
  }

  /// Sends the image bytes directly to the Label Scanning FastAPI backend.
  Future<void> _sendImageToServer(Uint8List imageBytes) async {
    setState(() {
      _isAnalyzing = true;
      _errorMessage = null;
    });

    try {
      final result = await _scannerService.scanImageBytes(
        imageBytes,
        userAllergens: _userAllergies,
      );

      if (mounted) {
        setState(() {
          _scanResult = result;
          _isAnalyzing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isAnalyzing = false;
          _errorMessage =
              'Could not communicate with the Label Scanning server at ${_scannerService.baseUrl}.\n\n'
              'Details: $e\n\n'
              'Make sure the server is running in "Label Scanning":\n'
              'python3 -m uvicorn main:app --host 0.0.0.0 --port 8000';
        });
      }
    }
  }

  @override
  void dispose() {
    _scannerService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Misbar Allergen Scanner'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_ethernet),
            tooltip: 'Server Settings',
            onPressed: _showServerSettingsDialog,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // User Allergy Filter Section
              _buildAllergyFilterCard(theme),
              const SizedBox(height: 16),

              // Action Bar
              Row(
                children: [
                  Expanded(
                    child: FilledButton.icon(
                      onPressed:
                          _isAnalyzing ? null : _launchPhotoTakingActivity,
                      icon: const Icon(Icons.add_a_photo),
                      label: Text(_scanResult != null || _inMemoryImageBytes != null
                          ? 'Take / Pick Another'
                          : 'Open Camera / Gallery'),
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Volatile In-Memory Image Preview & Privacy Badge
              if (_inMemoryImageBytes != null) ...[
                Card(
                  elevation: 2,
                  clipBehavior: Clip.antiAlias,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      ConstrainedBox(
                        constraints: const BoxConstraints(
                          maxHeight: 240,
                          minHeight: 140,
                        ),
                        child: Image.memory(
                          _inMemoryImageBytes!,
                          fit: BoxFit.contain,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                        color: theme.colorScheme.surfaceContainerHighest,
                        child: Row(
                          children: [
                            Icon(
                              Icons.lock_outline,
                              size: 16,
                              color: theme.colorScheme.primary,
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                'Memory Only: Photo was NOT saved to device storage',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: theme.colorScheme.onSurfaceVariant,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Analyzing / Loading state
              if (_isAnalyzing) ...[
                Card(
                  elevation: 0,
                  color: theme.colorScheme.secondaryContainer.withValues(alpha: 0.4),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(
                      color: theme.colorScheme.secondary.withValues(alpha: 0.3),
                    ),
                  ),
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 28, horizontal: 20),
                    child: Column(
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text(
                          'Streaming image to Label Scanning server...',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 6),
                        Text(
                          'Extracting OCR text & matching allergens with AI',
                          style: TextStyle(fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Error Display
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.red.shade300),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.error_outline, color: Colors.red.shade700),
                          const SizedBox(width: 8),
                          Text(
                            'Server Error',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.red.shade900,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _errorMessage!,
                        style: TextStyle(
                          color: Colors.red.shade900,
                          fontSize: 13,
                        ),
                      ),
                      if (_inMemoryImageBytes != null) ...[
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: _isAnalyzing
                              ? null
                              : () =>
                                  _sendImageToServer(_inMemoryImageBytes!),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry Sending to Server'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.red.shade900,
                            side: BorderSide(color: Colors.red.shade400),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Scan Results Display
              if (_scanResult != null && !_isAnalyzing) ...[
                _buildResultsSection(_scanResult!, theme),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAllergyFilterCard(ThemeData theme) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.shield_outlined,
                    size: 20, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Your Allergy Profile:',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: _availableAllergens.map((allergen) {
                final isSelected = _userAllergies.contains(allergen);
                return FilterChip(
                  label: Text(allergen.replaceAll(' allergy', '')),
                  selected: isSelected,
                  onSelected: (selected) {
                    setState(() {
                      if (selected) {
                        _userAllergies.add(allergen);
                      } else {
                        _userAllergies.remove(allergen);
                      }
                    });
                    // Automatically re-evaluate with the new allergy profile if an image is loaded
                    if (_inMemoryImageBytes != null && !_isAnalyzing) {
                      _sendImageToServer(_inMemoryImageBytes!);
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContentErrorCard(ScanResult result, ThemeData theme) {
    final isNoText = result.isNoText;
    final title = result.errorTitle ??
        (isNoText
            ? 'No Text Detected / لم يتم العثور على نص'
            : 'No Ingredients Found / لم يتم العثور على قائمة المكونات');
    final message = result.message ??
        (isNoText
            ? 'The image does not contain readable text. Please ensure the product label is clear, well-lit, and in focus. / الصورة لا تحتوي على نص واضح. يرجى التأكد من وضوح الملصق وإضاءته الجيدة.'
            : 'Text was detected, but no food ingredients list was found. Please photograph the "Ingredients" ("المكونات") section. / تم العثور على نص ولكن لم يتم التعرف على قائمة مكونات غذائية. يرجى تصوير قسم "المكونات" على المنتج.');

    final icon = isNoText
        ? Icons.document_scanner_outlined
        : Icons.no_food_outlined;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.amber.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber.shade600, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.shade200.withValues(alpha: 0.4),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade100,
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: Colors.amber.shade900, size: 32),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF451A03),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      message,
                      style: TextStyle(
                        fontSize: 13,
                        height: 1.4,
                        color: Colors.grey.shade900,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _launchPhotoTakingActivity,
            icon: const Icon(Icons.camera_alt_outlined),
            label: const Text(
              'Retake Photo / إعادة التصوير',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            style: FilledButton.styleFrom(
              backgroundColor: Colors.amber.shade800,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsSection(ScanResult result, ThemeData theme) {
    // If the image had no text or no ingredients list, show dedicated warning card and hide accordions
    if (result.hasContentError) {
      return _buildContentErrorCard(result, theme);
    }

    final isSafe = result.isSafe;
    final statusColor = isSafe ? Colors.green : Colors.red;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Safety Status Banner
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isSafe ? Colors.green.shade50 : Colors.red.shade50,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: isSafe ? Colors.green.shade400 : Colors.red.shade400,
              width: 1.5,
            ),
          ),
          child: Row(
            children: [
              Icon(
                isSafe ? Icons.check_circle : Icons.warning_amber_rounded,
                color: statusColor,
                size: 40,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isSafe ? 'Safe for You' : '⚠️ Allergen Warning!',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: isSafe
                            ? Colors.green.shade900
                            : Colors.red.shade900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      isSafe
                          ? 'No matching allergens detected from your profile.'
                          : 'Found ${result.allergensDetected.length} allergen categories in the label.',
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey.shade800,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // Detected Allergens List
        if (result.allergensDetected.isNotEmpty) ...[
          Text(
            'Detected Allergens:',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          ...result.allergensDetected.map((item) {
            final isConflict = item.isUserAllergen;
            return Card(
              color: isConflict ? Colors.red.shade50 : Colors.orange.shade50,
              margin: const EdgeInsets.only(bottom: 8),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(
                  color:
                      isConflict ? Colors.red.shade300 : Colors.orange.shade300,
                ),
              ),
              child: ListTile(
                leading: Icon(
                  isConflict ? Icons.dangerous : Icons.warning,
                  color: isConflict ? Colors.red : Colors.orange.shade800,
                ),
                title: Text(
                  item.allergen,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color:
                        isConflict ? Colors.red.shade900 : Colors.orange.shade900,
                  ),
                ),
                subtitle: Text(
                  'Matched: ${item.matchedIngredients.join(', ')}',
                ),
                trailing: isConflict
                    ? Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Text(
                          'YOUR ALLERGY',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      )
                    : null,
              ),
            );
          }),
          const SizedBox(height: 8),
        ],

        // Extracted Ingredients
        ExpansionTile(
          title: const Text(
            'Extracted Ingredient List',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          subtitle: const Text('Identified by Open Food Facts model'),
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: theme.colorScheme.surfaceContainerHighest,
              child: Text(
                result.ingredientList.isNotEmpty
                    ? result.ingredientList
                    : 'No separate ingredient list detected.',
                style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              ),
            ),
          ],
        ),

        // Raw OCR text
        ExpansionTile(
          title: const Text(
            'Raw OCR Text',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          subtitle: Text('Engine: ${result.ocrEngine}'),
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: theme.colorScheme.surfaceContainerHighest,
              child: Text(
                result.extractedOcrText.isNotEmpty
                    ? result.extractedOcrText
                    : 'No text extracted.',
                style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
              ),
            ),
          ],
        ),
      ],
    );
  }

  void _showServerSettingsDialog() {
    final controller = TextEditingController(text: _scannerService.baseUrl);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Label Scanning Server URL'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Default Android Emulator URL: http://10.0.2.2:8000\n'
              'Default Localhost / iOS: http://127.0.0.1:8000',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'Backend URL',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              setState(() {
                _scannerService.baseUrl = controller.text.trim();
              });
              Navigator.of(ctx).pop();
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}
