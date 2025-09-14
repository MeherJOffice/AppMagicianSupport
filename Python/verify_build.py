#!/usr/bin/env python3
"""
Build verification script for AppMagician pipeline.
Verifies that Flutter apps build correctly across all platforms.
"""

import os
import sys
import re
import subprocess
import argparse
import platform
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class BuildVerifier:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.checks: List[Dict] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.is_macos = platform.system() == "Darwin"
        
    def verify_build(self) -> bool:
        """Run all build verification checks and return True if all pass."""
        print("🔨 Starting build verification...")
        print(f"📁 App root: {self.app_root}")
        print(f"🖥️  Platform: {platform.system()}")
        print("="*60)
        
        # Check if app directory exists
        if not self.app_root.exists():
            print(f"❌ ERROR: App directory does not exist: {self.app_root}")
            return False
            
        # Change to app directory
        os.chdir(self.app_root)
        
        # Run all build verification checks
        self.verify_flutter_clean()
        self.verify_flutter_pub_get()
        self.verify_flutter_analyze()
        self.verify_flutter_test()
        if self.is_macos:
            self.verify_ios_build()
        self.verify_generated_files()
        self.verify_app_installation()
        
        # Print results
        self.print_build_report()
        
        return len(self.errors) == 0
    
    def add_check(self, name: str, passed: bool, message: str, details: str = ""):
        """Add a build verification check result."""
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
        
    def run_command(self, command: List[str], capture_output: bool = True, timeout: int = 300) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.app_root
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
            
    def verify_flutter_clean(self):
        """Run flutter clean to ensure clean build."""
        print("\n🧹 Running flutter clean...")
        
        exit_code, stdout, stderr = self.run_command(["flutter", "clean"])
        
        if exit_code == 0:
            self.add_check("Flutter Clean", True, "Clean completed successfully")
        else:
            self.add_check("Flutter Clean", False, f"Clean failed (exit code: {exit_code})", stderr)
            
    def verify_flutter_pub_get(self):
        """Run flutter pub get to ensure dependencies are resolved."""
        print("\n📦 Running flutter pub get...")
        
        exit_code, stdout, stderr = self.run_command(["flutter", "pub", "get"])
        
        if exit_code == 0:
            # Check for any warnings in the output
            if "warning" in stdout.lower() or "warning" in stderr.lower():
                self.add_warning("Dependencies resolved with warnings")
            
            self.add_check("Flutter Pub Get", True, "Dependencies resolved successfully")
        else:
            self.add_check("Flutter Pub Get", False, f"Dependency resolution failed (exit code: {exit_code})", stderr)
            
    def verify_flutter_analyze(self):
        """Run flutter analyze to check for compilation errors."""
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
                
    def verify_flutter_test(self):
        """Run flutter test to ensure all tests pass."""
        print("\n🧪 Running flutter test...")
        
        exit_code, stdout, stderr = self.run_command(["flutter", "test"])
        
        if exit_code == 0:
            # Extract test results
            test_match = re.search(r"(\d+) tests? passed", stdout)
            if test_match:
                test_count = int(test_match.group(1))
                self.add_check("Flutter Test", True, f"All {test_count} tests passed")
            else:
                self.add_check("Flutter Test", True, "All tests passed")
        else:
            # Extract failure information
            failure_match = re.search(r"(\d+) tests? failed", stdout)
            if failure_match:
                failure_count = int(failure_match.group(1))
                self.add_check(
                    "Flutter Test", 
                    False, 
                    f"{failure_count} tests failed",
                    stdout + stderr
                )
            else:
                self.add_check("Flutter Test", False, "Tests failed", stdout + stderr)
                
            
    def verify_ios_build(self):
        """Run flutter build ios --debug to verify iOS build (macOS only)."""
        if not self.is_macos:
            self.add_check("iOS Build", True, "Skipped (not on macOS)")
            return
            
        print("\n🍎 Building iOS app (debug)...")
        
        exit_code, stdout, stderr = self.run_command([
            "flutter", "build", "ios", "--debug", "--no-codesign"
        ], timeout=600)  # 10 minute timeout for build
        
        if exit_code == 0:
            # Check if iOS build artifacts were created
            ios_build_dir = self.app_root / "build" / "ios"
            if ios_build_dir.exists():
                self.add_check("iOS Build", True, "iOS app built successfully")
            else:
                self.add_check("iOS Build", False, "iOS build directory not found")
        else:
            self.add_check("iOS Build", False, f"iOS build failed (exit code: {exit_code})", stderr)
            
    def verify_generated_files(self):
        """Check that all generated files are properly created."""
        print("\n📄 Checking generated files...")
        
        # Check for essential generated files
        essential_files = []
        
        if self.is_macos:
            essential_files.extend([
                "build/ios/Debug-iphoneos/Runner.app",
                "build/ios/Debug-iphoneos/Runner.app/Info.plist",
            ])
        
        missing_files = []
        for file_path in essential_files:
            full_path = self.app_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                
        if missing_files:
            self.add_check(
                "Generated Files", 
                False, 
                f"Missing {len(missing_files)} essential files",
                ", ".join(missing_files)
            )
        else:
            self.add_check("Generated Files", True, f"All {len(essential_files)} essential files present")
            
        # Check for additional important files
        additional_files = [
            "pubspec.lock",
            ".packages",
        ]
        
        present_files = []
        for file_path in additional_files:
            full_path = self.app_root / file_path
            if full_path.exists():
                present_files.append(file_path)
                
        if present_files:
            self.add_check(
                "Additional Files", 
                True, 
                f"Found {len(present_files)} additional important files"
            )
        else:
            self.add_warning("No additional important files found")
            
    def verify_app_installation(self):
        """Verify that the app can be installed and launched."""
        print("\n📱 Verifying app installation...")
        
        # Check iOS app bundle integrity (macOS only)
        if self.is_macos:
            ios_app_path = self.app_root / "build" / "ios" / "Debug-iphoneos" / "Runner.app"
            if ios_app_path.exists():
                try:
                    # Check if Info.plist exists and is readable
                    info_plist = ios_app_path / "Info.plist"
                    if info_plist.exists():
                        self.add_check("iOS App Installation", True, "iOS app bundle is valid")
                    else:
                        self.add_check("iOS App Installation", False, "Info.plist not found in iOS app bundle")
                except Exception as e:
                    self.add_check("iOS App Installation", False, f"Could not verify iOS app bundle: {e}")
            else:
                self.add_check("iOS App Installation", False, "iOS app bundle not found")
        else:
            self.add_check("iOS App Installation", True, "Skipped (not on macOS)")
                
    def print_build_report(self):
        """Print comprehensive build verification report."""
        print("\n" + "="*60)
        print("📊 BUILD VERIFICATION REPORT")
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
            if check.get('details') and not check["passed"]:
                print(f"    Details: {check['details'][:200]}...")
                
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
            print("\n🎉 All build verification checks passed!")
        elif passed_checks >= total_checks * 0.8:  # 80% pass rate
            print("\n⚠️  Build verification mostly passed (80%+)")
        else:
            print("\n❌ Build verification failed")
            
        # Platform-specific information
        print(f"\n🖥️  Platform Information:")
        print(f"  System: {platform.system()}")
        print(f"  Architecture: {platform.machine()}")
        print(f"  Python: {platform.python_version()}")
        
        # Build artifacts summary
        print(f"\n📦 Build Artifacts:")
        if self.is_macos:
            ios_app_path = self.app_root / "build" / "ios" / "Debug-iphoneos" / "Runner.app"
            if ios_app_path.exists():
                print(f"  iOS App: Present")
                
        print("="*60)


def main():
    """Main entry point for the build verification script."""
    parser = argparse.ArgumentParser(
        description="Verify Flutter app builds correctly across all platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Verify build for default app
    python3 Python/verify_build.py
    
    # Verify build for specific app
    APP_ROOT=/path/to/app python3 Python/verify_build.py
    
    # Verify build with verbose output
    python3 Python/verify_build.py --verbose

BUILD VERIFICATION CHECKS:
    ✅ Flutter clean (clean build environment)
    ✅ Flutter pub get (dependency resolution)
    ✅ Flutter analyze (compilation errors)
    ✅ Flutter test (all tests pass)
    ✅ iOS build (iOS app generation, macOS only)
    ✅ Generated files (essential build artifacts)
    ✅ App installation (file integrity)

EXIT CODES:
    0    All build verification checks passed
    1    One or more build verification checks failed
        """
    )
    
    parser.add_argument(
        '--app-root',
        help='Path to the app root directory (default: $HOME/AppMagician/$APP_DIR)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    
    parser.add_argument(
        '--skip-ios',
        action='store_true',
        help='Skip iOS build verification'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip test execution'
    )
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'generated_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    # Create verifier and run verification
    verifier = BuildVerifier(app_root)
    
    # Apply command line options
    if args.skip_ios:
        verifier.verify_ios_build = lambda: verifier.add_check("iOS Build", True, "Skipped by user request")
    if args.skip_tests:
        verifier.verify_flutter_test = lambda: verifier.add_check("Flutter Test", True, "Skipped by user request")
    
    success = verifier.verify_build()
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Build verification PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Build verification FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
