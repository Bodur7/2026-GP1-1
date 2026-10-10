import 'package:flutter_test/flutter_test.dart';
import 'package:misbar/main.dart';

void main() {
  testWidgets('Allergen scanner smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MisbarApp());

    // Verify that the title and allergy profile render.
    expect(find.text('Misbar Allergen Scanner'), findsOneWidget);
    expect(find.text('Your Allergy Profile:'), findsOneWidget);
  });
}
