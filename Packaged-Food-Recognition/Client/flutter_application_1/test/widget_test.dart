import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:misbar_app/screens/welcome_screen.dart';

void main() {
  testWidgets('App loads initial welcome screen', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
    await tester.pumpAndSettle();

    expect(find.text('Log In'), findsOneWidget);
    expect(find.text('Create Account'), findsOneWidget);
  });
}
