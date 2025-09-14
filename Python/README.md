# Python Scripts for AppMagician Pipeline

This folder contains Python scripts that were extracted from the Jenkins pipeline to improve maintainability and code organization.

## Scripts

### `generate_prompts.py`
- **Purpose**: Generates app specifications and prompts using ChatGPT or DeepSeek APIs
- **Usage**: Called by Jenkins pipeline to create app specifications based on user input
- **Environment Variables**:
  - `LLM_PROVIDER`: 'chatgpt' or 'deepseek'
  - `OPENAI_MODEL`: OpenAI model name (when using ChatGPT)
  - `DEEPSEEK_MODEL`: DeepSeek model name (when using DeepSeek)
  - `OPENAI_API_KEY`: API key for OpenAI (when using ChatGPT)
  - `DEEPSEEK_API_KEY`: API key for DeepSeek (when using DeepSeek)
  - `APP_IDEA`: App idea/prompt hint
  - `BUNDLE_ID`: iOS bundle identifier
  - `LOCALES`: Comma-separated locale codes
  - `DEFAULT_LOCALE`: Default locale
  - `TEST_MODE`: Set to '1' for testing without API keys (generates mock response)
  - `DEBUG_MODE`: Set to '1' to enable debug output

### `cursor_fix.py`
- **Purpose**: Automatically fixes Flutter analyze and test issues using cursor-agent
- **Usage**: Called when previous pipeline steps introduce issues
- **Environment Variables**:
  - `STEP`: Current step number for context
  - `CURSOR_API_KEY`: API key for cursor-agent
  - `CURSOR_CI`: Set to '1' for CI mode
  - `CURSOR_NO_INTERACTIVE`: Set to '1' for non-interactive mode

### `cursor_run.py`
- **Purpose**: Executes cursor-agent with prompts and handles output with sentinel detection
- **Usage**: Runs cursor-agent for each step in the pipeline
- **Environment Variables**:
  - `CURSOR_API_KEY`: API key for cursor-agent
  - `CURSOR_CI`: Set to '1' for CI mode
  - `CURSOR_NO_INTERACTIVE`: Set to '1' for non-interactive mode

### `build_fix.py`
- **Purpose**: Automatically fixes Flutter build issues using cursor-agent
- **Usage**: Called when iOS build fails to apply fixes
- **Environment Variables**:
  - `CURSOR_API_KEY`: API key for cursor-agent

### `validate_integration.py`
- **Purpose**: Validates that all features are properly integrated in the Flutter app
- **Usage**: Called from Jenkins pipeline to check app integration
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Validation Checks**:
  - App structure and required directories
  - Feature screen imports and file existence
  - Provider usage in screens
  - Screen implementations and required elements
  - File locations and core files
  - Duplicate screen implementations
  - Routing integration
- **Exit Codes**:
  - `0`: All validations passed
  - `1`: Validation failures found

### `validate_feature.py`
- **Purpose**: Validates individual features for proper structure and integration
- **Usage**: Command line tool to check specific features
- **Arguments**:
  - `feature_name`: Name of the feature to validate (required)
  - `--app-root`: Path to app root directory (optional)
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Validation Checks**:
  - Feature directory exists in `lib/features/{feature}/`
  - Proper structure: `data/`, `domain/`, `presentation/`
  - Has `data/providers/`, `domain/models/`, `presentation/screens/`
  - Screens use providers (`ref.watch({feature}Provider)`)
  - HomeScreen imports correct screens from the feature
  - No placeholder screens exist
  - Feature integration in `main.dart` and `pubspec.yaml`
- **Exit Codes**:
  - `0`: All validations passed
  - `1`: Validation failures found
- **Examples**:
  ```bash
  python3 Python/validate_feature.py expenses
  python3 Python/validate_feature.py savings --app-root /path/to/app
  ```

### `cleanup_placeholders.py`
- **Purpose**: Removes placeholder files after real implementations are in place
- **Usage**: Command line tool to clean up placeholder content
- **Arguments**:
  - `--app-root`: Path to app root directory (optional)
  - `--verbose`: Enable verbose output (optional)
  - `--dry-run`: Show what would be removed without actually removing files (optional)
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Cleanup Actions**:
  - Remove placeholder screens from home feature
  - Keep only `dashboard_screen.dart` and `home_screen.dart` in home
  - Remove duplicate files
  - Remove empty or minimal content files
  - Remove conflicting files (`*_old.dart`, `*_backup.dart`, etc.)
  - Create backups before removal
- **Safety Features**:
  - Never removes essential files (`main.dart`, `pubspec.yaml`, etc.)
  - Never removes files in platform directories (`ios/`, `android/`, etc.)
  - Creates backups before removal
  - Verifies real implementations exist before removing placeholders
  - Logs all actions for transparency
- **Exit Codes**:
  - `0`: Cleanup completed successfully
  - `1`: Cleanup completed with errors
- **Examples**:
  ```bash
  python3 Python/cleanup_placeholders.py
  python3 Python/cleanup_placeholders.py --dry-run
  python3 Python/cleanup_placeholders.py --verbose
  ```

### `quality_gates.py`
- **Purpose**: Runs comprehensive quality checks for Flutter iOS apps
- **Usage**: Command line tool to validate app quality
- **Arguments**:
  - `--app-root`: Path to app root directory (optional)
  - `--min-coverage`: Minimum test coverage percentage (default: 70.0)
  - `--json-output`: Output results to JSON file (optional)
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Quality Checks**:
  - Flutter analyze (errors only, not warnings)
  - Flutter tests (all tests must pass)
  - Test coverage (minimum threshold)
  - Dependencies (all resolved)
  - Build success (iOS build --no-codesign)
  - Localization files (properly generated)
  - Hardcoded strings (none found)
  - Provider initialization (properly configured)
- **Exit Codes**:
  - `0`: All quality gates passed
  - `1`: One or more quality gates failed
- **Examples**:
  ```bash
  python3 Python/quality_gates.py
  python3 Python/quality_gates.py --min-coverage 80
  python3 Python/quality_gates.py --json-output report.json
  ```

### `validate_navigation.py`
- **Purpose**: Validates Flutter app navigation flow and structure
- **Usage**: Command line tool to check navigation implementation
- **Arguments**:
  - `--app-root`: Path to app root directory (optional)
  - `--verbose`: Enable verbose output (optional)
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Navigation Validation Checks**:
  - HomeScreen navigation structure (not IndexedStack)
  - Navigation destinations properly defined
  - Navigation icons and labels correctly set
  - Navigation state management working
  - No navigation-related memory leaks
  - Proper keyboard handling
  - Navigation animations working correctly
- **Exit Codes**:
  - `0`: All navigation validations passed
  - `1`: Navigation validation failures found
- **Examples**:
  ```bash
  python3 Python/validate_navigation.py
  python3 Python/validate_navigation.py --verbose
  python3 Python/validate_navigation.py --app-root /path/to/app
  ```

### `verify_build.py`
- **Purpose**: Verifies Flutter app builds correctly across all platforms
- **Usage**: Command line tool to check build process and artifacts
- **Arguments**:
  - `--app-root`: Path to app root directory (optional)
  - `--verbose`: Enable verbose output (optional)
  - `--skip-ios`: Skip iOS build verification (optional)
  - `--skip-tests`: Skip test execution (optional)
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Build Verification Checks**:
  - Flutter clean (clean build environment)
  - Flutter pub get (dependency resolution)
  - Flutter analyze (compilation errors)
  - Flutter test (all tests pass)
  - iOS build (iOS app generation, macOS only)
  - Generated files (essential build artifacts)
  - App installation (file integrity)
- **Exit Codes**:
  - `0`: All build verification checks passed
  - `1`: One or more build verification checks failed
- **Examples**:
  ```bash
  python3 Python/verify_build.py
  python3 Python/verify_build.py --skip-tests
  python3 Python/verify_build.py --skip-ios --verbose
  python3 Python/verify_build.py --app-root /path/to/app
  ```

### `error_recovery.py`
- **Purpose**: Handles common pipeline failures and automatically fixes them
- **Usage**: Command line tool to detect and fix common Flutter errors
- **Arguments**:
  - `--app-root`: Path to app root directory (optional)
  - `--rollback-on-failure`: Rollback changes if recovery fails (optional)
  - `--verbose`: Enable verbose output (optional)
- **Environment Variables**:
  - `APP_DIR`: App directory name (default: 'test_todo_app')
  - `APP_ROOT`: Full path to app root (default: '$HOME/AppMagician/$APP_DIR')
- **Error Detection & Recovery**:
  - Detect common error patterns (missing imports, provider issues, navigation problems)
  - Automatically fix common issues (update imports, fix provider usage, etc.)
  - Provide detailed error analysis and suggested fixes
  - Create backup of working state before attempting fixes
  - Log all recovery attempts and their results
  - Include rollback functionality if fixes fail
- **Exit Codes**:
  - `0`: Error recovery successful
  - `1`: Error recovery failed
- **Examples**:
  ```bash
  python3 Python/error_recovery.py
  python3 Python/error_recovery.py --rollback-on-failure
  python3 Python/error_recovery.py --verbose
  python3 Python/error_recovery.py --app-root /path/to/app
  ```

## Requirements

- Python 3.6+
- cursor-agent CLI tool
- Required environment variables (see individual script documentation)

## Usage in Jenkins

The scripts are called from the Jenkins pipeline using:
```bash
python3 "${WORKSPACE}/Python/script_name.py"
```

Where `${WORKSPACE}` is the Jenkins workspace directory containing both the Jenkinsfile and Python folder.
