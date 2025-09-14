#!/usr/bin/env python3
"""
Quality gates script for AppMagician pipeline.
Runs comprehensive quality checks for Flutter iOS apps.
"""

import os
import sys
import re
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class QualityGates:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.checks: List[Dict] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.minimum_coverage = 70.0  # Minimum test coverage percentage
        
    def run_quality_checks(self, auto_fix: bool = False, max_attempts: int = 2) -> bool:
        """Run all quality checks and return True if all pass."""
        print("🚀 Starting quality gates...")
        print(f"📁 App root: {self.app_root}")
        print("="*60)
        
        # Check if app directory exists
        if not self.app_root.exists():
            print(f"❌ ERROR: App directory does not exist: {self.app_root}")
            return False
            
        # Change to app directory
        os.chdir(self.app_root)
        
        attempt = 1
        while attempt <= max_attempts:
            if attempt > 1:
                print(f"\n🔄 Quality gates attempt {attempt}/{max_attempts}")
                print("="*60)
            
            # Reset checks for each attempt
            self.checks = []
            self.errors = []
            self.warnings = []
            
            # Run all quality checks
            self.check_flutter_analyze()
            self.check_flutter_tests()
            self.check_test_coverage()
            self.check_dependencies()
            self.check_build_success()
            self.check_localization_files()
            self.check_hardcoded_strings()
            self.check_provider_initialization()
            
            # Check if all passed
            if len(self.errors) == 0:
                if attempt > 1:
                    print(f"\n✅ Quality gates passed on attempt {attempt}")
                self.print_quality_report()
                return True
            
            # If auto-fix is enabled and we have more attempts
            if auto_fix and attempt < max_attempts:
                print(f"\n🔧 Attempting auto-fix for {len(self.errors)} failed checks...")
                if self.attempt_auto_fix():
                    attempt += 1
                    continue
                else:
                    print("❌ Auto-fix failed")
                    break
            else:
                break
        
        # Print final results
        self.print_quality_report()
        return len(self.errors) == 0
    
    def add_check(self, name: str, passed: bool, message: str, details: str = ""):
        """Add a quality check result."""
        check = {
            "name": name,
            "passed": passed,
            "message": message,
            "details": details
        }
        self.checks.append(check)
        
        if passed:
            print(f"✅ {name}: {message}")
        else:
            print(f"❌ {name}: {message}")
            self.errors.append(f"{name}: {message}")
            
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        print(f"⚠️  WARNING: {message}")
        
    def run_command(self, command: List[str], capture_output: bool = True, env: dict = None) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
            
    def check_flutter_analyze(self):
        """Run flutter analyze and check for errors."""
        print("\n🔍 Running flutter analyze...")
        
        exit_code, stdout, stderr = self.run_command(["flutter", "analyze"])
        
        if exit_code == 0:
            self.add_check("Flutter Analyze", True, "No analysis issues found")
        else:
            # Check for actual errors vs warnings
            error_count = len(re.findall(r"error •", stdout + stderr))
            warning_count = len(re.findall(r"warning •", stdout + stderr))
            info_count = len(re.findall(r"info •", stdout + stderr))
            
            if error_count > 0:
                self.add_check(
                    "Flutter Analyze", 
                    False, 
                    f"Found {error_count} errors, {warning_count} warnings, {info_count} info messages",
                    stdout + stderr
                )
            else:
                self.add_check(
                    "Flutter Analyze", 
                    True, 
                    f"No errors found ({warning_count} warnings, {info_count} info messages)",
                    stdout + stderr
                )
                
    def check_flutter_tests(self):
        """Run flutter test and ensure all tests pass."""
        print("\n🧪 Running flutter tests...")
        
        exit_code, stdout, stderr = self.run_command(["flutter", "test"])
        
        if exit_code == 0:
            # Extract test results
            test_match = re.search(r"(\d+) tests? passed", stdout)
            if test_match:
                test_count = int(test_match.group(1))
                self.add_check("Flutter Tests", True, f"All {test_count} tests passed")
            else:
                self.add_check("Flutter Tests", True, "All tests passed")
        else:
            # Extract failure information
            failure_match = re.search(r"(\d+) tests? failed", stdout)
            if failure_match:
                failure_count = int(failure_match.group(1))
                self.add_check(
                    "Flutter Tests", 
                    False, 
                    f"{failure_count} tests failed",
                    stdout + stderr
                )
            else:
                self.add_check("Flutter Tests", False, "Tests failed", stdout + stderr)
                
    def check_test_coverage(self):
        """Check test coverage and ensure it's above minimum threshold."""
        print("\n📊 Checking test coverage...")
        
        # Run tests with coverage
        exit_code, stdout, stderr = self.run_command([
            "flutter", "test", "--coverage"
        ])
        
        if exit_code != 0:
            self.add_check("Test Coverage", False, "Failed to generate coverage report", stdout + stderr)
            return
            
        # Check if coverage file exists
        coverage_file = self.app_root / "coverage" / "lcov.info"
        if not coverage_file.exists():
            self.add_check("Test Coverage", False, "Coverage file not found")
            return
            
        # Parse coverage file
        try:
            with open(coverage_file, 'r') as f:
                coverage_content = f.read()
                
            # Extract coverage percentage
            coverage_match = re.search(r"LF:(\d+)\s+LH:(\d+)", coverage_content)
            if coverage_match:
                total_lines = int(coverage_match.group(1))
                covered_lines = int(coverage_match.group(2))
                coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                
                if coverage_percentage >= self.minimum_coverage:
                    self.add_check(
                        "Test Coverage", 
                        True, 
                        f"Coverage: {coverage_percentage:.1f}% (minimum: {self.minimum_coverage}%)"
                    )
                else:
                    self.add_check(
                        "Test Coverage", 
                        False, 
                        f"Coverage: {coverage_percentage:.1f}% (minimum: {self.minimum_coverage}%)"
                    )
            else:
                self.add_check("Test Coverage", False, "Could not parse coverage data")
                
        except Exception as e:
            self.add_check("Test Coverage", False, f"Error reading coverage file: {e}")
            
    def check_dependencies(self):
        """Verify that all required dependencies are installed."""
        print("\n📦 Checking dependencies...")
        
        # Check pubspec.yaml exists
        pubspec_file = self.app_root / "pubspec.yaml"
        if not pubspec_file.exists():
            self.add_check("Dependencies", False, "pubspec.yaml not found")
            return
            
        # Run flutter pub get
        exit_code, stdout, stderr = self.run_command(["flutter", "pub", "get"])
        
        if exit_code == 0:
            self.add_check("Dependencies", True, "All dependencies resolved successfully")
        else:
            self.add_check("Dependencies", False, "Dependency resolution failed", stdout + stderr)
            
        # Check for common required dependencies
        try:
            with open(pubspec_file, 'r') as f:
                pubspec_content = f.read()
                
            required_deps = [
                "flutter_localizations",
                "provider",
                "shared_preferences"
            ]
            
            missing_deps = []
            for dep in required_deps:
                if dep not in pubspec_content:
                    missing_deps.append(dep)
                    
            if missing_deps:
                self.add_warning(f"Missing recommended dependencies: {', '.join(missing_deps)}")
            else:
                self.add_check("Required Dependencies", True, "All required dependencies present")
                
        except Exception as e:
            self.add_warning(f"Could not check dependencies: {e}")
            
    def check_build_success(self):
        """Check that the app builds successfully."""
        print("\n🔨 Checking build success...")
        
        # Try building iOS (no codesign for faster build)
        exit_code, stdout, stderr = self.run_command([
            "flutter", "build", "ios", "--no-codesign"
        ])
        
        if exit_code == 0:
            self.add_check("Build Success", True, "iOS build successful")
        else:
            self.add_check("Build Success", False, "iOS build failed", stdout + stderr)
            
    def check_localization_files(self):
        """Validate that all localization files are properly generated."""
        print("\n🌍 Checking localization files...")
        
        # Check for l10n directory
        l10n_dir = self.app_root / "lib" / "l10n"
        if not l10n_dir.exists():
            self.add_check("Localization Files", False, "l10n directory not found")
            return
            
        # Check for .arb files
        arb_files = list(l10n_dir.glob("*.arb"))
        if not arb_files:
            self.add_check("Localization Files", False, "No .arb files found")
            return
            
        # Check for required locales
        required_locales = ["en", "ar"]
        found_locales = []
        
        for arb_file in arb_files:
            locale_match = re.search(r"app_(\w+)\.arb", arb_file.name)
            if locale_match:
                found_locales.append(locale_match.group(1))
                
        missing_locales = [loc for loc in required_locales if loc not in found_locales]
        
        if missing_locales:
            self.add_check(
                "Localization Files", 
                False, 
                f"Missing locales: {', '.join(missing_locales)}"
            )
        else:
            self.add_check(
                "Localization Files", 
                True, 
                f"Found locales: {', '.join(found_locales)}"
            )
            
        # Check for localization delegate
        main_dart = self.app_root / "lib" / "main.dart"
        if main_dart.exists():
            try:
                with open(main_dart, 'r') as f:
                    main_content = f.read()
                    
                if "AppLocalizations.delegate" in main_content:
                    self.add_check("Localization Setup", True, "Localization delegate configured")
                else:
                    self.add_check("Localization Setup", False, "Localization delegate not configured")
                    
            except Exception as e:
                self.add_warning(f"Could not check localization setup: {e}")
                
    def check_hardcoded_strings(self):
        """Ensure no hardcoded strings exist in the codebase."""
        print("\n🔤 Checking for hardcoded strings...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        hardcoded_strings = []
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Skip test files and generated files
                if "test" in str(dart_file) or "generated" in str(dart_file):
                    continue
                    
                # Look for hardcoded strings (simple heuristic)
                # This is a basic check - in practice, you'd want more sophisticated analysis
                string_matches = re.findall(r'Text\s*\(\s*["\']([^"\']+)["\']', content)
                
                for match in string_matches:
                    # Skip very short strings and common patterns
                    if len(match) > 3 and not re.match(r'^[A-Z_]+$', match):
                        hardcoded_strings.append(f"{dart_file.name}: {match}")
                        
            except Exception as e:
                self.add_warning(f"Could not check {dart_file.name}: {e}")
                
        if hardcoded_strings:
            self.add_check(
                "Hardcoded Strings", 
                False, 
                f"Found {len(hardcoded_strings)} potential hardcoded strings",
                "\n".join(hardcoded_strings[:10])  # Show first 10
            )
        else:
            self.add_check("Hardcoded Strings", True, "No hardcoded strings found")
            
    def check_provider_initialization(self):
        """Check that all providers are properly initialized."""
        print("\n🔄 Checking provider initialization...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        provider_files = []
        provider_usage = []
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for provider imports
                if "provider" in content or "riverpod" in content:
                    provider_files.append(dart_file.name)
                    
                # Check for provider usage patterns
                provider_patterns = [
                    r"ChangeNotifierProvider",
                    r"Provider\.",
                    r"Consumer\(",
                    r"ref\.watch\(",
                    r"ref\.read\(",
                    r"useProvider\("
                ]
                
                for pattern in provider_patterns:
                    if re.search(pattern, content):
                        provider_usage.append(f"{dart_file.name}: {pattern}")
                        
            except Exception as e:
                self.add_warning(f"Could not check {dart_file.name}: {e}")
                
        if provider_files:
            self.add_check(
                "Provider Initialization", 
                True, 
                f"Found provider usage in {len(provider_files)} files"
            )
        else:
            self.add_check("Provider Initialization", False, "No provider usage found")
            
    def print_quality_report(self):
        """Print comprehensive quality report."""
        print("\n" + "="*60)
        print("📊 QUALITY GATES REPORT")
        print("="*60)
        
        # Count passed/failed checks
        passed_checks = sum(1 for check in self.checks if check["passed"])
        total_checks = len(self.checks)
        
        print(f"\n📈 Summary: {passed_checks}/{total_checks} checks passed")
        
        # Print detailed results
        print(f"\n📋 Detailed Results:")
        for check in self.checks:
            status = "✅ PASS" if check["passed"] else "❌ FAIL"
            print(f"  {status} {check['name']}: {check['message']}")
            
        if self.errors:
            print(f"\n❌ FAILED CHECKS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        # Overall status
        if passed_checks == total_checks:
            print("\n🎉 All quality gates passed!")
        elif passed_checks >= total_checks * 0.8:  # 80% pass rate
            print("\n⚠️  Quality gates mostly passed (80%+)")
        else:
            print("\n❌ Quality gates failed")
            
        print("="*60)
    
    def attempt_auto_fix(self) -> bool:
        """Attempt to auto-fix quality issues using Cursor."""
        print("\n🤖 Sending quality issues to Cursor for auto-fix...")
        
        # Create a comprehensive prompt for Cursor
        failed_checks = [check for check in self.checks if not check["passed"]]
        
        if not failed_checks:
            print("✅ No failed checks to fix")
            return True
        
        # Build detailed prompt
        prompt_parts = [
            "You are a senior Flutter iOS engineer. The quality gates have identified the following issues that need to be fixed:",
            "",
            "FAILED QUALITY CHECKS:"
        ]
        
        for check in failed_checks:
            prompt_parts.append(f"- {check['name']}: {check['message']}")
            if check.get('details'):
                prompt_parts.append(f"  Details: {check['details'][:500]}...")  # Limit details length
        
        prompt_parts.extend([
            "",
            "REQUIREMENTS:",
            "- Fix all the above quality issues",
            "- Maintain existing functionality",
            "- Ensure iOS build compatibility",
            "- Follow Flutter best practices",
            "- Make minimal, targeted changes",
            "",
            "When you are finished, print EXACTLY this line as the final output:",
            "~~CURSOR_DONE~~"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Save prompt to file for Cursor
        with open('.quality_fix_prompt.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        # Create wrapper for Cursor
        wrapper_content = """CONTEXT (MANDATORY — READ CAREFULLY):
- You are editing an EXISTING Flutter iOS project in the CURRENT working directory.
- NEVER run 'flutter create'. Do NOT create a nested Flutter project.
- Do NOT cd elsewhere; keep all changes inside this project root.
- Apply minimal, targeted changes needed to fix the reported quality issues.

COMPLETION REQUIREMENT:
- When you are DONE, print EXACTLY this line as the final output (no quotes/extra spaces):
~~CURSOR_DONE~~
"""
        
        with open('.wrap.txt', 'w', encoding='utf-8') as f:
            f.write(wrapper_content)
        
        # Combine wrapper and prompt
        with open('.prompt.txt', 'w', encoding='utf-8') as f:
            f.write(wrapper_content + "\n" + prompt)
        
        # Run Cursor auto-fix directly
        try:
            # Set up environment for cursor-agent
            env = os.environ.copy()
            env.update({
                'CURSOR_CI': '1',
                'CURSOR_NO_INTERACTIVE': '1',
                'CURSOR_EXIT_ON_COMPLETION': '1',
                'TERM': 'xterm-256color'
            })
            
            # Run cursor-agent directly (use full path)
            cursor_agent_path = "/Users/meher/.local/bin/cursor-agent"
            if not os.path.exists(cursor_agent_path):
                print(f"❌ cursor-agent not found at: {cursor_agent_path}")
                return False
            
            exit_code, stdout, stderr = self.run_command([
                cursor_agent_path, "-p", "--force", "--output-format", "text", prompt
            ], env=env)
            
            if exit_code == 0 and "~~CURSOR_DONE~~" in stdout:
                print("✅ Cursor auto-fix completed successfully")
                return True
            else:
                print(f"❌ Cursor auto-fix failed (exit code: {exit_code})")
                print(f"Output: {stdout[:500]}...")
                if stderr:
                    print(f"Error: {stderr[:500]}...")
                return False
                
        except Exception as e:
            print(f"❌ Error running Cursor auto-fix: {e}")
            return False


def main():
    """Main entry point for the quality gates script."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive quality checks for Flutter iOS apps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Run quality gates on default app
    python3 Python/quality_gates.py
    
    # Run quality gates with auto-fix enabled
    python3 Python/quality_gates.py --auto-fix
    
    # Run with custom coverage threshold and auto-fix
    python3 Python/quality_gates.py --min-coverage 80 --auto-fix
    
    # Run with multiple auto-fix attempts
    python3 Python/quality_gates.py --auto-fix --max-attempts 3

QUALITY CHECKS:
    ✅ Flutter analyze (errors only, not warnings)
    ✅ Flutter tests (all tests must pass)
    ✅ Test coverage (minimum threshold)
    ✅ Dependencies (all resolved)
    ✅ Build success (iOS build --no-codesign)
    ✅ Localization files (properly generated)
    ✅ Hardcoded strings (none found)
    ✅ Provider initialization (properly configured)

EXIT CODES:
    0    All quality gates passed
    1    One or more quality gates failed
        """
    )
    
    parser.add_argument(
        '--app-root',
        help='Path to the app root directory (default: $HOME/AppMagician/$APP_DIR)'
    )
    
    parser.add_argument(
        '--min-coverage',
        type=float,
        default=70.0,
        help='Minimum test coverage percentage (default: 70.0)'
    )
    
    parser.add_argument(
        '--json-output',
        help='Output results to JSON file'
    )
    
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Enable auto-fix using Cursor (default: false)'
    )
    
    parser.add_argument(
        '--max-attempts',
        type=int,
        default=2,
        help='Maximum auto-fix attempts (default: 2)'
    )
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'test_todo_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    # Create quality gates and run checks
    quality_gates = QualityGates(app_root)
    quality_gates.minimum_coverage = args.min_coverage
    
    success = quality_gates.run_quality_checks(
        auto_fix=args.auto_fix,
        max_attempts=args.max_attempts
    )
    
    # Output JSON if requested
    if args.json_output:
        try:
            report_data = {
                "timestamp": str(Path().cwd()),
                "app_root": str(app_root),
                "checks": quality_gates.checks,
                "errors": quality_gates.errors,
                "warnings": quality_gates.warnings,
                "passed": success
            }
            
            with open(args.json_output, 'w') as f:
                json.dump(report_data, f, indent=2)
                
            print(f"\n📄 Quality report saved to: {args.json_output}")
            
        except Exception as e:
            print(f"\n❌ Failed to save JSON report: {e}")
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Quality gates PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Quality gates FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
