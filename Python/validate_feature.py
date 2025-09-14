#!/usr/bin/env python3
"""
Feature validation script for AppMagician pipeline.
Validates individual features for proper structure and integration.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class FeatureValidator:
    def __init__(self, app_root: str, feature_name: str):
        self.app_root = Path(app_root)
        self.feature_name = feature_name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks: List[Tuple[str, bool, str]] = []  # (check_name, passed, message)
        
    def validate(self) -> bool:
        """Run all validation checks and return True if all pass."""
        print(f"🔍 Validating feature: {self.feature_name}")
        print(f"📁 App root: {self.app_root}")
        print("="*60)
        
        # Check if app directory exists
        if not self.app_root.exists():
            self.add_check("App directory exists", False, f"App directory does not exist: {self.app_root}")
            return False
            
        # Run all validation checks
        self.validate_feature_directory()
        self.validate_feature_structure()
        self.validate_provider_usage()
        self.validate_home_screen_imports()
        self.validate_no_placeholder_screens()
        self.validate_feature_integration()
        
        # Print results
        self.print_results()
        
        return len(self.errors) == 0
    
    def add_check(self, check_name: str, passed: bool, message: str):
        """Add a validation check result."""
        self.checks.append((check_name, passed, message))
        if passed:
            print(f"✅ {check_name}: {message}")
        else:
            print(f"❌ {check_name}: {message}")
            self.errors.append(f"{check_name}: {message}")
            
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        print(f"⚠️  WARNING: {message}")
        
    def validate_feature_directory(self):
        """Check if feature directory exists."""
        print("\n📁 Checking feature directory...")
        
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        if feature_dir.exists():
            self.add_check("Feature directory exists", True, f"Found: {feature_dir}")
        else:
            self.add_check("Feature directory exists", False, f"Missing: {feature_dir}")
            return
            
    def validate_feature_structure(self):
        """Validate feature has proper structure."""
        print("\n🏗️  Checking feature structure...")
        
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        
        # Required subdirectories
        required_dirs = [
            "data",
            "domain", 
            "presentation"
        ]
        
        for dir_name in required_dirs:
            dir_path = feature_dir / dir_name
            if dir_path.exists():
                self.add_check(f"Has {dir_name}/ directory", True, f"Found: {dir_path}")
            else:
                self.add_check(f"Has {dir_name}/ directory", False, f"Missing: {dir_path}")
                
        # Check for providers directory
        providers_dir = feature_dir / "data" / "providers"
        if providers_dir.exists():
            self.add_check("Has data/providers/ directory", True, f"Found: {providers_dir}")
        else:
            self.add_check("Has data/providers/ directory", False, f"Missing: {providers_dir}")
            
        # Check for models directory
        models_dir = feature_dir / "domain" / "models"
        if models_dir.exists():
            self.add_check("Has domain/models/ directory", True, f"Found: {models_dir}")
        else:
            self.add_check("Has domain/models/ directory", False, f"Missing: {models_dir}")
            
        # Check for screens directory
        screens_dir = feature_dir / "presentation" / "screens"
        if screens_dir.exists():
            self.add_check("Has presentation/screens/ directory", True, f"Found: {screens_dir}")
        else:
            self.add_check("Has presentation/screens/ directory", False, f"Missing: {screens_dir}")
            
    def validate_provider_usage(self):
        """Ensure screens use providers."""
        print("\n🔄 Checking provider usage...")
        
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if not screens_dir.exists():
            self.add_check("Provider usage validation", False, "Screens directory does not exist")
            return
            
        # Find all screen files
        screen_files = list(screens_dir.glob("*_screen.dart"))
        
        if not screen_files:
            self.add_check("Provider usage validation", False, "No screen files found")
            return
            
        provider_usage_found = False
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for provider usage patterns
                provider_patterns = [
                    rf"ref\.watch\({self.feature_name}Provider\)",
                    rf"ref\.read\({self.feature_name}Provider\)",
                    rf"useProvider\({self.feature_name}Provider\)",
                    rf"Consumer\({self.feature_name}Provider\)",
                    rf"Provider\.{self.feature_name}",
                ]
                
                for pattern in provider_patterns:
                    if re.search(pattern, content):
                        provider_usage_found = True
                        self.add_check(f"Provider usage in {screen_file.name}", True, f"Found: {pattern}")
                        break
                else:
                    self.add_check(f"Provider usage in {screen_file.name}", False, "No provider usage found")
                    
            except Exception as e:
                self.add_check(f"Provider usage in {screen_file.name}", False, f"Error reading file: {e}")
                
        if provider_usage_found:
            self.add_check("Provider usage validation", True, "At least one screen uses providers")
        else:
            self.add_check("Provider usage validation", False, "No screens use providers")
            
    def validate_home_screen_imports(self):
        """Check if HomeScreen imports correct screens from the feature."""
        print("\n🔗 Checking HomeScreen imports...")
        
        # Find HomeScreen
        home_screen_path = self.find_file("home_screen.dart")
        if not home_screen_path:
            self.add_check("HomeScreen imports", False, "HomeScreen not found")
            return
            
        try:
            with open(home_screen_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.add_check("HomeScreen imports", False, f"Cannot read HomeScreen: {e}")
            return
            
        # Check for feature screen imports
        feature_import_pattern = rf"features/{self.feature_name}/.*screen"
        feature_imports = re.findall(feature_import_pattern, content)
        
        if feature_imports:
            self.add_check("HomeScreen imports", True, f"Found imports: {feature_imports}")
        else:
            self.add_check("HomeScreen imports", False, f"No imports found for feature '{self.feature_name}'")
            
        # Check for specific screen imports
        feature_screens = self.get_feature_screens()
        imported_screens = []
        
        for screen in feature_screens:
            screen_import_pattern = rf"features/{self.feature_name}/.*{screen}"
            if re.search(screen_import_pattern, content):
                imported_screens.append(screen)
                
        if imported_screens:
            self.add_check("Specific screen imports", True, f"Imported screens: {imported_screens}")
        else:
            self.add_check("Specific screen imports", False, "No specific screens imported")
            
    def validate_no_placeholder_screens(self):
        """Validate that no placeholder screens exist."""
        print("\n🚫 Checking for placeholder screens...")
        
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if not screens_dir.exists():
            self.add_check("Placeholder screen check", False, "Screens directory does not exist")
            return
            
        screen_files = list(screens_dir.glob("*_screen.dart"))
        placeholder_found = False
        
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for placeholder content
                placeholder_patterns = [
                    r"TODO|FIXME|placeholder|sample|demo|lorem|ipsum",
                    r"Text\s*\(\s*['\"]\s*['\"]\s*\)",  # Empty Text widgets
                    r"Container\s*\(\s*\)",  # Empty containers
                    r"return\s+Scaffold\s*\(\s*\)",  # Empty Scaffold
                ]
                
                for pattern in placeholder_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        placeholder_found = True
                        self.add_check(f"Placeholder check in {screen_file.name}", False, f"Found placeholder: {pattern}")
                        break
                else:
                    self.add_check(f"Placeholder check in {screen_file.name}", True, "No placeholders found")
                    
            except Exception as e:
                self.add_check(f"Placeholder check in {screen_file.name}", False, f"Error reading file: {e}")
                
        if not placeholder_found:
            self.add_check("Placeholder screen check", True, "No placeholder screens found")
        else:
            self.add_check("Placeholder screen check", False, "Placeholder screens found")
            
    def validate_feature_integration(self):
        """Validate overall feature integration."""
        print("\n🔗 Checking feature integration...")
        
        # Check if feature is referenced in main.dart
        main_dart = self.app_root / "lib" / "main.dart"
        if main_dart.exists():
            try:
                with open(main_dart, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if self.feature_name in content:
                    self.add_check("Feature referenced in main.dart", True, f"Found references to '{self.feature_name}'")
                else:
                    self.add_check("Feature referenced in main.dart", False, f"No references to '{self.feature_name}'")
                    
            except Exception as e:
                self.add_check("Feature referenced in main.dart", False, f"Error reading main.dart: {e}")
        else:
            self.add_check("Feature referenced in main.dart", False, "main.dart not found")
            
        # Check for feature-specific dependencies in pubspec.yaml
        pubspec_path = self.app_root / "pubspec.yaml"
        if pubspec_path.exists():
            try:
                with open(pubspec_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for feature-specific dependencies
                feature_deps = []
                if "provider" in content:
                    feature_deps.append("provider")
                if "riverpod" in content:
                    feature_deps.append("riverpod")
                if "shared_preferences" in content:
                    feature_deps.append("shared_preferences")
                    
                if feature_deps:
                    self.add_check("Feature dependencies", True, f"Found dependencies: {feature_deps}")
                else:
                    self.add_check("Feature dependencies", False, "No feature-specific dependencies found")
                    
            except Exception as e:
                self.add_check("Feature dependencies", False, f"Error reading pubspec.yaml: {e}")
        else:
            self.add_check("Feature dependencies", False, "pubspec.yaml not found")
            
    def get_feature_screens(self) -> List[str]:
        """Get list of screen files in the feature."""
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if not screens_dir.exists():
            return []
            
        screen_files = list(screens_dir.glob("*_screen.dart"))
        return [f.stem.replace('_screen', '') for f in screen_files]
        
    def find_file(self, pattern: str) -> Optional[Path]:
        """Find a single file matching the pattern."""
        files = self.find_files(pattern)
        return files[0] if files else None
        
    def find_files(self, pattern: str) -> List[Path]:
        """Find all files matching the pattern."""
        files = []
        for root, dirs, filenames in os.walk(self.app_root):
            for filename in filenames:
                if re.match(pattern.replace('*', '.*'), filename):
                    files.append(Path(root) / filename)
        return files
        
    def print_results(self):
        """Print validation results."""
        print("\n" + "="*60)
        print("📊 FEATURE VALIDATION RESULTS")
        print("="*60)
        
        # Count passed/failed checks
        passed_checks = sum(1 for _, passed, _ in self.checks if passed)
        total_checks = len(self.checks)
        
        print(f"\n📈 Summary: {passed_checks}/{total_checks} checks passed")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
            
        print("="*60)


def main():
    """Main entry point for the feature validation script."""
    parser = argparse.ArgumentParser(
        description="Validate individual features in AppMagician pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Validate expenses feature
    python3 Python/validate_feature.py expenses
    
    # Validate savings feature with custom app path
    APP_ROOT=/path/to/app python3 Python/validate_feature.py savings
    
    # Validate settings feature
    python3 Python/validate_feature.py settings

VALIDATION CHECKS:
    ✅ Feature directory exists in lib/features/{feature}/
    ✅ Proper structure: data/, domain/, presentation/
    ✅ Has data/providers/, domain/models/, presentation/screens/
    ✅ Screens use providers (ref.watch({feature}Provider))
    ✅ HomeScreen imports correct screens from the feature
    ✅ No placeholder screens exist
    ✅ Feature integration in main.dart and pubspec.yaml

EXIT CODES:
    0    All validations passed
    1    Validation failures found
        """
    )
    
    parser.add_argument(
        'feature_name',
        help='Name of the feature to validate (e.g., "expenses", "savings", "settings")'
    )
    
    parser.add_argument(
        '--app-root',
        help='Path to the app root directory (default: $HOME/AppMagician/$APP_DIR)'
    )
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'test_todo_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    # Create validator and run validation
    validator = FeatureValidator(app_root, args.feature_name)
    success = validator.validate()
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Feature '{args.feature_name}' validation PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Feature '{args.feature_name}' validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
