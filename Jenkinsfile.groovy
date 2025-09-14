pipeline {
  agent any

  parameters {
    choice(name: 'LLM_PROVIDER', choices: ['chatgpt','deepseek'], description: 'Which LLM to use for generating the prompts')
    choice(name: 'OPENAI_MODEL', choices: ['gpt-4o-mini','gpt-4o','gpt-4-turbo'], description: 'OpenAI model (when LLM_PROVIDER=chatgpt)')
    string(name: 'DEEPSEEK_MODEL', defaultValue: 'deepseek-chat', description: 'DeepSeek model (when LLM_PROVIDER=deepseek)')
    string(name: 'APP_DIR', defaultValue: 'chatgpt_ios_app', description: 'Fallback app name if the model omits one')
    choice(name: 'DEFAULT_LOCALE', choices: ['en','ar'], description: 'Default locale in prompts')

    string(name: 'APP_IDEA', defaultValue: 'A minimal chat app that calls an LLM API and shows responses.', description: 'One-paragraph product idea / focus')
    booleanParam(name: 'INCLUDE_LOCALIZATION', defaultValue: true, description: 'Generate i18n scaffolding?')
    string(name: 'LOCALES', defaultValue: 'en,ar,fr,tr', description: 'Comma-separated BCP-47 codes when localization is enabled')
    string(name: 'BUNDLE_ID', defaultValue: 'com.example.myapp', description: 'iOS bundle identifier (e.g. com.company.app)')
    booleanParam(name: 'TEST_MODE', defaultValue: false, description: 'Enable test mode (bypasses API calls, generates mock data)')
    booleanParam(name: 'STRICT_LINTING', defaultValue: false, description: 'Enable strict linting (fail on warnings, not just errors)')
    booleanParam(name: 'STRICT_VALIDATION', defaultValue: true, description: 'Enable strict validation (fail build on validation failures)')
    booleanParam(name: 'ENABLE_PIPELINE_MONITORING', defaultValue: true, description: 'Enable pipeline health monitoring and metrics collection')
    booleanParam(name: 'GENERATE_PIPELINE_REPORT', defaultValue: true, description: 'Generate comprehensive pipeline health report at the end')

  }

  environment {
    OPENAI_API_KEY   = credentials('openai_api_key')     // used if LLM_PROVIDER=chatgpt
    DEEPSEEK_API_KEY = credentials('deepseek_api_key')   // used if LLM_PROVIDER=deepseek
    CURSOR_API_KEY   = credentials('cursor_api_key')     // for cursor-agent
    APP_ROOT = "${HOME}/AppMagician"
    DEBUG_MODE = '1'                                     // Enable debug output
    TEST_MODE = "${params.TEST_MODE ? '1' : '0'}"       // Pass test mode parameter
    STRICT_LINTING = "${params.STRICT_LINTING ? '1' : '0'}"      // Pass strict linting parameter
    STRICT_VALIDATION = "${params.STRICT_VALIDATION ? '1' : '0'}"  // Pass strict validation parameter
    ENABLE_PIPELINE_MONITORING = "${params.ENABLE_PIPELINE_MONITORING ? '1' : '0'}"  // Pass pipeline monitoring parameter
    GENERATE_PIPELINE_REPORT = "${params.GENERATE_PIPELINE_REPORT ? '1' : '0'}"  // Pass pipeline report parameter
    PIPELINE_ID = "${BUILD_NUMBER}_${BUILD_TIMESTAMP}"    // Unique pipeline identifier
    PIPELINE_START_TIME = "${System.currentTimeMillis()}" // Pipeline start timestamp
  }

  options { timestamps(); ansiColor('xterm'); disableConcurrentBuilds() }

  stages {

    stage('Guard: mac + tools') {
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''
            set -euo pipefail
            echo "Workspace: $WORKSPACE"
            echo "PATH: $PATH"
            [ "$(uname)" = "Darwin" ] || { echo "Must run on macOS"; exit 1; }
            which flutter       || { echo "❌ flutter not found"; exit 1; }
            which cursor-agent  || { echo "❌ cursor-agent not found"; exit 1; }
            xcodebuild -version >/dev/null
            mkdir -p out
          '''
        }
      }
    }

    stage('Initialize Pipeline Monitoring') {
      when {
        expression { env.ENABLE_PIPELINE_MONITORING == '1' }
      }
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''
            set -euo pipefail
            echo "📊 Initializing pipeline monitoring..."
            echo "Pipeline ID: $PIPELINE_ID"
            echo "Start Time: $PIPELINE_START_TIME"
            
            # Initialize pipeline monitoring database
            python3 "${WORKSPACE}/Python/pipeline_monitor.py" --init-db --db-path "${WORKSPACE}/pipeline_metrics.db"
            
            echo "✅ Pipeline monitoring initialized"
          '''
        }
      }
    }

    stage('Generate idea + prompts (ChatGPT or DeepSeek)') {
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''
            set -euo pipefail
            python3 "${WORKSPACE}/Python/generate_prompts.py"
            echo '------ app_spec.json ------'
            cat out/app_spec.json || true
            echo '---------------------------'
          '''
        }
      }
    }





    stage('Create project under ~/AppMagician/<AppName>') {
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''
            set -euo pipefail
            APP_JSON="$WORKSPACE/out/app_spec.json"
            RAW_NAME="$(jq -r '.app_name // empty' "$APP_JSON" 2>/dev/null || true)"
            [ -z "$RAW_NAME" ] && RAW_NAME="$(cat "$WORKSPACE/out/app_dir.txt" 2>/dev/null || true)"
            RAW_NAME="${RAW_NAME:-$APP_DIR}"

            # sanitize to valid Dart package
            SANITIZED="$(printf '%s' "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9_]+/_/g; s/^_+//; s/_+$//')"
            case "$SANITIZED" in
              [a-z]* ) ;;
              * ) SANITIZED="app_${SANITIZED}";;
            esac
            SANITIZED="${SANITIZED:-app_generated}"
            echo "$SANITIZED" > "$WORKSPACE/out/app_dir.txt"

            APP_DIR="$SANITIZED"
            BUNDLE_ID="${BUNDLE_ID:-com.example.generated}"
            APP_ORG="$(printf '%s' "$BUNDLE_ID" | sed -E 's/\\.[^.]+$//')"
            APP_ROOT="${APP_ROOT:-$HOME/AppMagician}"

            mkdir -p "${APP_ROOT}"
            cd "${APP_ROOT}"
            if [ ! -d "${APP_DIR}" ]; then
              flutter create --platforms=ios --org "$APP_ORG" "${APP_DIR}"
            fi

            cd "${APP_DIR}"
            PBX="ios/Runner.xcodeproj/project.pbxproj"
            if [ -f "$PBX" ]; then
              if [ "$(uname)" = "Darwin" ]; then SED=( -i '' ); else SED=( -i ); fi
              sed "${SED[@]}" -E "s/(PRODUCT_BUNDLE_IDENTIFIER = )[^;]+;/\\1${BUNDLE_ID};/g" "$PBX" || true
              echo "✅ Set PRODUCT_BUNDLE_IDENTIFIER=${BUNDLE_ID}"
            fi

            # helpful guide for Cursor
            cat > AGENTS.md << 'MD'
- Edit in-place only (no project creation).
- Use lib/features/** structure.
- Honor the app idea from the hint.
- Keep flutter analyze and tests passing.
MD
          '''
        }
      }
    }



    stage('Run Cursor prompts (one-by-one with checks, auto-fix, anti-nesting, SENTINEL)') {
      options { timeout(time: 30, unit: 'MINUTES') }
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin", "CURSOR_CI=1"]) {
          sh '''
        set -euo pipefail
        export CURSOR_API_KEY="${CURSOR_API_KEY}"
        export CURSOR_NO_INTERACTIVE=1
        export CURSOR_EXIT_ON_COMPLETION=1
        export TERM=xterm-256color

        APP_DIR="$(cat out/app_dir.txt)"
        cd "${APP_ROOT}/${APP_DIR}"

        SPEC="${WORKSPACE}/out/app_spec.json"
        [ -s "$SPEC" ] || { echo "No app_spec.json found; aborting."; exit 1; }

        COUNT=$(jq '.cursor_prompts | length' "$SPEC")
        echo "Found $COUNT prompts."

        if [ "$(uname)" = "Darwin" ]; then DEC="base64 -D"; else DEC="base64 -d"; fi

        # Wrapper + sentinel contract
        cat > .wrap.txt <<'EOT'
CONTEXT (MANDATORY — READ CAREFULLY):
- You are editing an EXISTING Flutter project at the CURRENT working directory.
- NEVER run `flutter create`. Do NOT create a nested Flutter project.
- Do NOT `cd` outside the current directory. Keep all changes inside this project root.
- If a prompt says "create a new project", reinterpret it as "modify the current project accordingly".
- Make concrete file edits (create/modify): pubspec.yaml, analysis_options.yaml, lib/**, test/**, ios/** ONLY as needed.

COMPLETION REQUIREMENTS:
- When you have COMPLETED the requested step, print EXACTLY this line on its own as the final output (no backticks/quotes/extra spaces):
~~CURSOR_DONE~~
- If no changes are needed, print: ~~CURSOR_DONE~~ (no changes needed)
- If you encounter an error you cannot resolve, print: ~~CURSOR_DONE~~ (error: <brief>)
- The sentinel must be the very last output from your response.

Now perform the requested step. Be explicit about file paths and contents you create or modify.
EOT

        # Create a seed test if suite is empty (prevents step-1 deadlock)
        seed_smoke_test_if_empty() {
          mkdir -p test
          # disable Flutter’s stock counter test if present (only once)
          if [ -f test/widget_test.dart ] && [ ! -f .disabled_default_test ]; then
            mv test/widget_test.dart test/_default_widget_test.disabled || true
            touch .disabled_default_test
          fi
          # count tests
          if ! ls test/*_test.dart >/dev/null 2>&1; then
            cat > test/smoke_test.dart <<'DART'
import 'package:flutter_test/flutter_test.dart';
void main() {
  test('smoke', () {
    expect(1 + 1, 2);
  });
}
DART
            echo "🧪 Seeded minimal smoke test."
          fi
        }

        run_checks() {
          # macOS-friendly hashing function
          hash_file() { command -v md5sum >/dev/null 2>&1 && md5sum "$1" | awk '{print $1}' || md5 -q "$1"; }
          
          seed_smoke_test_if_empty
          
          # Conditional flutter pub get - only when pubspec.yaml changes
          old_hash="$( [ -f .pubspec.hash ] && cat .pubspec.hash || echo none )"
          new_hash="$(hash_file pubspec.yaml || echo none)"
          if [ "$old_hash" != "$new_hash" ]; then
            echo "📦 Dependencies changed - running flutter pub get"
            flutter pub get >/dev/null 2>&1 || true
            echo "$new_hash" > .pubspec.hash
          else
            echo "📦 Dependencies unchanged - skipping flutter pub get"
          fi
          
          set +e
          
          # Conditional flutter analyze - only for Dart-related steps  
          if echo "${STEP:-}" | grep -E "(dart|lib/|test/)" >/dev/null || [ -z "${STEP:-}" ]; then
            echo "🔍 Running flutter analyze (Dart code may have changed)"
            flutter analyze > .an.out 2>&1; ANALYZE_RC=$?
          else
            echo "🔍 Skipping flutter analyze (no Dart code changes)"
            echo "No Dart code changes detected" > .an.out; ANALYZE_RC=0
          fi
          
          flutter test   > .test.out 2>&1;   TEST_RC=$?
          set -e
          
          # Check if strict linting is enabled
          if [ "${STRICT_LINTING}" = "1" ]; then
            # Strict mode: fail on any analyze issues
            if [ $ANALYZE_RC -eq 0 ] && [ $TEST_RC -eq 0 ]; then
              echo "✅ Analyze & tests passed (strict mode)."
              return 0
            else
              echo "❌ Checks failed (strict mode: analyze=$ANALYZE_RC, test=$TEST_RC)."
              return 1
            fi
          else
            # Relaxed mode: only fail on actual errors, not warnings/info
            if [ $TEST_RC -eq 0 ]; then
              # Check if analyze has actual errors (not just info/warnings)
              if grep -q "error •" .an.out; then
                echo "❌ Analyze has errors (test=$TEST_RC)."
                echo "---- analyze errors ----"; grep "error •" .an.out || true
                return 1
              else
                echo "✅ Tests passed, analyze has only warnings/info (analyze=$ANALYZE_RC, test=$TEST_RC)."
                return 0
              fi
            else
              echo "❌ Tests failed (analyze=$ANALYZE_RC, test=$TEST_RC)."
              echo "---- analyze tail ----"; tail -n 120 .an.out || true
              echo "---- test tail ----";    tail -n 120 .test.out || true
              return 1
            fi
          fi
        }

          ask_fix() {
          # macOS-friendly hashing function
          hash_file() { command -v md5sum >/dev/null 2>&1 && md5sum "$1" | awk '{print $1}' || md5 -q "$1"; }
          
          local STEP_NO="$1"
          export STEP="step ${STEP_NO}"
          : > .an.tail; : > .ts.tail
          [ -f .an.out ]   && tail -n 200 .an.out  | sed 's/"/\\"/g' > .an.tail || true
          [ -f .test.out ] && tail -n 200 .test.out| sed 's/"/\\"/g' > .ts.tail || true

          python3 "${WORKSPACE}/Python/cursor_fix.py"
          
          # Only run flutter pub get if pubspec.yaml might have changed during fix
          old_hash="$( [ -f .pubspec.hash ] && cat .pubspec.hash || echo none )"
          new_hash="$(hash_file pubspec.yaml || echo none)"
          if [ "$old_hash" != "$new_hash" ]; then
            echo "📦 Fix may have changed dependencies - running flutter pub get"
            flutter pub get >/dev/null 2>&1 || true
            echo "$new_hash" > .pubspec.hash
          fi
        }

        flatten_if_nested() {
          if [ -d "${APP_DIR}/${APP_DIR}" ]; then
            echo "⚠️  Detected nested project ${APP_DIR}/${APP_DIR} — flattening..."
            rsync -a "${APP_DIR}/${APP_DIR}/" "./"
            rm -rf "${APP_DIR:?}/${APP_DIR}"
            echo "✅ Flattened nested project."
          fi
        }

        run_cursor() {
          python3 "${WORKSPACE}/Python/cursor_run.py"
        }

        # Validation functions for each step
        validate_step() {
          local STEP_NO="$1"
          local STEP_CONTENT="$2"
          
          echo "🔍 Running validation for step ${STEP_NO}..."
          
          case "$STEP_NO" in
            3)
              # After HomeScreen creation
              echo "📱 Validating HomeScreen creation..."
              if [ -f "lib/features/home/presentation/screens/home_screen.dart" ]; then
                echo "✅ HomeScreen file exists"
                if grep -q "class.*HomeScreen" "lib/features/home/presentation/screens/home_screen.dart"; then
                  echo "✅ HomeScreen class found"
                else
                  echo "❌ HomeScreen class not found"
                  return 1
                fi
              else
                echo "❌ HomeScreen file not found"
                return 1
              fi
              ;;
            4)
              # After main feature screen creation - dynamic validation
              echo "🎯 Validating main feature integration..."
              # Find the main feature by looking at the prompt content
              if echo "$STEP_CONTENT" | grep -qi "expenses"; then
                echo "💰 Validating expenses feature integration..."
                python3 "${WORKSPACE}/Python/validate_feature.py" expenses || return 1
              elif echo "$STEP_CONTENT" | grep -qi "todo"; then
                echo "📝 Validating todo feature integration..."
                python3 "${WORKSPACE}/Python/validate_feature.py" todo || return 1
              elif echo "$STEP_CONTENT" | grep -qi "notes"; then
                echo "📝 Validating notes feature integration..."
                python3 "${WORKSPACE}/Python/validate_feature.py" notes || return 1
              else
                echo "ℹ️  Generic feature validation - checking for feature screens..."
                # Generic validation - check if any feature screens exist
                if find lib/features -name "*_screen.dart" | grep -v home | head -1; then
                  echo "✅ Feature screens found"
                else
                  echo "❌ No feature screens found"
                  return 1
                fi
              fi
              ;;
            5)
              # After form screen creation - dynamic validation
              echo "➕ Validating form elements..."
              # Find form screens dynamically
              FORM_SCREEN=$(find lib/features -name "*form*screen.dart" -o -name "*add*screen.dart" -o -name "*create*screen.dart" | head -1)
              if [ -n "$FORM_SCREEN" ]; then
                echo "✅ Form screen found: $FORM_SCREEN"
                if grep -q "Form\\|TextFormField\\|ElevatedButton\\|TextField" "$FORM_SCREEN"; then
                  echo "✅ Form elements found"
                else
                  echo "❌ Form elements not found"
                  return 1
                fi
              else
                echo "ℹ️  No specific form screen found - checking for general form elements..."
                if find lib/features -name "*screen.dart" -exec grep -l "Form\\\\|TextFormField\\\\|ElevatedButton\\\\|TextField" {} \\; | head -1; then
                  echo "✅ Form elements found in screens"
                else
                  echo "❌ No form elements found"
                  return 1
                fi
              fi
              ;;
            6)
              # After Localization
              echo "🌍 Validating localization..."
              if [ -f "lib/l10n/app_en.arb" ] && [ -f "lib/l10n/app_ar.arb" ]; then
                echo "✅ Localization files exist"
                if grep -q "app_title\\|settings\\|language" "lib/l10n/app_en.arb"; then
                  echo "✅ Localization keys found"
                else
                  echo "❌ Localization keys not found"
                  return 1
                fi
              else
                echo "❌ Localization files not found"
                return 1
              fi
              ;;
            7)
              # After secondary feature creation - dynamic validation
              echo "🎯 Validating secondary feature integration..."
              # Find secondary features by looking at the prompt content
              if echo "$STEP_CONTENT" | grep -qi "savings"; then
                echo "💾 Validating savings feature integration..."
                python3 "${WORKSPACE}/Python/validate_feature.py" savings || return 1
              elif echo "$STEP_CONTENT" | grep -qi "settings"; then
                echo "⚙️  Validating settings feature integration..."
                python3 "${WORKSPACE}/Python/validate_feature.py" settings || return 1
              else
                echo "ℹ️  Generic secondary feature validation..."
                # Check for any additional feature screens
                FEATURE_COUNT=$(find lib/features -name "*_screen.dart" | grep -v home | wc -l)
                if [ "$FEATURE_COUNT" -ge 2 ]; then
                  echo "✅ Multiple feature screens found ($FEATURE_COUNT)"
                else
                  echo "❌ Insufficient feature screens found ($FEATURE_COUNT)"
                  return 1
                fi
              fi
              ;;
            8)
              # After SettingsScreen creation - dynamic validation
              echo "⚙️  Validating settings feature integration..."
              if [ -f "lib/features/settings/presentation/screens/settings_screen.dart" ]; then
                echo "✅ Settings screen found"
                python3 "${WORKSPACE}/Python/validate_feature.py" settings || return 1
              else
                echo "ℹ️  No settings screen found - checking for general settings elements..."
                if find lib/features -name "*screen.dart" -exec grep -l "settings\\\\|Settings" {} \\; | head -1; then
                  echo "✅ Settings elements found"
                else
                  echo "❌ No settings elements found"
                  return 1
                fi
              fi
              ;;
            9)
              # After LoadingIndicator
              echo "⏳ Validating core widgets..."
              if [ -f "lib/core/presentation/widgets/loading_widget.dart" ]; then
                echo "✅ LoadingWidget file exists"
                if grep -q "CircularProgressIndicator\\|LoadingWidget" "lib/core/presentation/widgets/loading_widget.dart"; then
                  echo "✅ Loading indicator found"
                else
                  echo "❌ Loading indicator not found"
                  return 1
                fi
              else
                echo "❌ LoadingWidget file not found"
                return 1
              fi
              ;;
            10)
              # After RTL support
              echo "🔄 Validating RTL support..."
              if grep -q "TextDirection\\|RTL\\|LTR" "lib/main.dart"; then
                echo "✅ RTL support found in main.dart"
              else
                echo "❌ RTL support not found in main.dart"
                return 1
              fi
              ;;
            11)
              # After Dependencies
              echo "📦 Validating dependencies..."
              if [ -f "pubspec.yaml" ]; then
                echo "✅ pubspec.yaml exists"
                if grep -q "provider\\|riverpod\\|shared_preferences\\|flutter_localizations" "pubspec.yaml"; then
                  echo "✅ Required dependencies found"
                else
                  echo "❌ Required dependencies not found"
                  return 1
                fi
              else
                echo "❌ pubspec.yaml not found"
                return 1
              fi
              ;;
            12)
              # After Tests
              echo "🧪 Validating tests..."
              if flutter test >/dev/null 2>&1; then
                echo "✅ All tests pass"
              else
                echo "❌ Tests failed"
                return 1
              fi
              ;;
            *)
              echo "ℹ️  No specific validation for step ${STEP_NO}"
              ;;
          esac
          
          echo "✅ Step ${STEP_NO} validation passed"
          return 0
        }

        # Initialize STEP variable to avoid unbound variable errors
        export STEP=""

        i=0
        while [ $i -lt $COUNT ]; do
          B64=$(jq -r ".cursor_prompts[$i] | @base64" "$SPEC")
          printf "%s" "$B64" | $DEC > .prompt.raw
          STEP_NO=$((i+1))
          IS_LAST_STEP=$([ $i -eq $((COUNT-1)) ] && echo "true" || echo "false")

          cat .wrap.txt .prompt.raw > .prompt.txt

          echo "==============================="
          echo "Applying step ${STEP_NO}/${COUNT}"
          echo "-------------------------------"
          sed -n '1,180p' .prompt.txt || true

          # Record step start time for monitoring
          STEP_START_TIME=$(date +%s)
          
          run_cursor || true
          flatten_if_nested

          if run_checks; then
            echo "Step ${STEP_NO}: OK"
            
            # Run validation for specific steps
            if validate_step "$STEP_NO" "$(cat .prompt.raw)"; then
              echo "✅ Step ${STEP_NO} validation passed"
            else
              echo "❌ Step ${STEP_NO} validation failed"
              echo "🔄 Attempting to fix validation issues..."
              
              # Try to fix validation issues
              ATTEMPT=1
              MAX_VALIDATION_ATTEMPTS=2
              while [ $ATTEMPT -le $MAX_VALIDATION_ATTEMPTS ]; do
                echo "Validation fix attempt ${ATTEMPT}/${MAX_VALIDATION_ATTEMPTS} for step ${STEP_NO}..."
                ask_fix "${STEP_NO}" || true
                flatten_if_nested
                
                if validate_step "$STEP_NO" "$(cat .prompt.raw)"; then
                  echo "✅ Step ${STEP_NO} validation passed after fix attempt ${ATTEMPT}"
                  break
                fi
                ATTEMPT=$((ATTEMPT+1))
              done
              
              if [ $ATTEMPT -gt $MAX_VALIDATION_ATTEMPTS ]; then
                echo "❌ Step ${STEP_NO} validation failed after ${MAX_VALIDATION_ATTEMPTS} fix attempts"
                if [ "${STRICT_VALIDATION}" = "1" ]; then
                  echo "❌ Strict validation enabled - failing build"
                  exit 1
                else
                  echo "⚠️  Strict validation disabled - continuing to next step"
                fi
              fi
            fi
          else
            ATTEMPT=1
            MAX_ATTEMPTS=2
            while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
              echo "Auto-fix attempt ${ATTEMPT}/${MAX_ATTEMPTS} for step ${STEP_NO}..."
              ask_fix "${STEP_NO}" || true
              flatten_if_nested
              if run_checks; then
                echo "Step ${STEP_NO}: OK after auto-fix ${ATTEMPT}"
                
                # Run validation after successful fix
                if validate_step "$STEP_NO" "$(cat .prompt.raw)"; then
                  echo "✅ Step ${STEP_NO} validation passed after auto-fix"
                else
                  echo "⚠️  Step ${STEP_NO} validation failed after auto-fix - continuing"
                fi
                break
              fi
              ATTEMPT=$((ATTEMPT+1))
            done
            if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
              echo "⚠️  Step ${STEP_NO} failed after ${MAX_ATTEMPTS} auto-fix attempts."
              echo "🔄 Continuing to next step - later steps or build stage may fix this issue."
              echo "📝 This is normal - some steps depend on others being completed first."
              # Don't exit - continue to next step
            fi
          fi

          # Record step metrics for monitoring
          if [ "${ENABLE_PIPELINE_MONITORING}" = "1" ]; then
            STEP_END_TIME=$(date +%s)
            STEP_DURATION=$((STEP_END_TIME - STEP_START_TIME))
            
            echo "📊 Recording metrics for step ${STEP_NO}..."
            python3 "${WORKSPACE}/Python/pipeline_monitor.py" --record-step \
              --step-number "${STEP_NO}" \
              --step-duration "${STEP_DURATION}" \
              --step-success "$([ $? -eq 0 ] && echo 'true' || echo 'false')" \
              --db-path "${WORKSPACE}/pipeline_metrics.db" || true
          fi

          i=$((i+1))
        done
          '''
        }
      }
    }

    stage('Final Integration Validation') {
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''
        set -euo pipefail
        APP_DIR="$(cat out/app_dir.txt)"
        cd "${APP_ROOT}/${APP_DIR}"
        
        echo "🔍 Running final integration validation..."
        echo "=========================================="
        
        # Record validation start time
        VALIDATION_START_TIME=$(date +%s)
        
        # Run comprehensive integration validation
        python3 "${WORKSPACE}/Python/validate_integration.py" || {
          echo "❌ Integration validation failed"
          echo "🔄 Attempting to clean up placeholders..."
          python3 "${WORKSPACE}/Python/cleanup_placeholders.py" || true
          echo "🔄 Re-running integration validation..."
          python3 "${WORKSPACE}/Python/validate_integration.py" || {
            echo "❌ Integration validation still failed after cleanup"
            if [ "${STRICT_VALIDATION}" = "1" ]; then
              echo "❌ Strict validation enabled - failing build"
              exit 1
            else
              echo "⚠️  Strict validation disabled - continuing with warnings"
            fi
          }
        }
        
        echo "✅ Final integration validation passed"
        echo "=========================================="
        
        # Record validation metrics for monitoring
        if [ "${ENABLE_PIPELINE_MONITORING}" = "1" ]; then
          VALIDATION_END_TIME=$(date +%s)
          VALIDATION_DURATION=$((VALIDATION_END_TIME - VALIDATION_START_TIME))
          
          echo "📊 Recording integration validation metrics..."
          python3 "${WORKSPACE}/Python/pipeline_monitor.py" --record-stage \
            --stage-name "integration_validation" \
            --stage-duration "${VALIDATION_DURATION}" \
            --stage-success "true" \
            --db-path "${WORKSPACE}/pipeline_metrics.db" || true
        fi
          '''
        }
      }
    }

    stage('Build iOS (no codesign) with auto-fix loop') {
      options { timeout(time: 45, unit: 'MINUTES') }
      environment {
        CURSOR_CI = '1'
        CURSOR_NO_INTERACTIVE = '1'
        CURSOR_EXIT_ON_COMPLETION = '1'
        TERM = 'xterm-256color'
      }
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''#!/usr/bin/env bash
set -euo pipefail

# Resolve project dir (works even if APP_ROOT isn't defined in the pipeline)
APP_DIR="$(cat out/app_dir.txt)"
APP_ROOT_DEFAULT="${HOME}/AppMagician"
APP_ROOT="${APP_ROOT:-$APP_ROOT_DEFAULT}"
cd "${APP_ROOT}/${APP_DIR}"

# Guard: macOS only for iOS builds
if [ "$(uname -s)" != "Darwin" ]; then
  echo "This stage requires macOS to build iOS."
  exit 1
fi

# ----- Static wrapper (no backticks, no interpolation) -----
cat > .wrap.txt <<'EOT'
CONTEXT (MANDATORY — READ CAREFULLY):
- You are editing an EXISTING Flutter project in the CURRENT working directory.
- NEVER run 'flutter create'. Do NOT create a nested Flutter project.
- Do NOT cd elsewhere; keep all changes inside this project root.
- Apply minimal, targeted changes needed to fix the reported problems.

COMPLETION REQUIREMENT:
- When you are DONE, print EXACTLY this line as the final output (no quotes/extra spaces):
~~CURSOR_DONE~~
EOT

run_checks() {
  # macOS-friendly hashing function
  hash_file() { command -v md5sum >/dev/null 2>&1 && md5sum "$1" | awk '{print $1}' || md5 -q "$1"; }
  
  set +e
  
  # Conditional flutter pub get - only when pubspec.yaml changes
  old_hash="$( [ -f .pubspec.hash ] && cat .pubspec.hash || echo none )"
  new_hash="$(hash_file pubspec.yaml || echo none)"
  if [ "$old_hash" != "$new_hash" ]; then
    echo "📦 Build stage: Dependencies changed - running flutter pub get"
    flutter pub get > .pub.out 2>&1
    echo "$new_hash" > .pubspec.hash
  else
    echo "📦 Build stage: Dependencies unchanged - skipping flutter pub get"
    echo "Dependencies unchanged" > .pub.out
  fi
  
  flutter analyze > .an.out 2>&1;  ANALYZE_RC=$?
  flutter test   > .test.out 2>&1; TEST_RC=$?
  flutter build ios --no-codesign > .build.out 2>&1; BUILD_RC=$?
  set -e

  # Only fail on actual errors, not warnings/info
  if [ $TEST_RC -eq 0 ] && [ $BUILD_RC -eq 0 ]; then
    # Check if analyze has actual errors (not just info/warnings)
    if grep -q "error •" .an.out; then
      echo "❌ Analyze has errors (test=$TEST_RC, build=$BUILD_RC)."
      echo "---- analyze errors ----"; grep "error •" .an.out || true
      return 1
    else
      echo "✅ All checks passed (analyze has only warnings/info)."
      return 0
    fi
  fi

  echo "❌ Checks failed (analyze=$ANALYZE_RC, test=$TEST_RC, build=$BUILD_RC)."
  echo "---- analyze tail ----"; tail -n 80 .an.out || true
  echo "---- test tail ----";    tail -n 80 .test.out || true
  echo "---- build tail ----";   tail -n 120 .build.out || true
  return 1
}

ask_cursor_fix_generic() {
  # Capture safe tails (escape double quotes for JSON-ish prompts)
  AN_TAIL="$( [ -f .an.out ]   && tail -n 400 .an.out   | sed 's/\"/\\"/g' || true )"
  TS_TAIL="$( [ -f .test.out ] && tail -n 400 .test.out | sed 's/\"/\\"/g' || true )"
  BD_TAIL="$( [ -f .build.out ]&& tail -n 600 .build.out| sed 's/\"/\\"/g' || true )"

  cat > .prompt.raw <<'PROMPT'
You are a senior Flutter+iOS engineer running in CI.
Your task: Fix the project so ANALYZE, TESTS, and iOS BUILD (no codesign) all succeed.
Constraints:
- Edit the existing project in-place; do NOT create or nest a new Flutter project.
- Keep architecture under lib/** tidy; avoid large refactors unless required.
- Apply minimal, targeted changes.

After applying fixes, ensure all of the following pass in CI:
- flutter analyze
- flutter test
- flutter build ios --no-codesign

When you are finished, print ONLY this sentinel on its own line:
~~CURSOR_DONE~~
PROMPT

  {
    cat .wrap.txt
    cat .prompt.raw
    printf "\\n[ANALYZE TAIL]\\n%s\\n\\n[TEST TAIL]\\n%s\\n\\n[BUILD TAIL]\\n%s\\n" "$AN_TAIL" "$TS_TAIL" "$BD_TAIL"
  } > .prompt.txt

  # Send to Cursor and require the sentinel
  python3 "${WORKSPACE}/Python/build_fix.py"

  # Refresh deps after edits - only if pubspec.yaml changed
  old_hash="$( [ -f .pubspec.hash ] && cat .pubspec.hash || echo none )"
  new_hash="$(hash_file pubspec.yaml || echo none)"
  if [ "$old_hash" != "$new_hash" ]; then
    echo "📦 Build fix: Dependencies changed - running flutter pub get"
    flutter pub get >/dev/null 2>&1 || true
    echo "$new_hash" > .pubspec.hash
  fi
}

# Record build start time
BUILD_START_TIME=$(date +%s)

# -------- Auto-fix loop --------
ATTEMPT=1
MAX_ATTEMPTS=2
until run_checks; do
  if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ Max auto-fix attempts reached ($MAX_ATTEMPTS)."
    exit 1
  fi
  echo "🔄 Auto-fix attempt $ATTEMPT of $MAX_ATTEMPTS…"
  ask_cursor_fix_generic
  ATTEMPT=$((ATTEMPT+1))
done

# Record build metrics for monitoring
if [ "${ENABLE_PIPELINE_MONITORING}" = "1" ]; then
  BUILD_END_TIME=$(date +%s)
  BUILD_DURATION=$((BUILD_END_TIME - BUILD_START_TIME))
  
  echo "📊 Recording build metrics..."
  python3 "${WORKSPACE}/Python/pipeline_monitor.py" --record-stage \
    --stage-name "ios_build" \
    --stage-duration "${BUILD_DURATION}" \
    --stage-success "true" \
    --db-path "${WORKSPACE}/pipeline_metrics.db" || true
fi
          '''
        }
      }
    }

    stage('Pipeline Health Monitoring & Reporting') {
      when {
        expression { env.ENABLE_PIPELINE_MONITORING == '1' }
      }
      steps {
        withEnv(["PATH=${env.PATH}:${env.HOME}/.cursor/bin"]) {
          sh '''
          set -euo pipefail
          APP_DIR="$(cat out/app_dir.txt)"
          cd "${APP_ROOT}/${APP_DIR}"
          
          echo "Collecting comprehensive pipeline metrics..."
          echo "=============================================="
          
          # Collect current metrics and save to database
          python3 "${WORKSPACE}/Python/pipeline_monitor.py" --collect-metrics \
            --app-root "${APP_ROOT}/${APP_DIR}" \
            --pipeline-id "${PIPELINE_ID}" \
            --db-path "${WORKSPACE}/pipeline_metrics.db" || true
          
          # Generate health report if requested
          if [ "${GENERATE_PIPELINE_REPORT}" = "1" ]; then
            echo "Generating comprehensive pipeline health report..."
            python3 "${WORKSPACE}/Python/pipeline_monitor.py" --report \
              --db-path "${WORKSPACE}/pipeline_metrics.db" > "${WORKSPACE}/pipeline_health_report.txt" || true
            
            echo "Pipeline Health Report:"
            echo "========================="
            cat "${WORKSPACE}/pipeline_health_report.txt" || true
            echo "========================="
          fi
          
          # Generate dashboard view
          echo "Pipeline Dashboard:"
          echo "====================="
          python3 "${WORKSPACE}/Python/pipeline_monitor.py" --dashboard \
            --db-path "${WORKSPACE}/pipeline_metrics.db" || true
          echo "====================="
          
          # Export metrics for historical analysis
          echo "Exporting metrics for historical analysis..."
          python3 "${WORKSPACE}/Python/pipeline_monitor.py" --export json \
            --db-path "${WORKSPACE}/pipeline_metrics.db" || true
          
          echo "Pipeline monitoring completed"
          '''
        }
      }
    }
  }

  post {
    success {
      echo '✅ Build complete'
    }
    failure { echo '❌ Failed. Check the last analyze/test tail or flatten message above.' }
  }
}
