#!/usr/bin/env python3
"""
Smart validation script that uses AI-generated validation criteria
to validate each step of the pipeline.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("Usage: smart_validate.py <step_number> <step_content>")
        sys.exit(1)
    
    step_number = int(sys.argv[1])
    step_content = sys.argv[2]
    
    # Load the app spec to get validation criteria
    spec_file = "out/app_spec.json"
    if not os.path.exists(spec_file):
        print("❌ App spec file not found")
        sys.exit(1)
    
    with open(spec_file, 'r', encoding='utf-8') as f:
        app_spec = json.load(f)
    
    prompts = app_spec.get("cursor_prompts", [])
    if step_number < 1 or step_number > len(prompts):
        print(f"❌ Invalid step number: {step_number}")
        sys.exit(1)
    
    # Get the prompt and validation criteria for this step
    step_prompt = prompts[step_number - 1]
    
    # Handle both old string format and new object format
    if isinstance(step_prompt, dict):
        prompt_text = step_prompt.get("prompt", "")
        validation_criteria = step_prompt.get("validation_criteria", {})
    else:
        prompt_text = str(step_prompt)
        validation_criteria = {}
    
    print(f"📋 Validating Step {step_number}: {prompt_text[:100]}...")
    
    if not validation_criteria:
        print("⚠️  No validation criteria provided - using basic validation")
        # Fallback to basic validation
        if validate_basic(step_content, prompt_text):
            print("✅ Basic validation passed")
            sys.exit(0)
        else:
            print("❌ Basic validation failed")
            sys.exit(1)
    
    # Perform smart validation using the criteria
    validation_results = validate_with_criteria(validation_criteria)
    
    # Check if all validations passed
    failed_validations = [k for k, v in validation_results.items() if not v]
    
    if not failed_validations:
        print("✅ All validation criteria passed")
        sys.exit(0)
    else:
        print(f"❌ Validation failed for: {', '.join(failed_validations)}")
        for failed in failed_validations:
            print(f"   - {failed}: {validation_results[failed]}")
        sys.exit(1)


def validate_with_criteria(criteria):
    """Validate using the provided criteria dictionary."""
    results = {}
    
    for criterion, expected_value in criteria.items():
        try:
            if criterion == "file_exists":
                results[criterion] = validate_file_exists(expected_value)
            elif criterion == "contains_class":
                results[criterion] = validate_contains_class(expected_value)
            elif criterion == "contains_dependencies":
                results[criterion] = validate_contains_dependencies(expected_value)
            elif criterion == "contains_keys":
                results[criterion] = validate_contains_keys(expected_value)
            elif criterion == "has_methods":
                results[criterion] = validate_has_methods(expected_value)
            elif criterion == "has_language_switcher":
                results[criterion] = validate_has_language_switcher()
            elif criterion == "has_theme_toggle":
                results[criterion] = validate_has_theme_toggle()
            elif criterion == "has_notification_prefs":
                results[criterion] = validate_has_notification_prefs()
            elif criterion == "material_3_design":
                results[criterion] = validate_material_3_design()
            elif criterion == "rtl_support":
                results[criterion] = validate_rtl_support()
            elif criterion == "no_placeholders":
                results[criterion] = validate_no_placeholders()
            elif criterion == "no_counter_code":
                results[criterion] = validate_no_counter_code()
            elif criterion == "no_fake_data":
                results[criterion] = validate_no_fake_data()
            elif criterion == "arabic_text":
                results[criterion] = validate_arabic_text()
            elif criterion == "has_bottom_navigation":
                results[criterion] = validate_has_bottom_navigation()
            elif criterion == "has_tabs":
                results[criterion] = validate_has_tabs(expected_value)
            elif criterion == "has_circular_progress":
                results[criterion] = validate_has_circular_progress()
            elif criterion == "has_error_state":
                results[criterion] = validate_has_error_state()
            elif criterion == "has_retry_button":
                results[criterion] = validate_has_retry_button()
            elif criterion == "accessible":
                results[criterion] = validate_accessible()
            elif criterion == "localized":
                results[criterion] = validate_localized()
            elif criterion == "has_cfbundle_localizations":
                results[criterion] = validate_cfbundle_localizations(expected_value)
            elif criterion == "has_cfbundle_development_region":
                results[criterion] = validate_cfbundle_development_region(expected_value)
            elif criterion == "has_test_functions":
                results[criterion] = validate_has_test_functions(expected_value)
            elif criterion == "tests_both_locales":
                results[criterion] = validate_tests_both_locales(expected_value)
            elif criterion == "has_widget_tests":
                results[criterion] = validate_has_widget_tests()
            elif criterion == "tests_navigation":
                results[criterion] = validate_tests_navigation()
            elif criterion == "tests_rtl_layout":
                results[criterion] = validate_tests_rtl_layout()
            elif criterion == "tests_accessibility":
                results[criterion] = validate_tests_accessibility()
            else:
                # Generic boolean validation
                results[criterion] = bool(expected_value)
        except Exception as e:
            results[criterion] = f"Error: {str(e)}"
    
    return results


def validate_file_exists(file_path):
    """Check if a file exists."""
    return os.path.exists(file_path)


def validate_contains_class(class_name):
    """Check if any Dart file contains the specified class."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if f"class {class_name}" in content:
                    return True
        except:
            continue
    return False


def validate_contains_dependencies(dependencies):
    """Check if pubspec.yaml contains the specified dependencies."""
    if not os.path.exists("pubspec.yaml"):
        return False
    
    with open("pubspec.yaml", 'r', encoding='utf-8') as f:
        content = f.read()
    
    for dep in dependencies:
        if dep not in content:
            return False
    return True


def validate_contains_keys(keys):
    """Check if ARB files contain the specified keys."""
    arb_files = list(Path(".").rglob("*.arb"))
    if not arb_files:
        return False
    
    for arb_file in arb_files:
        try:
            with open(arb_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for key in keys:
                    if f'"{key}"' not in content:
                        return False
        except:
            continue
    return True


def validate_has_methods(methods):
    """Check if any Dart file contains the specified methods."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for method in methods:
                    if f"{method}(" in content:
                        return True
        except:
            continue
    return False


def validate_has_language_switcher():
    """Check if there's a language switcher in the code."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "DropdownButton" in content and ("English" in content or "العربية" in content):
                    return True
        except:
            continue
    return False


def validate_has_theme_toggle():
    """Check if there's a theme toggle in the code."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if ("Switch" in content or "Toggle" in content) and ("theme" in content.lower() or "dark" in content.lower()):
                    return True
        except:
            continue
    return False


def validate_has_notification_prefs():
    """Check if there are notification preferences in the code."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "notification" in content.lower() and ("preference" in content.lower() or "setting" in content.lower()):
                    return True
        except:
            continue
    return False


def validate_material_3_design():
    """Check if Material 3 design is used."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "MaterialApp" in content and ("theme" in content.lower() or "colorScheme" in content):
                    return True
        except:
            continue
    return False


def validate_rtl_support():
    """Check if RTL support is implemented."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "TextDirection.rtl" in content or "Directionality" in content:
                    return True
        except:
            continue
    return False


def validate_no_placeholders():
    """Check if there are no placeholder texts."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Lorem ipsum" in content or "placeholder" in content.lower() or "TODO" in content:
                    return False
        except:
            continue
    return True


def validate_no_counter_code():
    """Check if counter app code has been removed."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "counter" in content.lower() and ("increment" in content.lower() or "MyHomePage" in content):
                    return False
        except:
            continue
    return True


def validate_no_fake_data():
    """Check if there's no fake data."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "fake" in content.lower() or "sample" in content.lower() or "demo" in content.lower():
                    return False
        except:
            continue
    return True


def validate_arabic_text():
    """Check if Arabic text is present."""
    arb_files = list(Path(".").rglob("*.arb"))
    for arb_file in arb_files:
        try:
            with open(arb_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for Arabic characters
                if re.search(r'[\u0600-\u06FF]', content):
                    return True
        except:
            continue
    return False


def validate_has_bottom_navigation():
    """Check if bottom navigation is implemented."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "BottomNavigationBar" in content:
                    return True
        except:
            continue
    return False


def validate_has_tabs(tabs):
    """Check if specified tabs are present."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for tab in tabs:
                    if tab in content:
                        return True
        except:
            continue
    return False


def validate_has_circular_progress():
    """Check if CircularProgressIndicator is used."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "CircularProgressIndicator" in content:
                    return True
        except:
            continue
    return False


def validate_has_error_state():
    """Check if error state handling is implemented."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "error" in content.lower() and ("state" in content.lower() or "exception" in content.lower()):
                    return True
        except:
            continue
    return False


def validate_has_retry_button():
    """Check if retry button is implemented."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "retry" in content.lower() and "button" in content.lower():
                    return True
        except:
            continue
    return False


def validate_accessible():
    """Check if accessibility features are implemented."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Semantics" in content or "accessibility" in content.lower():
                    return True
        except:
            continue
    return False


def validate_localized():
    """Check if localization is implemented."""
    dart_files = list(Path(".").rglob("*.dart"))
    for dart_file in dart_files:
        try:
            with open(dart_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "AppLocalizations" in content or "Localizations" in content:
                    return True
        except:
            continue
    return False


def validate_cfbundle_localizations(locales):
    """Check if Info.plist has the specified localizations."""
    plist_file = "ios/Runner/Info.plist"
    if not os.path.exists(plist_file):
        return False
    
    with open(plist_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for locale in locales:
        if locale not in content:
            return False
    return True


def validate_cfbundle_development_region(region):
    """Check if Info.plist has the specified development region."""
    plist_file = "ios/Runner/Info.plist"
    if not os.path.exists(plist_file):
        return False
    
    with open(plist_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return region in content


def validate_has_test_functions(functions):
    """Check if test file has the specified test functions."""
    test_files = list(Path(".").rglob("*_test.dart"))
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for func in functions:
                    if f"test('{func}" in content or f"testWidgets('{func}" in content:
                        return True
        except:
            continue
    return False


def validate_tests_both_locales(locales):
    """Check if tests cover both locales."""
    test_files = list(Path(".").rglob("*_test.dart"))
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for locale in locales:
                    if locale in content:
                        return True
        except:
            continue
    return False


def validate_has_widget_tests():
    """Check if widget tests are present."""
    test_files = list(Path(".").rglob("*_test.dart"))
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "testWidgets" in content:
                    return True
        except:
            continue
    return False


def validate_tests_navigation():
    """Check if navigation tests are present."""
    test_files = list(Path(".").rglob("*_test.dart"))
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "navigation" in content.lower() and "test" in content.lower():
                    return True
        except:
            continue
    return False


def validate_tests_rtl_layout():
    """Check if RTL layout tests are present."""
    test_files = list(Path(".").rglob("*_test.dart"))
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "rtl" in content.lower() and "test" in content.lower():
                    return True
        except:
            continue
    return False


def validate_tests_accessibility():
    """Check if accessibility tests are present."""
    test_files = list(Path(".").rglob("*_test.dart"))
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "accessibility" in content.lower() and "test" in content.lower():
                    return True
        except:
            continue
    return False


def validate_basic(step_content, prompt_text):
    """Basic validation fallback when no criteria are provided."""
    # Simple file existence check based on prompt content
    if "Create lib/" in prompt_text:
        # Extract file path from prompt
        match = re.search(r'Create (lib/[^\s]+\.dart)', prompt_text)
        if match:
            file_path = match.group(1)
            return os.path.exists(file_path)
    
    if "Edit pubspec.yaml" in prompt_text:
        return os.path.exists("pubspec.yaml")
    
    if "Update ios/Runner/Info.plist" in prompt_text:
        return os.path.exists("ios/Runner/Info.plist")
    
    # Default to true if we can't determine what to check
    return True


if __name__ == "__main__":
    main()
