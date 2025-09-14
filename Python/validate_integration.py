#!/usr/bin/env python3
"""
Integration validation script for AppMagician pipeline.
Validates that all features are properly integrated in the Flutter app.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class IntegrationValidator:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.features: Dict[str, Dict] = {}
        self.screens: Dict[str, str] = {}
        self.providers: Dict[str, str] = {}
        
    def validate(self) -> bool:
        """Run all validation checks and return True if all pass."""
        print("🔍 Starting integration validation...")
        
        # Check if app directory exists
        if not self.app_root.exists():
            self.add_error(f"App directory does not exist: {self.app_root}")
            return False
            
        # Run all validation checks
        self.validate_app_structure()
        self.validate_feature_imports()
        self.validate_provider_usage()
        self.validate_screen_implementations()
        self.validate_file_locations()
        self.validate_no_duplicates()
        self.validate_routing_integration()
        
        # Print results
        self.print_results()
        
        return len(self.errors) == 0
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(f"❌ ERROR: {message}")
        
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def validate_app_structure(self):
        """Validate basic app structure."""
        print("📁 Validating app structure...")
        
        required_dirs = [
            "lib",
            "lib/features",
            "lib/core",
            "test",
            "ios"
        ]
        
        for dir_path in required_dirs:
            full_path = self.app_root / dir_path
            if not full_path.exists():
                self.add_error(f"Required directory missing: {dir_path}")
                
    def validate_feature_imports(self):
        """Validate that HomeScreen imports correct feature screens."""
        print("🔗 Validating feature imports...")
        
        # Find HomeScreen
        home_screen_path = self.find_file("home_screen.dart")
        if not home_screen_path:
            self.add_error("HomeScreen not found")
            return
            
        # Read HomeScreen content
        try:
            with open(home_screen_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.add_error(f"Cannot read HomeScreen: {e}")
            return
            
        # Check for proper imports
        self.check_home_screen_imports(content, home_screen_path)
        
    def check_home_screen_imports(self, content: str, file_path: Path):
        """Check HomeScreen imports for feature screens."""
        # Look for import statements
        import_pattern = r"import\s+['\"]([^'\"]+)['\"]"
        imports = re.findall(import_pattern, content)
        
        # Check for feature screen imports
        feature_imports = [imp for imp in imports if 'features/' in imp and 'screen' in imp]
        
        if not feature_imports:
            self.add_error("HomeScreen has no feature screen imports")
            return
            
        # Validate each feature import
        for imp in feature_imports:
            self.validate_feature_import(imp, file_path)
            
    def validate_feature_import(self, import_path: str, file_path: Path):
        """Validate a single feature import."""
        # Convert import to file path
        if import_path.startswith('package:'):
            # Package import - skip validation
            return
            
        # Relative import
        if import_path.startswith('../'):
            # Go up from current file location
            current_dir = file_path.parent
            target_path = current_dir / import_path
        else:
            # Assume lib/ root
            target_path = self.app_root / "lib" / import_path
            
        # Check if file exists
        if not target_path.exists():
            self.add_error(f"Imported file does not exist: {import_path} -> {target_path}")
            return
            
        # Check if it's a screen file
        if not target_path.name.endswith('_screen.dart'):
            self.add_warning(f"Import may not be a screen file: {import_path}")
            
    def validate_provider_usage(self):
        """Validate that screens use their respective Riverpod providers."""
        print("🔄 Validating provider usage...")
        
        # Find all screen files
        screen_files = self.find_files("*_screen.dart")
        
        for screen_file in screen_files:
            self.validate_screen_provider_usage(screen_file)
            
    def validate_screen_provider_usage(self, screen_file: Path):
        """Validate provider usage in a single screen."""
        try:
            with open(screen_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.add_error(f"Cannot read screen file {screen_file}: {e}")
            return
            
        # Check for provider imports
        provider_imports = re.findall(r"import\s+['\"]([^'\"]*provider[^'\"]*)['\"]", content)
        
        if not provider_imports:
            self.add_warning(f"Screen {screen_file.name} has no provider imports")
            return
            
        # Check for provider usage in code
        provider_usage = re.findall(r"useProvider|Provider\.|Consumer|ref\.watch|ref\.read", content)
        
        if not provider_usage:
            self.add_warning(f"Screen {screen_file.name} imports providers but doesn't use them")
            
    def validate_screen_implementations(self):
        """Validate that all screens are properly implemented."""
        print("📱 Validating screen implementations...")
        
        # Find all screen files
        screen_files = self.find_files("*_screen.dart")
        
        for screen_file in screen_files:
            self.validate_single_screen(screen_file)
            
    def validate_single_screen(self, screen_file: Path):
        """Validate a single screen implementation."""
        try:
            with open(screen_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.add_error(f"Cannot read screen file {screen_file}: {e}")
            return
            
        # Check for required screen elements
        required_elements = [
            r"class\s+\w+Screen\s+extends\s+\w+",
            r"Widget\s+build\s*\(",
            r"return\s+Scaffold|return\s+MaterialApp"
        ]
        
        for pattern in required_elements:
            if not re.search(pattern, content):
                self.add_error(f"Screen {screen_file.name} missing required element: {pattern}")
                
        # Check for placeholder content
        placeholder_patterns = [
            r"TODO|FIXME|placeholder|sample|demo|lorem|ipsum",
            r"Text\s*\(\s*['\"]\s*['\"]\s*\)",  # Empty Text widgets
            r"Container\s*\(\s*\)",  # Empty containers
        ]
        
        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.add_warning(f"Screen {screen_file.name} may contain placeholder content: {pattern}")
                
    def validate_file_locations(self):
        """Validate that all required files exist in correct locations."""
        print("📂 Validating file locations...")
        
        # Check for required core files
        required_core_files = [
            "lib/main.dart",
            "lib/core/presentation/screens/main_screen.dart",
            "lib/core/presentation/widgets/app_drawer.dart",
            "lib/core/presentation/widgets/loading_widget.dart",
            "lib/core/presentation/widgets/error_widget.dart"
        ]
        
        for file_path in required_core_files:
            full_path = self.app_root / file_path
            if not full_path.exists():
                self.add_error(f"Required core file missing: {file_path}")
                
        # Check for localization files
        l10n_files = self.find_files("*.arb")
        if not l10n_files:
            self.add_warning("No localization files (.arb) found")
            
        # Check for test files
        test_files = self.find_files("*_test.dart")
        if not test_files:
            self.add_warning("No test files found")
            
    def validate_no_duplicates(self):
        """Validate that no duplicate screen implementations exist."""
        print("🔍 Checking for duplicate implementations...")
        
        # Find all screen files
        screen_files = self.find_files("*_screen.dart")
        
        # Group by screen name
        screen_groups = {}
        for screen_file in screen_files:
            screen_name = screen_file.stem.replace('_screen', '')
            if screen_name not in screen_groups:
                screen_groups[screen_name] = []
            screen_groups[screen_name].append(screen_file)
            
        # Check for duplicates
        for screen_name, files in screen_groups.items():
            if len(files) > 1:
                self.add_error(f"Duplicate screen implementations for {screen_name}: {[f.name for f in files]}")
                
    def validate_routing_integration(self):
        """Validate that routing is properly integrated."""
        print("🛣️  Validating routing integration...")
        
        # Check main.dart for routing setup
        main_dart = self.app_root / "lib" / "main.dart"
        if main_dart.exists():
            try:
                with open(main_dart, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for routing setup
                if "MaterialApp" not in content:
                    self.add_error("main.dart missing MaterialApp setup")
                    
                if "routes" not in content and "onGenerateRoute" not in content:
                    self.add_warning("main.dart may not have routing configured")
                    
            except Exception as e:
                self.add_error(f"Cannot read main.dart: {e}")
                
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
        print("📊 VALIDATION RESULTS")
        print("="*60)
        
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
            
        print(f"\n📈 Summary: {len(self.errors)} errors, {len(self.warnings)} warnings")
        print("="*60)


def main():
    """Main entry point for the validation script."""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
🔍 Integration Validation Script for AppMagician Pipeline

USAGE:
    python3 Python/validate_integration.py [OPTIONS]

OPTIONS:
    -h, --help          Show this help message

ENVIRONMENT VARIABLES:
    APP_DIR             App directory name (default: 'test_todo_app')
    APP_ROOT            Full path to app root (default: '$HOME/AppMagician/$APP_DIR')

VALIDATION CHECKS:
    ✅ App structure and required directories
    ✅ Feature screen imports and file existence  
    ✅ Provider usage in screens
    ✅ Screen implementations and required elements
    ✅ File locations and core files
    ✅ Duplicate screen implementations
    ✅ Routing integration

EXIT CODES:
    0    All validations passed
    1    Validation failures found

EXAMPLES:
    # Validate default app
    python3 Python/validate_integration.py
    
    # Validate specific app
    APP_DIR=my_app python3 Python/validate_integration.py
    
    # Validate with custom path
    APP_ROOT=/path/to/app python3 Python/validate_integration.py
        """)
        sys.exit(0)
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'test_todo_app')
    app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    print(f"🔍 Validating integration for app: {app_dir}")
    print(f"📁 App root: {app_root}")
    
    # Create validator and run validation
    validator = IntegrationValidator(app_root)
    success = validator.validate()
    
    # Exit with appropriate code
    if success:
        print("\n✅ Integration validation PASSED")
        sys.exit(0)
    else:
        print("\n❌ Integration validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
