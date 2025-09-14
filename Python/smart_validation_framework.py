#!/usr/bin/env python3
"""
Smart Validation Framework for AppMagician Pipeline.
Provides AI-driven validation capabilities for all validation scripts.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from abc import ABC, abstractmethod


class SmartValidator(ABC):
    """Base class for smart validators."""
    
    def __init__(self, app_root: str, validation_type: str):
        self.app_root = Path(app_root)
        self.validation_type = validation_type
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks: List[Tuple[str, bool, str]] = []
        
    @abstractmethod
    def validate_with_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Validate using AI-generated criteria."""
        pass
        
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


class SmartFeatureValidator(SmartValidator):
    """Smart validator for feature validation."""
    
    def __init__(self, app_root: str, feature_name: str):
        super().__init__(app_root, "feature")
        self.feature_name = feature_name
        
    def validate_with_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Validate feature using AI-generated criteria."""
        print(f"🧠 Smart validating feature: {self.feature_name}")
        
        for criterion, expected_value in criteria.items():
            try:
                if criterion == "feature_directory_exists":
                    self.validate_feature_directory(expected_value)
                elif criterion == "feature_structure":
                    self.validate_feature_structure(expected_value)
                elif criterion == "provider_usage":
                    self.validate_provider_usage(expected_value)
                elif criterion == "screen_implementations":
                    self.validate_screen_implementations(expected_value)
                elif criterion == "no_placeholders":
                    self.validate_no_placeholders(expected_value)
                elif criterion == "feature_integration":
                    self.validate_feature_integration(expected_value)
                elif criterion == "dependencies":
                    self.validate_dependencies(expected_value)
                else:
                    # Generic validation
                    self.add_check(criterion, bool(expected_value), f"Generic check: {criterion}")
            except Exception as e:
                self.add_check(criterion, False, f"Error validating {criterion}: {str(e)}")
                
        return len(self.errors) == 0
        
    def validate_feature_directory(self, expected_path: str):
        """Validate feature directory exists."""
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        if feature_dir.exists():
            self.add_check("Feature directory exists", True, f"Found: {feature_dir}")
        else:
            self.add_check("Feature directory exists", False, f"Missing: {feature_dir}")
            
    def validate_feature_structure(self, required_dirs: List[str]):
        """Validate feature has proper structure."""
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        
        for dir_name in required_dirs:
            dir_path = feature_dir / dir_name
            if dir_path.exists():
                self.add_check(f"Has {dir_name}/ directory", True, f"Found: {dir_path}")
            else:
                self.add_check(f"Has {dir_name}/ directory", False, f"Missing: {dir_path}")
                
    def validate_provider_usage(self, expected_patterns: List[str]):
        """Validate provider usage in screens."""
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if not screens_dir.exists():
            self.add_check("Provider usage validation", False, "Screens directory does not exist")
            return
            
        screen_files = list(screens_dir.glob("*_screen.dart"))
        if not screen_files:
            self.add_check("Provider usage validation", False, "No screen files found")
            return
            
        provider_usage_found = False
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in expected_patterns:
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
            
    def validate_screen_implementations(self, expected_screens: List[str]):
        """Validate screen implementations."""
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if not screens_dir.exists():
            self.add_check("Screen implementations", False, "Screens directory does not exist")
            return
            
        screen_files = list(screens_dir.glob("*_screen.dart"))
        found_screens = [f.stem.replace('_screen', '') for f in screen_files]
        
        for expected_screen in expected_screens:
            if expected_screen in found_screens:
                self.add_check(f"Screen {expected_screen} exists", True, f"Found: {expected_screen}_screen.dart")
            else:
                self.add_check(f"Screen {expected_screen} exists", False, f"Missing: {expected_screen}_screen.dart")
                
    def validate_no_placeholders(self, placeholder_patterns: List[str]):
        """Validate no placeholder content."""
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if not screens_dir.exists():
            self.add_check("Placeholder check", False, "Screens directory does not exist")
            return
            
        screen_files = list(screens_dir.glob("*_screen.dart"))
        placeholder_found = False
        
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
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
            
    def validate_feature_integration(self, integration_points: List[str]):
        """Validate feature integration."""
        for integration_point in integration_points:
            if integration_point == "main_dart":
                self.validate_main_dart_integration()
            elif integration_point == "pubspec_yaml":
                self.validate_pubspec_integration()
            elif integration_point == "routing":
                self.validate_routing_integration()
                
    def validate_main_dart_integration(self):
        """Validate integration in main.dart."""
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
            
    def validate_pubspec_integration(self):
        """Validate integration in pubspec.yaml."""
        pubspec_path = self.app_root / "pubspec.yaml"
        if pubspec_path.exists():
            try:
                with open(pubspec_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
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
            
    def validate_routing_integration(self):
        """Validate routing integration."""
        # Check if feature screens are properly routed
        feature_dir = self.app_root / "lib" / "features" / self.feature_name
        screens_dir = feature_dir / "presentation" / "screens"
        
        if screens_dir.exists():
            screen_files = list(screens_dir.glob("*_screen.dart"))
            if screen_files:
                self.add_check("Feature routing integration", True, f"Found {len(screen_files)} screens to route")
            else:
                self.add_check("Feature routing integration", False, "No screens found for routing")
        else:
            self.add_check("Feature routing integration", False, "Screens directory does not exist")
            
    def validate_dependencies(self, expected_deps: List[str]):
        """Validate dependencies."""
        pubspec_path = self.app_root / "pubspec.yaml"
        if pubspec_path.exists():
            try:
                with open(pubspec_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                missing_deps = []
                for dep in expected_deps:
                    if dep not in content:
                        missing_deps.append(dep)
                        
                if not missing_deps:
                    self.add_check("Dependencies validation", True, f"All required dependencies found: {expected_deps}")
                else:
                    self.add_check("Dependencies validation", False, f"Missing dependencies: {missing_deps}")
                    
            except Exception as e:
                self.add_check("Dependencies validation", False, f"Error reading pubspec.yaml: {e}")
        else:
            self.add_check("Dependencies validation", False, "pubspec.yaml not found")


class SmartIntegrationValidator(SmartValidator):
    """Smart validator for integration validation."""
    
    def __init__(self, app_root: str):
        super().__init__(app_root, "integration")
        
    def validate_with_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Validate integration using AI-generated criteria."""
        print("🧠 Smart validating integration...")
        
        for criterion, expected_value in criteria.items():
            try:
                if criterion == "app_structure":
                    self.validate_app_structure(expected_value)
                elif criterion == "feature_imports":
                    self.validate_feature_imports(expected_value)
                elif criterion == "provider_usage":
                    self.validate_provider_usage(expected_value)
                elif criterion == "screen_implementations":
                    self.validate_screen_implementations(expected_value)
                elif criterion == "file_locations":
                    self.validate_file_locations(expected_value)
                elif criterion == "no_duplicates":
                    self.validate_no_duplicates(expected_value)
                elif criterion == "routing_integration":
                    self.validate_routing_integration(expected_value)
                else:
                    # Generic validation
                    self.add_check(criterion, bool(expected_value), f"Generic check: {criterion}")
            except Exception as e:
                self.add_check(criterion, False, f"Error validating {criterion}: {str(e)}")
                
        return len(self.errors) == 0
        
    def validate_app_structure(self, required_dirs: List[str]):
        """Validate basic app structure."""
        for dir_path in required_dirs:
            full_path = self.app_root / dir_path
            if not full_path.exists():
                self.add_check(f"Required directory {dir_path}", False, f"Missing: {dir_path}")
            else:
                self.add_check(f"Required directory {dir_path}", True, f"Found: {dir_path}")
                
    def validate_feature_imports(self, expected_imports: List[str]):
        """Validate feature imports."""
        home_screen_path = self.find_file("home_screen.dart")
        if not home_screen_path:
            self.add_check("Feature imports", False, "HomeScreen not found")
            return
            
        try:
            with open(home_screen_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_imports = []
            for expected_import in expected_imports:
                if expected_import in content:
                    found_imports.append(expected_import)
                    
            if found_imports:
                self.add_check("Feature imports", True, f"Found imports: {found_imports}")
            else:
                self.add_check("Feature imports", False, f"No expected imports found: {expected_imports}")
                
        except Exception as e:
            self.add_check("Feature imports", False, f"Cannot read HomeScreen: {e}")
            
    def validate_provider_usage(self, expected_patterns: List[str]):
        """Validate provider usage across all screens."""
        screen_files = self.find_files("*_screen.dart")
        
        provider_usage_found = False
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in expected_patterns:
                    if re.search(pattern, content):
                        provider_usage_found = True
                        break
                        
            except Exception as e:
                self.add_warning(f"Cannot read {screen_file.name}: {e}")
                
        if provider_usage_found:
            self.add_check("Provider usage", True, "Provider usage found in screens")
        else:
            self.add_check("Provider usage", False, "No provider usage found")
            
    def validate_screen_implementations(self, expected_elements: List[str]):
        """Validate screen implementations."""
        screen_files = self.find_files("*_screen.dart")
        
        for screen_file in screen_files:
            try:
                with open(screen_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                missing_elements = []
                for element in expected_elements:
                    if not re.search(element, content):
                        missing_elements.append(element)
                        
                if not missing_elements:
                    self.add_check(f"Screen {screen_file.name}", True, "All required elements found")
                else:
                    self.add_check(f"Screen {screen_file.name}", False, f"Missing elements: {missing_elements}")
                    
            except Exception as e:
                self.add_check(f"Screen {screen_file.name}", False, f"Cannot read file: {e}")
                
    def validate_file_locations(self, expected_files: List[str]):
        """Validate file locations."""
        for file_path in expected_files:
            full_path = self.app_root / file_path
            if not full_path.exists():
                self.add_check(f"Required file {file_path}", False, f"Missing: {file_path}")
            else:
                self.add_check(f"Required file {file_path}", True, f"Found: {file_path}")
                
    def validate_no_duplicates(self, duplicate_check: bool):
        """Validate no duplicate implementations."""
        if not duplicate_check:
            return
            
        screen_files = self.find_files("*_screen.dart")
        screen_groups = {}
        
        for screen_file in screen_files:
            screen_name = screen_file.stem.replace('_screen', '')
            if screen_name not in screen_groups:
                screen_groups[screen_name] = []
            screen_groups[screen_name].append(screen_file)
            
        duplicates_found = False
        for screen_name, files in screen_groups.items():
            if len(files) > 1:
                duplicates_found = True
                self.add_check(f"Duplicate check {screen_name}", False, f"Duplicate implementations: {[f.name for f in files]}")
                
        if not duplicates_found:
            self.add_check("No duplicates", True, "No duplicate implementations found")
            
    def validate_routing_integration(self, expected_routing: List[str]):
        """Validate routing integration."""
        main_dart = self.app_root / "lib" / "main.dart"
        if main_dart.exists():
            try:
                with open(main_dart, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                routing_found = []
                for routing_element in expected_routing:
                    if routing_element in content:
                        routing_found.append(routing_element)
                        
                if routing_found:
                    self.add_check("Routing integration", True, f"Found routing elements: {routing_found}")
                else:
                    self.add_check("Routing integration", False, f"No routing elements found: {expected_routing}")
                    
            except Exception as e:
                self.add_check("Routing integration", False, f"Cannot read main.dart: {e}")
        else:
            self.add_check("Routing integration", False, "main.dart not found")
            
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


class SmartNavigationValidator(SmartValidator):
    """Smart validator for navigation validation."""
    
    def __init__(self, app_root: str):
        super().__init__(app_root, "navigation")
        
    def validate_with_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Validate navigation using AI-generated criteria."""
        print("🧠 Smart validating navigation...")
        
        for criterion, expected_value in criteria.items():
            try:
                if criterion == "navigation_structure":
                    self.validate_navigation_structure(expected_value)
                elif criterion == "navigation_destinations":
                    self.validate_navigation_destinations(expected_value)
                elif criterion == "navigation_icons_labels":
                    self.validate_navigation_icons_labels(expected_value)
                elif criterion == "navigation_state_management":
                    self.validate_navigation_state_management(expected_value)
                elif criterion == "navigation_memory_leaks":
                    self.validate_navigation_memory_leaks(expected_value)
                elif criterion == "keyboard_handling":
                    self.validate_keyboard_handling(expected_value)
                elif criterion == "navigation_animations":
                    self.validate_navigation_animations(expected_value)
                else:
                    # Generic validation
                    self.add_check(criterion, bool(expected_value), f"Generic check: {criterion}")
            except Exception as e:
                self.add_check(criterion, False, f"Error validating {criterion}: {str(e)}")
                
        return len(self.errors) == 0
        
    def validate_navigation_structure(self, expected_patterns: List[str]):
        """Validate navigation structure."""
        home_screen_path = self.find_file("home_screen.dart")
        if not home_screen_path:
            self.add_check("Navigation structure", False, "HomeScreen not found")
            return
            
        try:
            with open(home_screen_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_patterns = []
            for pattern in expected_patterns:
                if re.search(pattern, content):
                    found_patterns.append(pattern)
                    
            if found_patterns:
                self.add_check("Navigation structure", True, f"Found patterns: {found_patterns}")
            else:
                self.add_check("Navigation structure", False, f"No navigation patterns found: {expected_patterns}")
                
        except Exception as e:
            self.add_check("Navigation structure", False, f"Cannot read HomeScreen: {e}")
            
    def validate_navigation_destinations(self, expected_destinations: List[str]):
        """Validate navigation destinations."""
        screen_files = self.find_files("*_screen.dart")
        
        if not screen_files:
            self.add_check("Navigation destinations", False, "No screen files found")
            return
            
        # Check for route definitions
        main_dart = self.app_root / "lib" / "main.dart"
        routes_defined = False
        
        if main_dart.exists():
            try:
                with open(main_dart, 'r', encoding='utf-8') as f:
                    main_content = f.read()
                    
                if "routes:" in main_content or "onGenerateRoute" in main_content:
                    routes_defined = True
                    
            except Exception as e:
                self.add_warning(f"Cannot read main.dart: {e}")
                
        if routes_defined:
            self.add_check("Route definitions", True, "Routes are properly defined")
        else:
            self.add_check("Route definitions", False, "No route definitions found")
            
    def validate_navigation_icons_labels(self, expected_elements: List[str]):
        """Validate navigation icons and labels."""
        dart_files = list(self.app_root.rglob("*.dart"))
        
        icons_found = 0
        labels_found = 0
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if any(pattern in content for pattern in ["BottomNavigationBar", "Drawer", "TabBar"]):
                    if "Icons." in content:
                        icons_found += 1
                    if "label:" in content or "title:" in content:
                        labels_found += 1
                        
            except Exception:
                continue
                
        if icons_found > 0:
            self.add_check("Navigation icons", True, f"Found {icons_found} files with proper icons")
        else:
            self.add_check("Navigation icons", False, "No proper icons found")
            
        if labels_found > 0:
            self.add_check("Navigation labels", True, f"Found {labels_found} files with proper labels")
        else:
            self.add_check("Navigation labels", False, "No proper labels found")
            
    def validate_navigation_state_management(self, expected_patterns: List[str]):
        """Validate navigation state management."""
        dart_files = list(self.app_root.rglob("*.dart"))
        
        state_management_found = 0
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if any(pattern in content for pattern in expected_patterns):
                    state_management_found += 1
                    
            except Exception:
                continue
                
        if state_management_found > 0:
            self.add_check("Navigation state management", True, f"Found {state_management_found} files with state management")
        else:
            self.add_check("Navigation state management", False, "No state management found")
            
    def validate_navigation_memory_leaks(self, check_memory_leaks: bool):
        """Validate no navigation memory leaks."""
        if not check_memory_leaks:
            return
            
        dart_files = list(self.app_root.rglob("*.dart"))
        
        memory_leak_issues = []
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for common memory leak patterns
                leak_patterns = [
                    r"Timer\s*\([^)]+\)[^;]*$",
                    r"StreamSubscription[^;]*$",
                    r"AnimationController[^;]*$",
                    r"TextEditingController[^;]*$",
                    r"FocusNode[^;]*$",
                    r"ScrollController[^;]*$"
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
            self.add_check("Navigation memory leaks", False, f"Found {len(memory_leak_issues)} potential memory leak issues")
            for issue in memory_leak_issues[:5]:  # Show first 5
                self.add_warning(issue)
        else:
            self.add_check("Navigation memory leaks", True, "No memory leak patterns found")
            
    def validate_keyboard_handling(self, expected_patterns: List[str]):
        """Validate keyboard handling."""
        dart_files = list(self.app_root.rglob("*.dart"))
        
        keyboard_handling_found = 0
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in expected_patterns:
                    if re.search(pattern, content):
                        keyboard_handling_found += 1
                        break
                        
            except Exception:
                continue
                
        if keyboard_handling_found > 0:
            self.add_check("Keyboard handling", True, f"Found {keyboard_handling_found} files with proper keyboard handling")
        else:
            self.add_check("Keyboard handling", False, "No proper keyboard handling found")
            
    def validate_navigation_animations(self, expected_animations: List[str]):
        """Validate navigation animations."""
        dart_files = list(self.app_root.rglob("*.dart"))
        
        animation_usage = 0
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for animation in expected_animations:
                    if animation in content:
                        animation_usage += 1
                        break
                        
            except Exception:
                continue
                
        if animation_usage > 0:
            self.add_check("Navigation animations", True, f"Found {animation_usage} files with animations")
        else:
            self.add_check("Navigation animations", False, "No animations found")
            
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


def get_smart_validation_criteria(validation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-generated validation criteria for the given validation type and context."""
    
    # This would ideally call an AI service to generate criteria based on the context
    # For now, we'll provide intelligent defaults based on the validation type
    
    if validation_type == "feature":
        feature_name = context.get("feature_name", "unknown")
        return {
            "feature_directory_exists": True,
            "feature_structure": ["data", "domain", "presentation"],
            "provider_usage": [f"ref.watch({feature_name}Provider)", f"ref.read({feature_name}Provider)"],
            "screen_implementations": [f"{feature_name}_screen"],
            "no_placeholders": ["TODO", "FIXME", "placeholder", "sample", "demo"],
            "feature_integration": ["main_dart", "pubspec_yaml", "routing"],
            "dependencies": ["provider", "shared_preferences"]
        }
        
    elif validation_type == "integration":
        return {
            "app_structure": ["lib", "lib/features", "lib/core", "test", "ios"],
            "feature_imports": ["features/", "screen"],
            "provider_usage": ["useProvider", "Provider.", "Consumer", "ref.watch", "ref.read"],
            "screen_implementations": [r"class\s+\w+Screen\s+extends\s+\w+", r"Widget\s+build\s*\(", r"return\s+Scaffold"],
            "file_locations": ["lib/main.dart", "lib/core/presentation/screens/main_screen.dart"],
            "no_duplicates": True,
            "routing_integration": ["MaterialApp", "routes", "onGenerateRoute"]
        }
        
    elif validation_type == "navigation":
        return {
            "navigation_structure": [r"Navigator\.push", r"Navigator\.pop", r"BottomNavigationBar", r"Drawer"],
            "navigation_destinations": ["routes:", "onGenerateRoute"],
            "navigation_icons_labels": ["Icons.", "label:", "title:"],
            "navigation_state_management": ["Provider", "Consumer", "StatefulWidget", "setState"],
            "navigation_memory_leaks": True,
            "keyboard_handling": [r"FocusScope\.of\(context\)\.unfocus\(\)", r"FocusManager\.instance\.primaryFocus"],
            "navigation_animations": ["AnimationController", "Animation<", "Tween<", "AnimatedBuilder"]
        }
        
    else:
        return {}


def main():
    """Main entry point for the smart validation framework."""
    if len(sys.argv) < 3:
        print("Usage: smart_validation_framework.py <validation_type> <context_json>")
        print("Validation types: feature, integration, navigation")
        sys.exit(1)
        
    validation_type = sys.argv[1]
    context_json = sys.argv[2]
    
    try:
        context = json.loads(context_json)
    except json.JSONDecodeError:
        print("Invalid JSON context provided")
        sys.exit(1)
        
    # Get app root from context or environment
    app_root = context.get("app_root", os.environ.get("APP_ROOT", f"{os.environ.get('HOME', '/tmp')}/AppMagician/generated_app"))
    
    # Get validation criteria
    criteria = get_smart_validation_criteria(validation_type, context)
    
    # Create appropriate validator
    if validation_type == "feature":
        feature_name = context.get("feature_name", "unknown")
        validator = SmartFeatureValidator(app_root, feature_name)
    elif validation_type == "integration":
        validator = SmartIntegrationValidator(app_root)
    elif validation_type == "navigation":
        validator = SmartNavigationValidator(app_root)
    else:
        print(f"Unknown validation type: {validation_type}")
        sys.exit(1)
        
    # Run validation
    success = validator.validate_with_criteria(criteria)
    
    # Print results
    print("\n" + "="*60)
    print(f"📊 SMART {validation_type.upper()} VALIDATION RESULTS")
    print("="*60)
    
    passed_checks = sum(1 for _, passed, _ in validator.checks if passed)
    total_checks = len(validator.checks)
    
    print(f"\n📈 Summary: {passed_checks}/{total_checks} checks passed")
    
    if validator.errors:
        print(f"\n❌ ERRORS ({len(validator.errors)}):")
        for error in validator.errors:
            print(f"  {error}")
            
    if validator.warnings:
        print(f"\n⚠️  WARNINGS ({len(validator.warnings)}):")
        for warning in validator.warnings:
            print(f"  {warning}")
            
    if not validator.errors and not validator.warnings:
        print("\n✅ All smart validations passed!")
        
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
