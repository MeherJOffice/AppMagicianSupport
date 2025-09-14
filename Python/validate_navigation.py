#!/usr/bin/env python3
"""
Navigation validation script for AppMagician pipeline.
Validates Flutter app navigation flow and structure.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class NavigationValidator:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks: List[Tuple[str, bool, str]] = []  # (check_name, passed, message)
        
    def validate(self) -> bool:
        """Run all navigation validation checks and return True if all pass."""
        print("🧭 Starting navigation validation...")
        print(f"📁 App root: {self.app_root}")
        print("="*60)
        
        # Check if app directory exists
        if not self.app_root.exists():
            print(f"❌ ERROR: App directory does not exist: {self.app_root}")
            return False
            
        # Run all validation checks
        self.validate_navigation_structure()
        self.validate_navigation_destinations()
        self.validate_navigation_icons_labels()
        self.validate_navigation_state_management()
        self.validate_navigation_memory_leaks()
        self.validate_keyboard_handling()
        self.validate_navigation_animations()
        
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
        
    def validate_navigation_structure(self):
        """Check that HomeScreen uses proper navigation structure."""
        print("\n🏠 Checking navigation structure...")
        
        # Find HomeScreen
        home_screen_path = self.find_file("home_screen.dart")
        if not home_screen_path:
            self.add_check("HomeScreen Navigation Structure", False, "HomeScreen not found")
            return
            
        try:
            with open(home_screen_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.add_check("HomeScreen Navigation Structure", False, f"Cannot read HomeScreen: {e}")
            return
            
        # Check for proper navigation structure
        navigation_issues = []
        
        # Check for IndexedStack (not recommended for complex navigation)
        if "IndexedStack" in content:
            navigation_issues.append("Uses IndexedStack (not recommended for complex navigation)")
            
        # Check for proper navigation patterns
        proper_patterns = [
            r"Navigator\.push",
            r"Navigator\.pop",
            r"Navigator\.pushReplacement",
            r"Navigator\.pushAndRemoveUntil",
            r"BottomNavigationBar",
            r"Drawer",
            r"TabBar",
            r"TabBarView",
            r"PageView",
            r"CupertinoTabScaffold"
        ]
        
        found_patterns = []
        for pattern in proper_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
                
        if found_patterns:
            self.add_check("HomeScreen Navigation Structure", True, f"Uses proper navigation patterns: {', '.join(found_patterns[:3])}")
        else:
            self.add_check("HomeScreen Navigation Structure", False, "No proper navigation patterns found")
            
        # Check for navigation state management
        state_patterns = [
            r"setState",
            r"Provider\.of",
            r"Consumer",
            r"BlocBuilder",
            r"ValueNotifier",
            r"ChangeNotifier"
        ]
        
        state_found = any(re.search(pattern, content) for pattern in state_patterns)
        if state_found:
            self.add_check("Navigation State Management", True, "Proper state management found")
        else:
            self.add_check("Navigation State Management", False, "No state management found")
            
    def validate_navigation_destinations(self):
        """Verify that all navigation destinations are properly defined."""
        print("\n🎯 Checking navigation destinations...")
        
        # Find all screen files
        screen_files = self.find_files("*_screen.dart")
        
        if not screen_files:
            self.add_check("Navigation Destinations", False, "No screen files found")
            return
            
        # Check for route definitions
        main_dart = self.app_root / "lib" / "main.dart"
        routes_defined = False
        on_generate_route = False
        
        if main_dart.exists():
            try:
                with open(main_dart, 'r', encoding='utf-8') as f:
                    main_content = f.read()
                    
                if "routes:" in main_content or "routes = " in main_content:
                    routes_defined = True
                    
                if "onGenerateRoute" in main_content:
                    on_generate_route = True
                    
            except Exception as e:
                self.add_warning(f"Cannot read main.dart: {e}")
                
        if routes_defined or on_generate_route:
            self.add_check("Route Definitions", True, "Routes are properly defined")
        else:
            self.add_check("Route Definitions", False, "No route definitions found")
            
        # Check for navigation calls in screens
        navigation_calls = 0
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Count navigation calls
                nav_patterns = [
                    r"Navigator\.push",
                    r"Navigator\.pop",
                    r"Navigator\.pushReplacement",
                    r"Navigator\.pushNamed",
                    r"Navigator\.pushReplacementNamed",
                    r"Navigator\.popAndPushNamed"
                ]
                
                for pattern in nav_patterns:
                    navigation_calls += len(re.findall(pattern, content))
                    
            except Exception as e:
                self.add_warning(f"Cannot read {screen_file.name}: {e}")
                
        if navigation_calls > 0:
            self.add_check("Navigation Calls", True, f"Found {navigation_calls} navigation calls")
        else:
            self.add_check("Navigation Calls", False, "No navigation calls found")
            
        # Check for proper screen imports
        home_screen_path = self.find_file("home_screen.dart")
        if home_screen_path:
            try:
                with open(home_screen_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for screen imports
                screen_imports = re.findall(r"import\s+['\"]([^'\"]*screen[^'\"]*)['\"]", content)
                
                if screen_imports:
                    self.add_check("Screen Imports", True, f"Found {len(screen_imports)} screen imports")
                else:
                    self.add_check("Screen Imports", False, "No screen imports found")
                    
            except Exception as e:
                self.add_warning(f"Cannot check screen imports: {e}")
                
    def validate_navigation_icons_labels(self):
        """Ensure that navigation icons and labels are correctly set."""
        print("\n🎨 Checking navigation icons and labels...")
        
        # Find navigation-related files
        navigation_files = []
        
        # Look for files with navigation patterns
        for root, dirs, filenames in os.walk(self.app_root / "lib"):
            for filename in filenames:
                if filename.endswith('.dart'):
                    file_path = Path(root) / filename
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        if any(pattern in content for pattern in [
                            "BottomNavigationBar", "Drawer", "TabBar", "NavigationBar"
                        ]):
                            navigation_files.append(file_path)
                            
                    except Exception:
                        continue
                        
        if not navigation_files:
            self.add_check("Navigation Icons Labels", False, "No navigation components found")
            return
            
        # Check each navigation file
        proper_icons = 0
        proper_labels = 0
        
        for nav_file in navigation_files:
            try:
                with open(nav_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper icon usage
                icon_patterns = [
                    r"Icons\.\w+",
                    r"Icon\s*\(\s*Icons\.\w+",
                    r"icon:\s*Icons\.\w+",
                    r"leading:\s*Icon\s*\(",
                    r"trailing:\s*Icon\s*\("
                ]
                
                for pattern in icon_patterns:
                    if re.search(pattern, content):
                        proper_icons += 1
                        break
                        
                # Check for proper label usage
                label_patterns = [
                    r"label:\s*['\"][^'\"]+['\"]",
                    r"title:\s*['\"][^'\"]+['\"]",
                    r"Text\s*\(\s*['\"][^'\"]+['\"]",
                    r"child:\s*Text\s*\("
                ]
                
                for pattern in label_patterns:
                    if re.search(pattern, content):
                        proper_labels += 1
                        break
                        
            except Exception as e:
                self.add_warning(f"Cannot read {nav_file.name}: {e}")
                
        if proper_icons > 0:
            self.add_check("Navigation Icons", True, f"Found {proper_icons} files with proper icons")
        else:
            self.add_check("Navigation Icons", False, "No proper icons found")
            
        if proper_labels > 0:
            self.add_check("Navigation Labels", True, f"Found {proper_labels} files with proper labels")
        else:
            self.add_check("Navigation Labels", False, "No proper labels found")
            
    def validate_navigation_state_management(self):
        """Validate that navigation state management is working."""
        print("\n🔄 Checking navigation state management...")
        
        # Find state management files
        state_files = []
        
        for root, dirs, filenames in os.walk(self.app_root / "lib"):
            for filename in filenames:
                if filename.endswith('.dart'):
                    file_path = Path(root) / filename
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Check for state management patterns
                        if any(pattern in content for pattern in [
                            "Provider", "Consumer", "BlocBuilder", "ValueNotifier", 
                            "ChangeNotifier", "StatefulWidget", "setState"
                        ]):
                            state_files.append(file_path)
                            
                    except Exception:
                        continue
                        
        if not state_files:
            self.add_check("Navigation State Management", False, "No state management found")
            return
            
        # Check for proper state management patterns
        provider_usage = 0
        consumer_usage = 0
        stateful_widgets = 0
        
        for state_file in state_files:
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if "Provider" in content:
                    provider_usage += 1
                    
                if "Consumer" in content:
                    consumer_usage += 1
                    
                if "StatefulWidget" in content:
                    stateful_widgets += 1
                    
            except Exception as e:
                self.add_warning(f"Cannot read {state_file.name}: {e}")
                
        if provider_usage > 0:
            self.add_check("Provider Usage", True, f"Found {provider_usage} files using Provider")
        else:
            self.add_check("Provider Usage", False, "No Provider usage found")
            
        if consumer_usage > 0:
            self.add_check("Consumer Usage", True, f"Found {consumer_usage} files using Consumer")
        else:
            self.add_check("Consumer Usage", False, "No Consumer usage found")
            
        if stateful_widgets > 0:
            self.add_check("StatefulWidget Usage", True, f"Found {stateful_widgets} StatefulWidget files")
        else:
            self.add_check("StatefulWidget Usage", False, "No StatefulWidget usage found")
            
    def validate_navigation_memory_leaks(self):
        """Check that there are no navigation-related memory leaks."""
        print("\n💾 Checking for navigation memory leaks...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        memory_leak_issues = []
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for common memory leak patterns
                leak_patterns = [
                    r"Timer\s*\([^)]+\)[^;]*$",  # Timer without cancel
                    r"StreamSubscription[^;]*$",  # StreamSubscription without cancel
                    r"AnimationController[^;]*$",  # AnimationController without dispose
                    r"TextEditingController[^;]*$",  # TextEditingController without dispose
                    r"FocusNode[^;]*$",  # FocusNode without dispose
                    r"ScrollController[^;]*$"  # ScrollController without dispose
                ]
                
                for pattern in leak_patterns:
                    if re.search(pattern, content, re.MULTILINE):
                        memory_leak_issues.append(f"{dart_file.name}: Potential memory leak pattern")
                        
                # Check for proper dispose methods
                if "StatefulWidget" in content and "dispose" not in content:
                    memory_leak_issues.append(f"{dart_file.name}: StatefulWidget without dispose method")
                    
            except Exception as e:
                self.add_warning(f"Cannot check {dart_file.name}: {e}")
                
        if memory_leak_issues:
            self.add_check("Navigation Memory Leaks", False, f"Found {len(memory_leak_issues)} potential memory leak issues")
            for issue in memory_leak_issues[:5]:  # Show first 5
                self.add_warning(issue)
        else:
            self.add_check("Navigation Memory Leaks", True, "No memory leak patterns found")
            
    def validate_keyboard_handling(self):
        """Verify that keyboard handling is proper."""
        print("\n⌨️  Checking keyboard handling...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        keyboard_issues = []
        proper_keyboard_handling = 0
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper keyboard handling
                keyboard_patterns = [
                    r"FocusScope\.of\(context\)\.unfocus\(\)",
                    r"FocusManager\.instance\.primaryFocus\?\.unfocus\(\)",
                    r"GestureDetector.*onTap.*unfocus",
                    r"Scaffold.*resizeToAvoidBottomInset",
                    r"MediaQuery\.of\(context\)\.viewInsets\.bottom"
                ]
                
                for pattern in keyboard_patterns:
                    if re.search(pattern, content):
                        proper_keyboard_handling += 1
                        break
                        
                # Check for potential keyboard issues
                if "TextField" in content or "TextFormField" in content:
                    if "FocusNode" not in content and "FocusScope" not in content:
                        keyboard_issues.append(f"{dart_file.name}: TextField without proper focus handling")
                        
            except Exception as e:
                self.add_warning(f"Cannot check {dart_file.name}: {e}")
                
        if proper_keyboard_handling > 0:
            self.add_check("Keyboard Handling", True, f"Found {proper_keyboard_handling} files with proper keyboard handling")
        else:
            self.add_check("Keyboard Handling", False, "No proper keyboard handling found")
            
        if keyboard_issues:
            self.add_check("Keyboard Issues", False, f"Found {len(keyboard_issues)} potential keyboard issues")
            for issue in keyboard_issues[:3]:  # Show first 3
                self.add_warning(issue)
        else:
            self.add_check("Keyboard Issues", True, "No keyboard issues found")
            
    def validate_navigation_animations(self):
        """Ensure that navigation animations work correctly."""
        print("\n🎬 Checking navigation animations...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        animation_usage = 0
        proper_animations = 0
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for animation usage
                animation_patterns = [
                    r"AnimationController",
                    r"Animation<",
                    r"Tween<",
                    r"AnimatedBuilder",
                    r"AnimatedContainer",
                    r"AnimatedOpacity",
                    r"AnimatedPositioned",
                    r"AnimatedSize",
                    r"Hero",
                    r"PageRouteBuilder",
                    r"CustomRoute"
                ]
                
                for pattern in animation_patterns:
                    if re.search(pattern, content):
                        animation_usage += 1
                        break
                        
                # Check for proper animation setup
                if "AnimationController" in content:
                    if "dispose" in content and "vsync" in content:
                        proper_animations += 1
                        
            except Exception as e:
                self.add_warning(f"Cannot check {dart_file.name}: {e}")
                
        if animation_usage > 0:
            self.add_check("Navigation Animations", True, f"Found {animation_usage} files with animations")
        else:
            self.add_check("Navigation Animations", False, "No animations found")
            
        if proper_animations > 0:
            self.add_check("Proper Animation Setup", True, f"Found {proper_animations} files with proper animation setup")
        else:
            self.add_check("Proper Animation Setup", False, "No proper animation setup found")
            
        # Check for Material Design animations
        main_dart = self.app_root / "lib" / "main.dart"
        if main_dart.exists():
            try:
                with open(main_dart, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if "MaterialApp" in content:
                    self.add_check("Material Design Animations", True, "MaterialApp found - animations enabled")
                else:
                    self.add_check("Material Design Animations", False, "No MaterialApp found")
                    
            except Exception as e:
                self.add_warning(f"Cannot check MaterialApp: {e}")
                
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
        print("📊 NAVIGATION VALIDATION RESULTS")
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
            print("\n✅ All navigation validations passed!")
            
        print("="*60)


def main():
    """Main entry point for the navigation validation script."""
    parser = argparse.ArgumentParser(
        description="Validate Flutter app navigation flow and structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Validate navigation in default app
    python3 Python/validate_navigation.py
    
    # Validate navigation in specific app
    APP_ROOT=/path/to/app python3 Python/validate_navigation.py
    
    # Validate with verbose output
    python3 Python/validate_navigation.py --verbose

NAVIGATION VALIDATION CHECKS:
    ✅ HomeScreen navigation structure (not IndexedStack)
    ✅ Navigation destinations properly defined
    ✅ Navigation icons and labels correctly set
    ✅ Navigation state management working
    ✅ No navigation-related memory leaks
    ✅ Proper keyboard handling
    ✅ Navigation animations working correctly

EXIT CODES:
    0    All navigation validations passed
    1    Navigation validation failures found
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
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'generated_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    # Create validator and run validation
    validator = NavigationValidator(app_root)
    success = validator.validate()
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Navigation validation PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Navigation validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
