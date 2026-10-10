import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'allergen_scanner_service.dart';
import 'models/scan_result.dart';

class AllergenScannerScreen extends StatefulWidget {
  const AllergenScannerScreen({super.key});

  @override
  State<AllergenScannerScreen> createState() => _AllergenScannerScreenState();
}

class _AllergenScannerScreenState extends State<AllergenScannerScreen> {
  final AllergenScannerService _scannerService = AllergenScannerService();
  final ImagePicker _picker = ImagePicker();

  File? _selectedImage;
  bool _isLoading = false;
  String? _errorMessage;
  ScanResult? _scanResult;

  // Selected personal allergies
  final List<String> _userAllergies = [];
  List<String> _availableAllergens = []; // Populated from server via _loadAllergens()

  @override
  void initState() {
    super.initState();
    _loadAllergens();
  }

  Future<void> _loadAllergens() async {
    try {
      final list = await _scannerService.fetchAllergens();
      if (mounted && list.isNotEmpty) {
        setState(() => _availableAllergens = list);
      }
    } catch (_) {
      // Retain fallback list
    }
  }

  Future<void> _pickAndScanImage(ImageSource source) async {
    setState(() {
      _errorMessage = null;
    });

    try {
      final pickedFile = await _picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );

      if (pickedFile == null) return;

      final file = File(pickedFile.path);
      setState(() {
        _selectedImage = file;
        _isLoading = true;
        _scanResult = null;
      });

      // Call FastAPI backend
      final result = await _scannerService.scanImage(
        file,
        userAllergens: _userAllergies,
      );

      if (mounted) {
        setState(() {
          _scanResult = result;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Allergen Scanner'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // User Allergy Filter Section
            _buildAllergyFilterCard(),
            const SizedBox(height: 16),

            // Image Picker Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isLoading ? null : () => _pickAndScanImage(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Take Photo'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _isLoading ? null : () => _pickAndScanImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text('Pick Image'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Selected Image Preview
            if (_selectedImage != null) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.file(
                  _selectedImage!,
                  height: 200,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Loading Indicator
            if (_isLoading) ...[
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(32.0),
                  child: Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text(
                        'Analyzing label with Open Food Facts AI...',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                ),
              ),
            ],

            // Error Display
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade200),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: TextStyle(color: Colors.red.shade800),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Results Display
            if (_scanResult != null && !_isLoading) ...[
              _buildResultCard(_scanResult!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAllergyFilterCard() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Your Allergy Profile:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: _availableAllergens.map((allergen) {
                final isSelected = _userAllergies.contains(allergen);
                return FilterChip(
                  label: Text(allergen.replaceAll(' allergy', '')),
                  selected: isSelected,
                  selectedColor: Colors.teal.shade100,
                  checkmarkColor: Colors.teal.shade800,
                  onSelected: (selected) {
                    setState(() {
                      if (selected) {
                        _userAllergies.add(allergen);
                      } else {
                        _userAllergies.remove(allergen);
                      }
                    });
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard(ScanResult result) {
    if (result.status == 'no_text') {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.amber.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.amber.shade300),
        ),
        child: Row(
          children: [
            Icon(Icons.text_fields_outlined, color: Colors.amber.shade800, size: 36),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'No Text Detected',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.amber.shade900,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    result.message ?? 'No text could be detected in the image. Please make sure the label is clear, well-lit, and in focus.',
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade800),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    if (result.status == 'no_ingredients') {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.amber.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amber.shade300),
            ),
            child: Row(
              children: [
                Icon(Icons.search_off_rounded, color: Colors.amber.shade800, size: 36),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Please Scan an Ingredient List',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.amber.shade900,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        result.message ?? 'Text was detected, but no ingredient list could be identified. Please scan an ingredient list.',
                        style: TextStyle(fontSize: 13, color: Colors.grey.shade800),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          ExpansionTile(
            title: const Text(
              'Raw OCR Text Detected',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
            subtitle: Text('Engine: ${result.ocrEngine}'),
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                color: Colors.grey.shade100,
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

    final isSafe = result.isSafe;
    final color = isSafe ? Colors.green : Colors.red;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Safety Status Banner
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isSafe ? Colors.green.shade50 : Colors.red.shade50,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isSafe ? Colors.green.shade300 : Colors.red.shade300),
          ),
          child: Row(
            children: [
              Icon(
                isSafe ? Icons.check_circle : Icons.warning_amber_rounded,
                color: color,
                size: 36,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isSafe ? 'Safe for You' : '⚠️ Allergen Warning!',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: isSafe ? Colors.green.shade800 : Colors.red.shade800,
                      ),
                    ),
                    Text(
                      isSafe
                          ? 'No matching allergens found for your profile.'
                          : 'Found ${result.allergensDetected.length} allergen categories in ingredients.',
                      style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),


        // List of Detected Allergens
        if (result.allergensDetected.isNotEmpty) ...[
          const Text(
            'Detected Allergens:',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 8),
          ...result.allergensDetected.map((item) {
            final isConflict = item.isUserAllergen;
            return Card(
              color: isConflict ? Colors.red.shade50 : Colors.orange.shade50,
              margin: const EdgeInsets.only(bottom: 8),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(
                  color: isConflict ? Colors.red.shade300 : Colors.orange.shade300,
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
                    color: isConflict ? Colors.red.shade900 : Colors.orange.shade900,
                  ),
                ),
                subtitle: Text('Matched ingredients: ${item.matchedIngredients.join(', ')}'),
                trailing: isConflict
                    ? Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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

        // Extracted Ingredients Accordion (Open Food Facts Model)
        ExpansionTile(
          title: const Text(
            'Extracted Ingredient List (OFF AI)',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          subtitle: const Text('Isolated by Open Food Facts model'),
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: Colors.grey.shade100,
              child: Text(
                result.ingredientList.isNotEmpty
                    ? result.ingredientList
                    : 'No separate ingredient list detected.',
                style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              ),
            ),
          ],
        ),

        // Full OCR Text Accordion
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
              color: Colors.grey.shade100,
              child: Text(
                result.extractedOcrText,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
              ),
            ),
          ],
        ),
      ],
    );
  }

  @override
  void dispose() {
    _scannerService.dispose();
    super.dispose();
  }
}
