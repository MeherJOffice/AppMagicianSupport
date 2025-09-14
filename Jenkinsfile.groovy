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

  }

  environment {
    OPENAI_API_KEY   = credentials('openai_api_key')     // used if LLM_PROVIDER=chatgpt
    DEEPSEEK_API_KEY = credentials('deepseek_api_key')   // used if LLM_PROVIDER=deepseek
    CURSOR_API_KEY   = credentials('cursor_api_key')     // for cursor-agent
    APP_ROOT = "${HOME}/AppMagician"
    DEBUG_MODE = '1'                                     // Enable debug output
    TEST_MODE = "${params.TEST_MODE ? '1' : '0'}"       // Pass test mode parameter
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
          seed_smoke_test_if_empty
          
          # Conditional flutter pub get - only when pubspec.yaml changes
          if [ -f pubspec.yaml ] && [ .pubspec.hash != "$(md5sum pubspec.yaml 2>/dev/null || echo 'no-hash')" ]; then
            echo "📦 Dependencies changed - running flutter pub get"
            flutter pub get >/dev/null 2>&1 || true
            md5sum pubspec.yaml > .pubspec.hash 2>/dev/null || true
          else
            echo "📦 Dependencies unchanged - skipping flutter pub get"
          fi
          
          set +e
          
          # Conditional flutter analyze - only for Dart-related steps
          if [[ "${STEP:-}" =~ (dart|lib/|test/) ]] || [ -z "${STEP:-}" ]; then
            echo "🔍 Running flutter analyze (Dart code may have changed)"
            flutter analyze > .an.out 2>&1; ANALYZE_RC=$?
          else
            echo "🔍 Skipping flutter analyze (no Dart code changes)"
            echo "No Dart code changes detected" > .an.out; ANALYZE_RC=0
          fi
          
          flutter test   > .test.out 2>&1;   TEST_RC=$?
          set -e
          
          # Check if strict linting is enabled
          if [ "${STRICT_LINTING}" = "true" ]; then
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
          local STEP_NO="$1"
          export STEP="step ${STEP_NO}"
          : > .an.tail; : > .ts.tail
          [ -f .an.out ]   && tail -n 200 .an.out  | sed 's/"/\\"/g' > .an.tail || true
          [ -f .test.out ] && tail -n 200 .test.out| sed 's/"/\\"/g' > .ts.tail || true

          python3 "${WORKSPACE}/Python/cursor_fix.py"
          
          # Only run flutter pub get if pubspec.yaml might have changed during fix
          if [ -f pubspec.yaml ] && [ .pubspec.hash != "$(md5sum pubspec.yaml 2>/dev/null || echo 'no-hash')" ]; then
            echo "📦 Fix may have changed dependencies - running flutter pub get"
            flutter pub get >/dev/null 2>&1 || true
            md5sum pubspec.yaml > .pubspec.hash 2>/dev/null || true
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

          run_cursor || true
          flatten_if_nested

          if run_checks; then
            echo "Step ${STEP_NO}: OK"
          else
            ATTEMPT=1
            MAX_ATTEMPTS=2
            while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
              echo "Auto-fix attempt ${ATTEMPT}/${MAX_ATTEMPTS} for step ${STEP_NO}..."
              ask_fix "${STEP_NO}" || true
              flatten_if_nested
              if run_checks; then
                echo "Step ${STEP_NO}: OK after auto-fix ${ATTEMPT}"
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

          i=$((i+1))
        done
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
  set +e
  
  # Conditional flutter pub get - only when pubspec.yaml changes
  if [ -f pubspec.yaml ] && [ .pubspec.hash != "$(md5sum pubspec.yaml 2>/dev/null || echo 'no-hash')" ]; then
    echo "📦 Build stage: Dependencies changed - running flutter pub get"
    flutter pub get > .pub.out 2>&1
    md5sum pubspec.yaml > .pubspec.hash 2>/dev/null || true
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
  if [ -f pubspec.yaml ] && [ .pubspec.hash != "$(md5sum pubspec.yaml 2>/dev/null || echo 'no-hash')" ]; then
    echo "📦 Build fix: Dependencies changed - running flutter pub get"
    flutter pub get >/dev/null 2>&1 || true
    md5sum pubspec.yaml > .pubspec.hash 2>/dev/null || true
  fi
}

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
'''
    }
  }
}



  }

  post {
    success {
      sh '''
        set -euo pipefail
        APP_DIR="$(cat out/app_dir.txt)"
        DEST="${APP_ROOT}/${APP_DIR}"
        echo "✅ Build complete in: $DEST"
        open "$DEST" || true
      '''
    }
    failure { echo '❌ Failed. Check the last analyze/test tail or flatten message above.' }
  }
}
