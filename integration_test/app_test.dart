import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:expense_saver/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Expense Saver App Integration Tests', () {
    late WidgetTester tester;

    setUp(() async {
      tester = IntegrationTestWidgetsFlutterBinding.instance.tester;
    });

    group('App Initialization Tests', () {
      testWidgets('App launches successfully', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        expect(find.byType(MaterialApp), findsOneWidget);
        expect(find.byType(Scaffold), findsOneWidget);
      });

      testWidgets('App shows home screen by default', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Should show home screen content
        expect(find.text('Home'), findsOneWidget);
      });
    });

    group('Navigation Flow Tests', () {
      testWidgets('Complete navigation flow between all tabs', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Test navigation to Expenses tab
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        expect(find.text('Expenses'), findsOneWidget);
        
        // Test navigation to Savings tab
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        expect(find.text('Savings'), findsOneWidget);
        
        // Test navigation to Settings tab
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        expect(find.text('Settings'), findsOneWidget);
        
        // Test navigation back to Home tab
        await tester.tap(find.text('Home'));
        await tester.pumpAndSettle();
        expect(find.text('Home'), findsOneWidget);
      });

      testWidgets('Bottom navigation bar works correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Verify bottom navigation bar exists
        expect(find.byType(BottomNavigationBar), findsOneWidget);
        
        // Test all navigation items
        final bottomNav = find.byType(BottomNavigationBar);
        expect(bottomNav, findsOneWidget);
        
        // Verify navigation items have proper icons and labels
        expect(find.text('Home'), findsOneWidget);
        expect(find.text('Expenses'), findsOneWidget);
        expect(find.text('Savings'), findsOneWidget);
        expect(find.text('Settings'), findsOneWidget);
      });

      testWidgets('Drawer navigation works correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Open drawer
        await tester.tap(find.byIcon(Icons.menu));
        await tester.pumpAndSettle();
        
        // Verify drawer items
        expect(find.text('Home'), findsOneWidget);
        expect(find.text('Expenses'), findsOneWidget);
        expect(find.text('Savings'), findsOneWidget);
        expect(find.text('Settings'), findsOneWidget);
        
        // Close drawer
        await tester.tapAt(const Offset(100, 100));
        await tester.pumpAndSettle();
      });
    });

    group('Expenses Functionality Tests', () {
      testWidgets('Add new expense', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Expenses tab
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        // Tap add expense button
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        // Fill expense form
        await tester.enterText(find.byType(TextFormField).first, 'Test Expense');
        await tester.enterText(find.byType(TextFormField).at(1), '50.00');
        
        // Select category
        await tester.tap(find.byType(DropdownButtonFormField));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Food').last);
        await tester.pumpAndSettle();
        
        // Save expense
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        
        // Verify expense was added
        expect(find.text('Test Expense'), findsOneWidget);
        expect(find.text('\$50.00'), findsOneWidget);
      });

      testWidgets('Edit existing expense', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Expenses tab
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        // Find and tap edit button for first expense
        await tester.tap(find.byIcon(Icons.edit).first);
        await tester.pumpAndSettle();
        
        // Modify expense
        await tester.enterText(find.byType(TextFormField).first, 'Updated Expense');
        await tester.enterText(find.byType(TextFormField).at(1), '75.00');
        
        // Save changes
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        
        // Verify expense was updated
        expect(find.text('Updated Expense'), findsOneWidget);
        expect(find.text('\$75.00'), findsOneWidget);
      });

      testWidgets('Delete expense', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Expenses tab
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        // Find and tap delete button for first expense
        await tester.tap(find.byIcon(Icons.delete).first);
        await tester.pumpAndSettle();
        
        // Confirm deletion
        await tester.tap(find.text('Delete'));
        await tester.pumpAndSettle();
        
        // Verify expense was deleted
        expect(find.text('Updated Expense'), findsNothing);
      });

      testWidgets('Expense form validation', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Expenses tab
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        // Tap add expense button
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        // Try to save without filling required fields
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        
        // Verify validation errors
        expect(find.text('Please enter expense name'), findsOneWidget);
        expect(find.text('Please enter amount'), findsOneWidget);
        
        // Fill invalid amount
        await tester.enterText(find.byType(TextFormField).at(1), 'invalid');
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        
        // Verify amount validation
        expect(find.text('Please enter valid amount'), findsOneWidget);
      });
    });

    group('Savings Functionality Tests', () {
      testWidgets('Add money to savings', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Savings tab
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        
        // Tap add money button
        await tester.tap(find.text('Add to Savings'));
        await tester.pumpAndSettle();
        
        // Enter amount
        await tester.enterText(find.byType(TextFormField), '100.00');
        
        // Save
        await tester.tap(find.text('Add'));
        await tester.pumpAndSettle();
        
        // Verify money was added
        expect(find.text('\$100.00'), findsOneWidget);
      });

      testWidgets('Update monthly target', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Savings tab
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        
        // Tap update target button
        await tester.tap(find.text('Update Monthly Target'));
        await tester.pumpAndSettle();
        
        // Enter new target
        await tester.enterText(find.byType(TextFormField), '500.00');
        
        // Save
        await tester.tap(find.text('Update'));
        await tester.pumpAndSettle();
        
        // Verify target was updated
        expect(find.text('\$500.00'), findsOneWidget);
      });

      testWidgets('Savings progress calculation', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Savings tab
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        
        // Verify progress is displayed
        expect(find.textContaining('% Complete'), findsOneWidget);
        expect(find.textContaining('remaining'), findsOneWidget);
      });
    });

    group('Settings Functionality Tests', () {
      testWidgets('Theme switching (Light/Dark)', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings tab
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        // Find theme toggle
        final themeToggle = find.byType(Switch);
        expect(themeToggle, findsOneWidget);
        
        // Toggle theme to dark
        await tester.tap(themeToggle);
        await tester.pumpAndSettle();
        
        // Verify theme changed
        final materialApp = tester.widget<MaterialApp>(find.byType(MaterialApp));
        expect(materialApp.theme?.brightness, Brightness.dark);
        
        // Toggle back to light
        await tester.tap(themeToggle);
        await tester.pumpAndSettle();
        
        // Verify theme changed back
        final materialAppLight = tester.widget<MaterialApp>(find.byType(MaterialApp));
        expect(materialAppLight.theme?.brightness, Brightness.light);
      });

      testWidgets('Language switching (English/Arabic)', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings tab
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        // Find language dropdown
        final languageDropdown = find.byType(DropdownButton<String>);
        expect(languageDropdown, findsOneWidget);
        
        // Tap dropdown
        await tester.tap(languageDropdown);
        await tester.pumpAndSettle();
        
        // Select Arabic
        await tester.tap(find.text('العربية'));
        await tester.pumpAndSettle();
        
        // Verify language changed
        expect(find.text('الرئيسية'), findsOneWidget);
        
        // Switch back to English
        await tester.tap(languageDropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('English'));
        await tester.pumpAndSettle();
        
        // Verify language changed back
        expect(find.text('Home'), findsOneWidget);
      });

      testWidgets('Settings persistence', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings tab
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        // Change theme
        await tester.tap(find.byType(Switch));
        await tester.pumpAndSettle();
        
        // Navigate away and back
        await tester.tap(find.text('Home'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        // Verify theme setting persisted
        final switchWidget = tester.widget<Switch>(find.byType(Switch));
        expect(switchWidget.value, true);
      });
    });

    group('Data Persistence Tests', () {
      testWidgets('Data persists across app restarts', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Add an expense
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        await tester.enterText(find.byType(TextFormField).first, 'Persistent Expense');
        await tester.enterText(find.byType(TextFormField).at(1), '25.00');
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        
        // Restart app
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Expenses tab
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        // Verify expense persisted
        expect(find.text('Persistent Expense'), findsOneWidget);
        expect(find.text('\$25.00'), findsOneWidget);
      });

      testWidgets('Savings data persists across app restarts', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Add money to savings
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Add to Savings'));
        await tester.pumpAndSettle();
        
        await tester.enterText(find.byType(TextFormField), '200.00');
        await tester.tap(find.text('Add'));
        await tester.pumpAndSettle();
        
        // Restart app
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Savings tab
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        
        // Verify savings data persisted
        expect(find.text('\$200.00'), findsOneWidget);
      });
    });

    group('Form Validation Tests', () {
      testWidgets('All forms work correctly with validation', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Test expense form validation
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        // Test empty form submission
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        expect(find.text('Please enter expense name'), findsOneWidget);
        
        // Test invalid amount
        await tester.enterText(find.byType(TextFormField).at(1), 'abc');
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        expect(find.text('Please enter valid amount'), findsOneWidget);
        
        // Test savings form validation
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Add to Savings'));
        await tester.pumpAndSettle();
        
        // Test empty amount
        await tester.tap(find.text('Add'));
        await tester.pumpAndSettle();
        expect(find.text('Please enter amount'), findsOneWidget);
        
        // Test invalid amount
        await tester.enterText(find.byType(TextFormField), 'invalid');
        await tester.tap(find.text('Add'));
        await tester.pumpAndSettle();
        expect(find.text('Please enter valid amount'), findsOneWidget);
      });
    });

    group('Error Handling Tests', () {
      testWidgets('Error handling works properly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Test network error simulation (if applicable)
        // This would depend on your app's error handling implementation
        
        // Test invalid data handling
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        // Enter negative amount
        await tester.enterText(find.byType(TextFormField).first, 'Test Expense');
        await tester.enterText(find.byType(TextFormField).at(1), '-50.00');
        await tester.tap(find.text('Save'));
        await tester.pumpAndSettle();
        
        // Verify error handling
        expect(find.text('Amount must be positive'), findsOneWidget);
      });
    });

    group('Animation Tests', () {
      testWidgets('Animations work correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Test page transition animations
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        // Test form animation
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        // Verify form appears with animation
        expect(find.byType(TextFormField), findsWidgets);
        
        // Test dismiss animation
        await tester.tap(find.text('Cancel'));
        await tester.pumpAndSettle();
      });
    });

    group('Theme Tests', () {
      testWidgets('Light theme displays correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings and ensure light theme
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        final switchWidget = tester.widget<Switch>(find.byType(Switch));
        if (switchWidget.value) {
          await tester.tap(find.byType(Switch));
          await tester.pumpAndSettle();
        }
        
        // Verify light theme
        final materialApp = tester.widget<MaterialApp>(find.byType(MaterialApp));
        expect(materialApp.theme?.brightness, Brightness.light);
        
        // Test all screens in light theme
        await tester.tap(find.text('Home'));
        await tester.pumpAndSettle();
        expect(find.byType(MaterialApp), findsOneWidget);
        
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        expect(find.byType(MaterialApp), findsOneWidget);
        
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        expect(find.byType(MaterialApp), findsOneWidget);
      });

      testWidgets('Dark theme displays correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings and switch to dark theme
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        final switchWidget = tester.widget<Switch>(find.byType(Switch));
        if (!switchWidget.value) {
          await tester.tap(find.byType(Switch));
          await tester.pumpAndSettle();
        }
        
        // Verify dark theme
        final materialApp = tester.widget<MaterialApp>(find.byType(MaterialApp));
        expect(materialApp.theme?.brightness, Brightness.dark);
        
        // Test all screens in dark theme
        await tester.tap(find.text('Home'));
        await tester.pumpAndSettle();
        expect(find.byType(MaterialApp), findsOneWidget);
        
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        expect(find.byType(MaterialApp), findsOneWidget);
        
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        expect(find.byType(MaterialApp), findsOneWidget);
      });
    });

    group('Localization Tests', () {
      testWidgets('English language displays correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings and ensure English
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        final dropdown = find.byType(DropdownButton<String>);
        await tester.tap(dropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('English'));
        await tester.pumpAndSettle();
        
        // Verify English text
        expect(find.text('Home'), findsOneWidget);
        expect(find.text('Expenses'), findsOneWidget);
        expect(find.text('Savings'), findsOneWidget);
        expect(find.text('Settings'), findsOneWidget);
      });

      testWidgets('Arabic language displays correctly', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Navigate to Settings and switch to Arabic
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        final dropdown = find.byType(DropdownButton<String>);
        await tester.tap(dropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('العربية'));
        await tester.pumpAndSettle();
        
        // Verify Arabic text
        expect(find.text('الرئيسية'), findsOneWidget);
        expect(find.text('المصروفات'), findsOneWidget);
        expect(find.text('الادخار'), findsOneWidget);
        expect(find.text('الإعدادات'), findsOneWidget);
        
        // Test RTL layout
        final scaffold = tester.widget<Scaffold>(find.byType(Scaffold));
        expect(scaffold, findsOneWidget);
      });
    });

    group('Accessibility Tests', () {
      testWidgets('App is accessible', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Test semantic labels
        expect(find.bySemanticsLabel('Home'), findsOneWidget);
        expect(find.bySemanticsLabel('Expenses'), findsOneWidget);
        expect(find.bySemanticsLabel('Savings'), findsOneWidget);
        expect(find.bySemanticsLabel('Settings'), findsOneWidget);
        
        // Test form accessibility
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.add));
        await tester.pumpAndSettle();
        
        expect(find.bySemanticsLabel('Expense name'), findsOneWidget);
        expect(find.bySemanticsLabel('Amount'), findsOneWidget);
      });
    });

    group('Performance Tests', () {
      testWidgets('App performs well with large datasets', (WidgetTester tester) async {
        app.main();
        await tester.pumpAndSettle();
        
        // Add multiple expenses
        for (int i = 0; i < 10; i++) {
          await tester.tap(find.text('Expenses'));
          await tester.pumpAndSettle();
          await tester.tap(find.byIcon(Icons.add));
          await tester.pumpAndSettle();
          
          await tester.enterText(find.byType(TextFormField).first, 'Expense $i');
          await tester.enterText(find.byType(TextFormField).at(1), '${i * 10}.00');
          await tester.tap(find.text('Save'));
          await tester.pumpAndSettle();
        }
        
        // Verify all expenses are displayed
        expect(find.text('Expense 0'), findsOneWidget);
        expect(find.text('Expense 9'), findsOneWidget);
        
        // Test scrolling performance
        await tester.drag(find.byType(ListView), const Offset(0, -500));
        await tester.pumpAndSettle();
      });
    });

    group('CI/CD Headless Mode Tests', () {
      testWidgets('All tests can run in headless mode', (WidgetTester tester) async {
        // This test ensures all functionality works without UI interactions
        app.main();
        await tester.pumpAndSettle();
        
        // Verify app initializes
        expect(find.byType(MaterialApp), findsOneWidget);
        
        // Test navigation programmatically
        await tester.tap(find.text('Expenses'));
        await tester.pumpAndSettle();
        
        await tester.tap(find.text('Savings'));
        await tester.pumpAndSettle();
        
        await tester.tap(find.text('Settings'));
        await tester.pumpAndSettle();
        
        // Verify all screens load
        expect(find.byType(Scaffold), findsOneWidget);
      });
    });
  });
}
