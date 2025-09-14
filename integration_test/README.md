# Integration Tests for Expense Saver App

This directory contains comprehensive integration tests for the Expense Saver Flutter app.

## Test Coverage

### 🧭 Navigation Flow Tests
- Complete navigation flow between all tabs
- Bottom navigation bar functionality
- Drawer navigation
- Tab switching animations

### 💰 Expenses Functionality Tests
- Add new expenses
- Edit existing expenses
- Delete expenses
- Form validation
- Category selection
- Amount validation

### 💾 Savings Functionality Tests
- Add money to savings
- Update monthly targets
- Progress calculation
- Savings persistence

### ⚙️ Settings Functionality Tests
- Theme switching (Light/Dark)
- Language switching (English/Arabic)
- Settings persistence
- Preference storage

### 💾 Data Persistence Tests
- Data persists across app restarts
- SharedPreferences integration
- State management persistence

### 📝 Form Validation Tests
- All forms work correctly with validation
- Required field validation
- Format validation
- Error message display

### 🚨 Error Handling Tests
- Network error handling
- Invalid data handling
- Graceful error recovery
- User-friendly error messages

### 🎬 Animation Tests
- Page transition animations
- Form appearance animations
- Dismiss animations
- Smooth user interactions

### 🎨 Theme Tests
- Light theme display
- Dark theme display
- Theme switching
- Consistent theming across screens

### 🌍 Localization Tests
- English language display
- Arabic language display
- RTL layout support
- Language switching

### ♿ Accessibility Tests
- Semantic labels
- Screen reader support
- Keyboard navigation
- Focus management

### ⚡ Performance Tests
- Large dataset handling
- Scrolling performance
- Memory usage
- App responsiveness

### 🤖 CI/CD Headless Mode Tests
- Headless mode compatibility
- Automated testing support
- CI/CD pipeline integration

## Running Tests

### Prerequisites
- Flutter SDK installed
- Integration test dependencies
- Test device or emulator

### Command Line
```bash
# Run all integration tests
flutter test integration_test/

# Run specific test group
flutter test integration_test/app_test.dart --name "Navigation Flow Tests"

# Run with verbose output
flutter test integration_test/ --verbose

# Run in headless mode (for CI/CD)
flutter test integration_test/ --headless
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run Integration Tests
  run: |
    flutter test integration_test/ --headless
    flutter test integration_test/ --coverage
```

## Test Structure

### Test Groups
Each test group focuses on a specific aspect of the app:

1. **App Initialization Tests** - Basic app startup and initialization
2. **Navigation Flow Tests** - Navigation between screens and tabs
3. **Expenses Functionality Tests** - CRUD operations for expenses
4. **Savings Functionality Tests** - Savings management features
5. **Settings Functionality Tests** - App settings and preferences
6. **Data Persistence Tests** - Data storage and retrieval
7. **Form Validation Tests** - Input validation and error handling
8. **Error Handling Tests** - Error scenarios and recovery
9. **Animation Tests** - UI animations and transitions
10. **Theme Tests** - Light and dark theme functionality
11. **Localization Tests** - Multi-language support
12. **Accessibility Tests** - Accessibility compliance
13. **Performance Tests** - App performance under load
14. **CI/CD Headless Mode Tests** - Automated testing support

### Test Methods
Each test method follows the pattern:
```dart
testWidgets('Test description', (WidgetTester tester) async {
  // Setup
  app.main();
  await tester.pumpAndSettle();
  
  // Action
  await tester.tap(find.text('Button'));
  await tester.pumpAndSettle();
  
  // Verification
  expect(find.text('Expected Result'), findsOneWidget);
});
```

## Best Practices

### 1. Test Isolation
- Each test is independent
- No shared state between tests
- Clean setup and teardown

### 2. Realistic User Interactions
- Use actual user gestures (tap, drag, enter text)
- Wait for animations to complete (`pumpAndSettle()`)
- Test real user workflows

### 3. Comprehensive Coverage
- Test happy path scenarios
- Test error conditions
- Test edge cases
- Test different user configurations

### 4. Maintainable Tests
- Clear test names and descriptions
- Grouped related tests
- Reusable test utilities
- Good error messages

### 5. Performance Considerations
- Use `pumpAndSettle()` appropriately
- Avoid unnecessary waits
- Test with realistic data volumes
- Monitor test execution time

## Troubleshooting

### Common Issues

#### Tests Timing Out
```dart
// Use shorter timeouts for specific operations
await tester.pumpAndSettle(const Duration(seconds: 5));
```

#### Widget Not Found
```dart
// Use more specific finders
find.byKey(const Key('specific-widget'))
find.byType(TextFormField).first
```

#### Animation Issues
```dart
// Wait for animations to complete
await tester.pumpAndSettle();
// Or wait for specific duration
await tester.pump(const Duration(milliseconds: 500));
```

#### State Management Issues
```dart
// Ensure state is properly updated
await tester.pump();
await tester.pumpAndSettle();
```

### Debug Tips
- Use `debugDumpApp()` to inspect widget tree
- Use `tester.printToConsole()` for debugging output
- Use `flutter test --verbose` for detailed output
- Use `flutter test --coverage` for coverage analysis

## Continuous Integration

### GitHub Actions
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: subosito/flutter-action@v2
      - run: flutter test integration_test/ --headless
```

### Jenkins
```groovy
stage('Integration Tests') {
  steps {
    sh 'flutter test integration_test/ --headless'
  }
}
```

## Coverage Reports

Generate coverage reports for integration tests:
```bash
flutter test integration_test/ --coverage
genhtml coverage/lcov.info -o coverage/html
```

## Contributing

When adding new tests:
1. Follow existing test structure
2. Add appropriate test groups
3. Include both positive and negative test cases
4. Update this README with new test coverage
5. Ensure tests run in headless mode
6. Add proper error handling and cleanup
