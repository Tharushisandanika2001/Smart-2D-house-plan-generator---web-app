import 'package:flutter_test/flutter_test.dart';
import 'package:house_plan_app/main.dart';
import 'package:flutter/material.dart';

void main() {
  testWidgets('App builds and shows title', (WidgetTester tester) async {
    // Pump MyApp (without const)
    await tester.pumpWidget(MyApp());

    // Allow animations/navigations to finish
    await tester.pumpAndSettle();

    // Check if title text is in the widget tree
    expect(find.text('Smart 2D House Plan Generator'), findsOneWidget);
  });
}
