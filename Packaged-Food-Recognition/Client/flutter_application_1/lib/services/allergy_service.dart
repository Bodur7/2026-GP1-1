import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';

class AllergyService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  CollectionReference get _usersCollection => _firestore.collection('users');

  /// Fetches the user's saved allergies from Firestore
  Future<List<String>> fetchUserAllergies(String userId) async {
    try {
      final doc = await _usersCollection.doc(userId).get();
      if (doc.exists && doc.data() != null) {
        final data = doc.data() as Map<String, dynamic>;
        final List<dynamic>? list = data['allergies'];
        if (list != null) {
          return List<String>.from(list);
        }
      }
    } catch (e) {
      debugPrint('AllergyService.fetchUserAllergies error: $e');
    }
    return [];
  }

  /// Saves or updates the user's selected allergies in Firestore
  Future<void> saveUserAllergies(String userId, List<String> allergies) async {
    try {
      await _usersCollection.doc(userId).set({
        'allergies': allergies,
        'updatedAt': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));
    } catch (e) {
      debugPrint('AllergyService.saveUserAllergies error: $e');
      rethrow;
    }
  }

  /// Real-time stream of the user's allergy preferences
  Stream<List<String>> streamUserAllergies(String userId) {
    return _usersCollection.doc(userId).snapshots().map((snapshot) {
      if (!snapshot.exists || snapshot.data() == null) return [];
      final data = snapshot.data() as Map<String, dynamic>;
      final List<dynamic>? list = data['allergies'];
      return list != null ? List<String>.from(list) : [];
    });
  }
}
