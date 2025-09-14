#!/usr/bin/env python3
"""
LLM prompt generation script for AppMagician pipeline.
Generates app specifications and prompts using ChatGPT or DeepSeek APIs.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import time


def main():
    # Configuration from environment variables
    provider = os.environ.get('LLM_PROVIDER', 'chatgpt').strip().lower()
    openai_model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    deepseek_model = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    api_key = os.environ.get('OPENAI_API_KEY') if provider == 'chatgpt' else os.environ.get('DEEPSEEK_API_KEY')
    
    # Inputs from Jenkins params/env (all optional)
    prompt_hint = os.environ.get('APP_IDEA', '').strip()
    bundle_id = os.environ.get('BUNDLE_ID', 'com.example.generated').strip()
    locales_str = os.environ.get('LOCALES', '').strip()
    default_locale = os.environ.get('DEFAULT_LOCALE', 'en').strip()
    locales = [x.strip() for x in (locales_str.split(',') if locales_str else [default_locale]) if x.strip()]
    if not locales:
        locales = ['en']

    # Debug: Print environment variables (only in debug mode)
    if os.environ.get('DEBUG_MODE') == '1':
        print(f"DEBUG: LLM_PROVIDER={provider}", file=sys.stderr)
        print(f"DEBUG: OPENAI_MODEL={openai_model}", file=sys.stderr)
        print(f"DEBUG: DEEPSEEK_MODEL={deepseek_model}", file=sys.stderr)
        print(f"DEBUG: API_KEY present={bool(api_key)}", file=sys.stderr)
        print(f"DEBUG: APP_IDEA='{prompt_hint}'", file=sys.stderr)
        print(f"DEBUG: BUNDLE_ID='{bundle_id}'", file=sys.stderr)
        print(f"DEBUG: LOCALES='{locales_str}'", file=sys.stderr)
    
    if not api_key:
        print("Missing API key for provider", provider, file=sys.stderr)
        # For testing purposes, create a mock response
        if os.environ.get('TEST_MODE') == '1':
            print("TEST_MODE enabled - generating mock response", file=sys.stderr)
            obj = {
                "app_name": "generated_app",
                "spec": {"theme": "light", "locale": locales[0], "platforms": ["ios"], "features": ["utility"]},
                "cursor_prompts": [
                    "Edit pubspec.yaml: add dependencies for state management and UI components.",
                    "Create lib/main.dart: set up MaterialApp with theme and routing.",
                    "Create lib/features/main/main_model.dart: define main data model.",
                    "Create lib/features/main/main_service.dart: implement CRUD operations.",
                    "Create lib/features/main/main_list_widget.dart: display list of items.",
                    "Create lib/features/main/main_form_widget.dart: add/edit item form.",
                    "Write test/features/main/main_service_test.dart: unit tests for service.",
                    "Write test/features/main/main_widget_test.dart: widget tests for UI."
                ],
                "meta": {
                    "requested_locales": locales,
                    "bundle_id_hint": bundle_id,
                    "feature_summary": prompt_hint or "Implement app feature."
                }
            }
            os.makedirs("out", exist_ok=True)
            with open("out/app_spec.json", "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, ensure_ascii=False)
            with open("out/app_dir.txt", "w") as f:
                f.write(obj.get("app_name", "test_app"))
            print("Provider:", provider)
            print("Model:", "test-mode")
            print("App name:", obj.get("app_name"))
            print("Prompts:", len(obj.get("cursor_prompts", [])))
            return
        sys.exit(1)

    url = "https://api.openai.com/v1/chat/completions" if provider == 'chatgpt' else "https://api.deepseek.com/chat/completions"
    model = openai_model if provider == 'chatgpt' else deepseek_model
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # ---- Validation helpers ----
    FORBIDDEN = [
        r'\bflutter\s+create\b',
        r'\bCreate\s+(a\s+)?Flutter\s+project\b',
        r'\bset\s+up\s+the\s+iOS\s+platform\b',
        r'\bUpdate\s+ios/Runner\.xcodeproj/project\.pbxproj\b'
    ]

    def prompt_is_valid(p):
        # Handle both old string format and new object format
        if isinstance(p, dict):
            prompt_text = p.get("prompt", "")
            validation_criteria = p.get("validation_criteria", {})
            if not prompt_text or not prompt_text.strip():
                return False, "empty_prompt"
            if not validation_criteria:
                return False, "missing_validation_criteria"
            p = prompt_text  # Use the prompt text for further validation
        
        if not isinstance(p, str) or not p.strip():
            return False, "empty"
        if len(p) > 8000:  # Increased to 8000 for extremely detailed, human-level prompts
            return False, "too_long"
        s = p.lower()
        if '```' in p:
            return False, "code_fence"
        for pat in FORBIDDEN:
            if re.search(pat, p, re.I):
                return False, "forbidden:" + pat
        # More flexible validation - allow prompts that mention files, directories, or development concepts
        has_development_reference = bool(re.search(r'\b(pubspec\.yaml|analysis_options\.yaml|lib/|test/|ios/|\.dart|\.arb|\.yaml|\.plist|dependencies|localization|theme|widget|repository|entity|model)\b', p))
        if not has_development_reference:
            return False, "no_explicit_file_paths"
        return True, "ok"

    HINT_KEYWORDS = [w for w in re.findall(r'[a-z]{3,}', prompt_hint.lower())] or []

    def prompts_cover_hint(prompts):
        if not HINT_KEYWORDS:
            return True
        
        # Extract prompt text from both old string format and new object format
        prompt_texts = []
        for p in prompts:
            if isinstance(p, dict):
                prompt_texts.append(p.get("prompt", ""))
            else:
                prompt_texts.append(str(p))
        
        joined = " ".join(prompt_texts).lower()
        # Be more flexible - only require 1-2 keywords instead of all 3
        required_keywords = min(2, len(HINT_KEYWORDS))
        matching_keywords = sum(1 for w in HINT_KEYWORDS if w in joined)
        if os.environ.get('DEBUG_MODE') == '1':
            print(f"DEBUG: Hint keywords: {HINT_KEYWORDS}", file=sys.stderr)
            print(f"DEBUG: Required: {required_keywords}, Found: {matching_keywords}", file=sys.stderr)
        return matching_keywords >= required_keywords

    def concrete_enough(prompts):
        # Extract prompt text from both old string format and new object format
        prompt_texts = []
        for p in prompts:
            if isinstance(p, dict):
                prompt_texts.append(p.get("prompt", ""))
            else:
                prompt_texts.append(str(p))
        
        joined = "\n".join(prompt_texts)
        # More comprehensive quality checks (widget tests are optional and non-critical)
        has_dart_files = bool(re.search(r'\blib/[^\s]+\.dart\b', joined))
        has_tests = bool(re.search(r'\btest/[^\s]+_test\.dart\b', joined))
        has_localization = bool(re.search(r'\.arb\b|l10n|localization', joined, re.I))
        has_modern_ui = bool(re.search(r'material|theme|ui|widget', joined, re.I))
        has_architecture = bool(re.search(r'repository|entity|model|service', joined, re.I))
        
        # Core functionality requirements - tests are optional bonus
        # Require at least 3 out of 4 core indicators (tests don't count toward minimum)
        core_quality_score = sum([has_dart_files, has_localization, has_modern_ui, has_architecture])
        if os.environ.get('DEBUG_MODE') == '1':
            print(f"DEBUG: Quality check - dart:{has_dart_files}, tests:{has_tests} (optional), localization:{has_localization}, ui:{has_modern_ui}, arch:{has_architecture}, core_score:{core_quality_score}/4", file=sys.stderr)
        return core_quality_score >= 3

    def set_is_valid(prompts):
        if not isinstance(prompts, list) or not prompts:
            return False, ["prompts_missing"]
        problems = []
        if not (12 <= len(prompts) <= 15):  # Updated range for extremely detailed prompts
            problems.append(f"count:{len(prompts)}")
        
        # Check total length of all prompts (should be reasonable but detailed)
        total_length = 0
        for p in prompts:
            if isinstance(p, dict):
                total_length += len(p.get("prompt", ""))
            else:
                total_length += len(str(p))
        
        if os.environ.get('DEBUG_MODE') == '1':
            print(f"DEBUG: Total prompts length: {total_length} characters", file=sys.stderr)
        if total_length > 25000:  # Increased limit for extremely detailed prompts
            problems.append(f"total_length:{total_length}")
        
        for i, p in enumerate(prompts):
            ok, why = prompt_is_valid(p)
            if not ok:
                problems.append(f"p{i+1}:{why}")
        if not prompts_cover_hint(prompts):
            problems.append("idea_alignment")
        if not concrete_enough(prompts):
            problems.append("concreteness")
        return (len(problems) == 0), problems

    def strip_code_fences(text: str) -> str:
        text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.I)
        text = re.sub(r'```\s*$', '', text, flags=re.I)
        return text.strip()

    system_msg = (
        "You are a senior Flutter iOS lead working INSIDE an existing repo. "
        "Your task is to generate EXTREMELY DETAILED, PRODUCTION-READY app specifications. "
        "Each prompt must be as detailed as a human would ask ChatGPT for Cursor prompts. "
        "Focus on POLISHED, MODERN UI/UX with working localization and NO fake data. "
        "Return STRICT JSON only. Do NOT suggest creating projects. "
        "Every step must edit explicit files under pubspec.yaml, analysis_options.yaml, lib/**, test/**, or ios/** (safe files only). "
        "CRITICAL: Each prompt must specify exact file paths, class names, method signatures, UI components, colors, spacing, and complete implementation details. "
        "MANDATORY: Remove all fake/placeholder data, create working localization with settings screen, implement fully functional features. "
        "Prioritize: 1) Remove fake data, 2) Working localization, 3) Functional features, 4) Modern Material Design 3.0, 5) Proper RTL/LTR support. "
        "PUT widget tests as the FINAL step - they are optional and non-critical for core app functionality. "
        "VALIDATION REQUIREMENT: For each prompt, include a 'validation_criteria' field that specifies exactly what to check to verify the step was completed successfully. "
        "Validation criteria should include: file existence checks, class/method presence, specific content patterns, and functional requirements."
    )

    # App spec scaffold we want the model to follow - MUCH MORE DETAILED like human prompts
    spec_hint = {
        "app_name": "app_generated",
        "spec": {"theme": "light", "locale": locales[0], "platforms": ["ios"], "features": ["utility"]},
        "cursor_prompts": [
            {
                "prompt": "Edit pubspec.yaml: Add flutter_localizations, intl ^0.19.0, provider ^6.1.1, shared_preferences ^2.2.2, cupertino_icons ^1.0.8, and any specific packages needed for the app functionality. Remove any unused dependencies and ensure all versions are compatible.",
                "validation_criteria": {
                    "file_exists": "pubspec.yaml",
                    "contains_dependencies": ["flutter_localizations", "intl", "provider", "shared_preferences"],
                    "no_unused_deps": true,
                    "version_compatible": true
                }
            },
            {
                "prompt": "Create lib/l10n/app_en.arb: Add ALL user-facing strings including 'app_title', 'settings', 'language', 'theme', 'notifications', 'save', 'cancel', 'delete', 'edit', 'add', 'search', 'loading', 'error', 'success', 'retry', 'back', 'next', 'done', 'yes', 'no', 'ok', and feature-specific strings. Each string should be complete sentences, not fragments.",
                "validation_criteria": {
                    "file_exists": "lib/l10n/app_en.arb",
                    "contains_keys": ["app_title", "settings", "language", "theme", "notifications", "save", "cancel"],
                    "no_placeholders": true,
                    "complete_sentences": true
                }
            },
            {
                "prompt": "Create lib/l10n/app_ar.arb: Translate ALL strings from app_en.arb to Arabic. Ensure proper RTL text direction and cultural appropriateness. Use formal Arabic (Fusha) unless the app context requires colloquial. Include proper Arabic punctuation and formatting.",
                "validation_criteria": {
                    "file_exists": "lib/l10n/app_ar.arb",
                    "contains_keys": ["app_title", "settings", "language", "theme", "notifications", "save", "cancel"],
                    "arabic_text": true,
                    "rtl_support": true
                }
            },
            {
                "prompt": "Create lib/l10n/app_localizations.dart: Implement AppLocalizations class extending LocalizationsDelegate. Add methods for all strings, proper RTL support with TextDirection.rtl for Arabic, and fallback to English. Include locale-specific number/date formatting.",
                "validation_criteria": {
                    "file_exists": "lib/l10n/app_localizations.dart",
                    "contains_class": "AppLocalizations",
                    "extends_delegate": "LocalizationsDelegate",
                    "has_rtl_support": true,
                    "has_fallback": true
                }
            },
            {
                "prompt": "Create lib/main.dart: Replace default counter app with MaterialApp 3.0. Set supportedLocales to [Locale('en'), Locale('ar')], localizationsDelegates with AppLocalizations.delegate, localeResolutionCallback for fallback, theme with Material 3.0 colors, and home pointing to MainScreen(). Remove all counter app code.",
                "validation_criteria": {
                    "file_exists": "lib/main.dart",
                    "contains_materialapp": true,
                    "supported_locales": ["en", "ar"],
                    "localizations_delegate": "AppLocalizations.delegate",
                    "no_counter_code": true,
                    "material_3_theme": true
                }
            },
            {
                "prompt": "Create lib/features/settings/presentation/screens/settings_screen.dart: Build a complete settings screen with language switcher (DropdownButton with 'English' and 'العربية' options), theme toggle (Light/Dark), notification preferences, and app info section. Use Material 3.0 design with proper spacing, typography, and RTL layout support.",
                "validation_criteria": {
                    "file_exists": "lib/features/settings/presentation/screens/settings_screen.dart",
                    "contains_class": "SettingsScreen",
                    "has_language_switcher": true,
                    "has_theme_toggle": true,
                    "has_notification_prefs": true,
                    "material_3_design": true,
                    "rtl_support": true
                }
            },
            {
                "prompt": "Create lib/features/settings/presentation/providers/settings_provider.dart: Implement ChangeNotifier with SharedPreferences for persistent storage. Include methods: setLanguage(String locale), setTheme(bool isDark), getLanguage(), getTheme(), loadSettings(), saveSettings(). Handle loading states and errors.",
                "validation_criteria": {
                    "file_exists": "lib/features/settings/presentation/providers/settings_provider.dart",
                    "contains_class": "SettingsProvider",
                    "extends_changenotifier": true,
                    "has_methods": ["setLanguage", "setTheme", "getLanguage", "getTheme", "loadSettings", "saveSettings"],
                    "uses_sharedpreferences": true,
                    "has_error_handling": true
                }
            },
            {
                "prompt": "Create lib/features/settings/data/repositories/settings_repository.dart: Implement SettingsRepository interface with methods: saveLanguage(String locale), saveTheme(bool isDark), getLanguage(), getTheme(). Use SharedPreferences for persistence and proper error handling.",
                "validation_criteria": {
                    "file_exists": "lib/features/settings/data/repositories/settings_repository.dart",
                    "contains_class": "SettingsRepository",
                    "has_methods": ["saveLanguage", "saveTheme", "getLanguage", "getTheme"],
                    "uses_sharedpreferences": true,
                    "has_error_handling": true
                }
            },
            {
                "prompt": "Create lib/features/core/presentation/screens/main_screen.dart: Replace MyHomePage with a proper main screen that has BottomNavigationBar with Home, Settings tabs. Include proper state management, navigation, and RTL support. Remove all counter app references and fake data.",
                "validation_criteria": {
                    "file_exists": "lib/features/core/presentation/screens/main_screen.dart",
                    "contains_class": "MainScreen",
                    "has_bottom_navigation": true,
                    "has_tabs": ["Home", "Settings"],
                    "no_counter_references": true,
                    "no_fake_data": true,
                    "rtl_support": true
                }
            },
            {
                "prompt": "Create lib/features/core/presentation/widgets/app_drawer.dart: Build a Material 3.0 drawer with app logo, navigation items (Home, Settings, About), language switcher, theme toggle, and proper RTL layout. Include proper spacing and typography.",
                "validation_criteria": {
                    "file_exists": "lib/features/core/presentation/widgets/app_drawer.dart",
                    "contains_class": "AppDrawer",
                    "has_navigation_items": ["Home", "Settings", "About"],
                    "has_language_switcher": true,
                    "has_theme_toggle": true,
                    "material_3_design": true,
                    "rtl_support": true
                }
            },
            {
                "prompt": "Create lib/features/core/presentation/widgets/loading_widget.dart: Build a reusable loading widget with CircularProgressIndicator, proper sizing, and loading text that respects localization. Include error state with retry button.",
                "validation_criteria": {
                    "file_exists": "lib/features/core/presentation/widgets/loading_widget.dart",
                    "contains_class": "LoadingWidget",
                    "has_circular_progress": true,
                    "has_loading_text": true,
                    "has_error_state": true,
                    "has_retry_button": true,
                    "localized_text": true
                }
            },
            {
                "prompt": "Create lib/features/core/presentation/widgets/error_widget.dart: Build a reusable error widget with error icon, error message, retry button, and proper styling. Make it accessible and localized.",
                "validation_criteria": {
                    "file_exists": "lib/features/core/presentation/widgets/error_widget.dart",
                    "contains_class": "ErrorWidget",
                    "has_error_icon": true,
                    "has_error_message": true,
                    "has_retry_button": true,
                    "accessible": true,
                    "localized": true
                }
            },
            {
                "prompt": "Update ios/Runner/Info.plist: Add CFBundleLocalizations array with 'en' and 'ar', CFBundleDevelopmentRegion set to 'en', and any required permissions for the app functionality. Remove any unused configurations.",
                "validation_criteria": {
                    "file_exists": "ios/Runner/Info.plist",
                    "has_cfbundle_localizations": ["en", "ar"],
                    "has_cfbundle_development_region": "en",
                    "no_unused_configs": true
                }
            },
            {
                "prompt": "Write test/features/settings/settings_provider_test.dart: Unit tests for SettingsProvider including language switching, theme toggling, persistence, and error handling. Test both English and Arabic locales.",
                "validation_criteria": {
                    "file_exists": "test/features/settings/settings_provider_test.dart",
                    "has_test_functions": ["language_switching", "theme_toggling", "persistence", "error_handling"],
                    "tests_both_locales": ["en", "ar"]
                }
            },
            {
                "prompt": "Write test/features/core/main_screen_test.dart: Widget tests for MainScreen including navigation, RTL layout, and accessibility. Test language switching and theme changes (optional - non-critical for app functionality).",
                "validation_criteria": {
                    "file_exists": "test/features/core/main_screen_test.dart",
                    "has_widget_tests": true,
                    "tests_navigation": true,
                    "tests_rtl_layout": true,
                    "tests_accessibility": true
                }
            }
        ],
        "meta": {
            "requested_locales": locales,
            "bundle_id_hint": bundle_id,
            "feature_summary": prompt_hint or "Implement utility feature."
        }
    }

    # User message that forces alignment with the hint and forbids project creation
    user_msg = f"""
Create a **PRODUCTION-READY iOS Flutter app** based on this idea:
"{prompt_hint}"

CRITICAL REQUIREMENTS - BE EXTREMELY DETAILED:

1. **REMOVE ALL FAKE/PLACEHOLDER DATA**: 
   - Delete all counter app code, fake data, sample data, placeholder text
   - Replace with real, functional features that match the app idea
   - No "Lorem ipsum", "Sample text", or demo content

2. **WORKING LOCALIZATION SYSTEM**:
   - Create complete .arb files with ALL user-facing strings
   - Build a settings screen with language switcher (English/Arabic dropdown)
   - Implement proper RTL layout for Arabic (text direction, UI mirroring)
   - Add persistent language storage with SharedPreferences
   - Test language switching works immediately

3. **POLISHED UI/UX**:
   - Material Design 3.0 with proper color schemes, typography, spacing
   - Smooth animations, loading states, error handling
   - Responsive layout, proper navigation, intuitive user flow
   - Remove all default Flutter styling, create custom polished design

4. **WORKING FEATURES**:
   - Each feature must be fully functional, not just UI mockups
   - Real data persistence, proper state management
   - Error handling, loading states, user feedback
   - Features must work in both English and Arabic

5. **DETAILED PROMPTS** (like a human would ask):
   - Specify exact file paths, class names, method signatures
   - Include specific UI components, colors, spacing values
   - Detail the complete implementation, not just "create a screen"
   - Mention specific packages, versions, and configurations
   - Include proper error handling and edge cases

EXAMPLE OF DETAILED PROMPT:
"Create lib/features/reminder/presentation/screens/reminder_screen.dart: Build a complete reminder screen with FloatingActionButton for adding reminders, ListView.builder for displaying reminders with CheckboxListTile, proper Material 3.0 styling with primary color #2196F3, spacing of 16px between items, and RTL support. Include empty state with Icon(Icons.alarm_off) and Text('No reminders yet'). Handle loading states with CircularProgressIndicator and errors with SnackBar."

Generate 12-15 EXTREMELY DETAILED prompts that create a fully functional, polished app with working localization, no fake data, and production-ready features.

Return JSON EXACTLY with keys:
{{
  "app_name": "lowercase_snake_case_name",
  "spec": {{"theme":"light|dark","locale":"{locales[0]}", "platforms":["ios"], "features":["feature_name"]}},
  "cursor_prompts": [
    {{
      "prompt": "extremely detailed step 1 with specific files, classes, methods, UI details...",
      "validation_criteria": {{
        "file_exists": "path/to/file.dart",
        "contains_class": "ClassName",
        "has_methods": ["method1", "method2"],
        "specific_requirements": true
      }}
    }},
    {{
      "prompt": "extremely detailed step 2...",
      "validation_criteria": {{
        "file_exists": "path/to/file.dart",
        "contains_pattern": "specific content pattern",
        "functional_requirement": true
      }}
    }}
  ],
  "meta": {{"requested_locales": {json.dumps(locales)}, "bundle_id_hint": "{bundle_id}", "feature_summary": "1-line feature description"}}
}}
"""

    def call_api(body):
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)

    attempts = 0
    obj = None
    while attempts < 3:
        attempts += 1
        body = {"model": model, "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]}
        try:
            if os.environ.get('DEBUG_MODE') == '1':
                print(f"DEBUG: Attempting API call {attempts}/3 with model: {model}", file=sys.stderr)
            data = call_api(body)
            content = strip_code_fences(data["choices"][0]["message"]["content"])
            if os.environ.get('DEBUG_MODE') == '1':
                print(f"DEBUG: API response length: {len(content)}", file=sys.stderr)
            obj = json.loads(content)
            if os.environ.get('DEBUG_MODE') == '1':
                print(f"DEBUG: Parsed JSON successfully", file=sys.stderr)
        except json.JSONDecodeError as e:
            if os.environ.get('DEBUG_MODE') == '1':
                print(f"DEBUG: JSON decode error: {e}", file=sys.stderr)
                print(f"DEBUG: Content preview: {content[:200]}...", file=sys.stderr)
            if provider == 'chatgpt' and model not in ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']:
                model = 'gpt-4o-mini'
                continue
            print("LLM response was not valid JSON:", e, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            if os.environ.get('DEBUG_MODE') == '1':
                print(f"DEBUG: API call failed: {e}", file=sys.stderr)
            if provider == 'chatgpt' and model not in ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']:
                model = 'gpt-4o-mini'
                continue
            print("LLM call/parse failed:", e, file=sys.stderr)
            sys.exit(1)

        prompts = obj.get("cursor_prompts", [])
        if os.environ.get('DEBUG_MODE') == '1':
            print(f"DEBUG: Got {len(prompts)} prompts from LLM", file=sys.stderr)
        ok, why = set_is_valid(prompts)
        if os.environ.get('DEBUG_MODE') == '1':
            print(f"DEBUG: Validation result: ok={ok}, issues={why}", file=sys.stderr)
        if ok:
            break
        # corrective re-ask
        user_msg += "\n\nFix these validation issues and resend JSON only: " + ", ".join(map(str, why))
    else:
        print("Failed to obtain valid prompts after retries.", file=sys.stderr)
        sys.exit(1)

    os.makedirs("out", exist_ok=True)
    with open("out/app_spec.json", "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    with open("out/app_dir.txt", "w") as f:
        f.write((obj.get("app_name") or os.environ.get("APP_DIR", "generated_app")).strip())

    print("Provider:", provider)
    print("Model:", model)
    print("App name:", obj.get("app_name"))
    print("Prompts:", len(obj.get("cursor_prompts", [])))
    if os.environ.get('DEBUG_MODE') == '1':
        print(f"DEBUG: Final model used: {model}", file=sys.stderr)


if __name__ == "__main__":
    main()
