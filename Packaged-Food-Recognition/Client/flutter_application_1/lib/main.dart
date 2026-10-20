import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'theme/app_colors.dart';
import 'screens/welcome_screen.dart';
import 'screens/allergy_selection_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint('Firebase.initializeApp warning: $e');
  }
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
      home: const AuthGate(),
    );
  }
}

/// Listens to the Firebase Auth state:
/// - If signed in: navigates straight to AllergySelectionScreen
/// - If signed out: presents the WelcomeScreen with Login & Create Account options
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    try {
      return StreamBuilder<User?>(
        stream: FirebaseAuth.instance.authStateChanges(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Scaffold(
              backgroundColor: AppColors.background,
              body: Center(
                child: CircularProgressIndicator(color: AppColors.primaryGreen),
              ),
            );
          }

          if (snapshot.hasData && snapshot.data != null) {
            return const AllergySelectionScreen();
          }

          return const WelcomeScreen();
        },
      );
    } catch (_) {
      // Graceful fallback if Firebase is not yet initialized with google-services.json
      return const WelcomeScreen();
    }
  }
}
