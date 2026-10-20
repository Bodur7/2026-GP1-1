import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  User? get currentUser => _auth.currentUser;

  Stream<User?> get authStateChanges => _auth.authStateChanges();

  /// Creates a new user with email & password, sets display name,
  /// and initializes their user profile in Firestore
  Future<UserCredential> signUp({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final credential = await _auth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password,
      );

      final user = credential.user;
      if (user != null) {
        await user.updateDisplayName(name.trim());

        // Initialize user document in Firestore
        await _firestore.collection('users').doc(user.uid).set({
          'name': name.trim(),
          'email': email.trim(),
          'allergies': <String>[],
          'createdAt': FieldValue.serverTimestamp(),
          'updatedAt': FieldValue.serverTimestamp(),
        }, SetOptions(merge: true));
      }

      return credential;
    } catch (e) {
      debugPrint('AuthService.signUp error: $e');
      rethrow;
    }
  }

  /// Signs in an existing user with email and password
  Future<UserCredential> signIn({
    required String email,
    required String password,
  }) async {
    try {
      return await _auth.signInWithEmailAndPassword(
        email: email.trim(),
        password: password,
      );
    } catch (e) {
      debugPrint('AuthService.signIn error: $e');
      rethrow;
    }
  }

  /// Signs out the current user
  Future<void> signOut() async {
    try {
      await _auth.signOut();
    } catch (e) {
      debugPrint('AuthService.signOut error: $e');
      rethrow;
    }
  }
}
