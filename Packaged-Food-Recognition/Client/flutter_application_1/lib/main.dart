import 'package:flutter/material.dart';
import 'theme/app_colors.dart';
import 'screens/allergy_selection_screen.dart';

void main() {
  runApp(const MisbarApp());
}

class MisbarApp extends StatelessWidget {
  const MisbarApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Misbar',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Roboto',
        scaffoldBackgroundColor: AppColors.background,
        colorScheme: ColorScheme.fromSeed(seedColor: AppColors.primaryGreen),
        useMaterial3: true,
      ),
      home: const AllergySelectionScreen(),
    );
  }
}


