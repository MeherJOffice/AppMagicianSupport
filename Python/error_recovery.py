#!/usr/bin/env python3
"""
Error recovery script for AppMagician pipeline.
Handles common pipeline failures and automatically fixes them.
"""

import os
import sys
import re
import shutil
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from datetime import datetime


class ErrorRecovery:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.errors: List[Dict] = []
        self.fixes_applied: List[Dict] = []
        self.backup_dir: Optional[Path] = None
        self.recovery_log: List[Dict] = []
        self.start_time = datetime.now()
        
    def recover_from_errors(self) -> bool:
        """Run error recovery process and return True if successful."""
        print("🔧 Starting error recovery...")
        print(f"📁 App root: {self.app_root}")
        print("="*60)
        
        # Check if app directory exists
        if not self.app_root.exists():
            print(f"❌ ERROR: App directory does not exist: {self.app_root}")
            return False
            
        # Change to app directory
        os.chdir(self.app_root)
        
        # Create backup before attempting fixes
        if not self.create_backup():
            print("❌ Failed to create backup - aborting recovery")
            return False
            
        # Detect common error patterns
        self.detect_common_errors()
        
        # Apply automatic fixes
        self.apply_automatic_fixes()
        
        # Verify fixes worked
        success = self.verify_fixes()
        
        # Log recovery results
        self.log_recovery_results()
        
        return success
    
    def create_backup(self) -> bool:
        """Create backup of working state before attempting fixes."""
        print("\n💾 Creating backup...")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = self.app_root.parent / f"{self.app_root.name}_backup_{timestamp}"
            
            # Copy entire app directory
            shutil.copytree(self.app_root, self.backup_dir)
            
            print(f"✅ Backup created: {self.backup_dir}")
            self.log_recovery_action("backup_created", f"Backup created at {self.backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            self.log_recovery_action("backup_failed", f"Backup failed: {e}")
            return False
    
    def detect_common_errors(self):
        """Detect common error patterns in the codebase."""
        print("\n🔍 Detecting common errors...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        for dart_file in dart_files:
            try:
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for common error patterns
                self.check_missing_imports(dart_file, content)
                self.check_provider_issues(dart_file, content)
                self.check_navigation_problems(dart_file, content)
                self.check_localization_issues(dart_file, content)
                self.check_syntax_errors(dart_file, content)
                self.check_state_management_issues(dart_file, content)
                
            except Exception as e:
                self.add_error("file_read_error", f"Cannot read {dart_file}: {e}")
                
        print(f"📊 Detected {len(self.errors)} error patterns")
    
    def check_missing_imports(self, file_path: Path, content: str):
        """Check for missing import statements."""
        # Common Flutter imports that might be missing
        common_imports = {
            'MaterialApp': 'package:flutter/material.dart',
            'Scaffold': 'package:flutter/material.dart',
            'AppBar': 'package:flutter/material.dart',
            'Text': 'package:flutter/material.dart',
            'Container': 'package:flutter/material.dart',
            'Column': 'package:flutter/material.dart',
            'Row': 'package:flutter/material.dart',
            'ElevatedButton': 'package:flutter/material.dart',
            'TextField': 'package:flutter/material.dart',
            'Navigator': 'package:flutter/material.dart',
            'Provider': 'package:provider/provider.dart',
            'Consumer': 'package:provider/provider.dart',
            'ChangeNotifier': 'package:flutter/foundation.dart',
            'SharedPreferences': 'package:shared_preferences/shared_preferences.dart',
        }
        
        for widget, import_path in common_imports.items():
            if widget in content and f"import '{import_path}'" not in content:
                self.add_error("missing_import", f"{file_path.name}: Missing import for {widget}", {
                    'file': str(file_path),
                    'widget': widget,
                    'import_path': import_path
                })
    
    def check_provider_issues(self, file_path: Path, content: str):
        """Check for provider-related issues."""
        # Check for provider usage without proper imports
        if 'Provider' in content or 'Consumer' in content:
            if 'package:provider/provider.dart' not in content:
                self.add_error("provider_import_missing", f"{file_path.name}: Provider usage without import", {
                    'file': str(file_path),
                    'issue': 'provider_import_missing'
                })
        
        # Check for ChangeNotifier without proper import
        if 'ChangeNotifier' in content:
            if 'package:flutter/foundation.dart' not in content:
                self.add_error("changenotifier_import_missing", f"{file_path.name}: ChangeNotifier without import", {
                    'file': str(file_path),
                    'issue': 'changenotifier_import_missing'
                })
        
        # Check for provider usage patterns
        provider_patterns = [
            r'Provider\.of<[^>]+>\(context\)',
            r'Consumer<[^>]+>',
            r'ChangeNotifierProvider',
            r'MultiProvider'
        ]
        
        for pattern in provider_patterns:
            if re.search(pattern, content):
                if 'package:provider/provider.dart' not in content:
                    self.add_error("provider_pattern_missing_import", f"{file_path.name}: Provider pattern without import", {
                        'file': str(file_path),
                        'pattern': pattern,
                        'issue': 'provider_pattern_missing_import'
                    })
    
    def check_navigation_problems(self, file_path: Path, content: str):
        """Check for navigation-related issues."""
        # Check for Navigator usage without proper import
        if 'Navigator' in content:
            if 'package:flutter/material.dart' not in content:
                self.add_error("navigator_import_missing", f"{file_path.name}: Navigator usage without import", {
                    'file': str(file_path),
                    'issue': 'navigator_import_missing'
                })
        
        # Check for common navigation patterns
        navigation_patterns = [
            r'Navigator\.push',
            r'Navigator\.pop',
            r'Navigator\.pushNamed',
            r'Navigator\.pushReplacement'
        ]
        
        for pattern in navigation_patterns:
            if re.search(pattern, content):
                if 'package:flutter/material.dart' not in content:
                    self.add_error("navigation_pattern_missing_import", f"{file_path.name}: Navigation pattern without import", {
                        'file': str(file_path),
                        'pattern': pattern,
                        'issue': 'navigation_pattern_missing_import'
                    })
    
    def check_localization_issues(self, file_path: Path, content: str):
        """Check for localization-related issues."""
        # Check for hardcoded strings
        hardcoded_patterns = [
            r'Text\s*\(\s*["\'][^"\']+["\']',
            r'title:\s*["\'][^"\']+["\']',
            r'label:\s*["\'][^"\']+["\']'
        ]
        
        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Skip very short strings and common patterns
                if len(match) > 5 and not re.match(r'^[A-Z_]+$', match):
                    self.add_error("hardcoded_string", f"{file_path.name}: Hardcoded string found", {
                        'file': str(file_path),
                        'string': match,
                        'issue': 'hardcoded_string'
                    })
    
    def check_syntax_errors(self, file_path: Path, content: str):
        """Check for common syntax errors."""
        # Check for missing semicolons
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.endswith((';', '{', '}', ':', ',')) and not line.startswith(('//', '/*', '*')):
                # Skip certain patterns that don't need semicolons
                if not re.match(r'^(import|export|part|library|typedef|class|enum|mixin|extension)', line):
                    if re.search(r'[a-zA-Z0-9_]\s*$', line):  # Ends with alphanumeric
                        self.add_error("missing_semicolon", f"{file_path.name}:{i+1}: Missing semicolon", {
                            'file': str(file_path),
                            'line': i + 1,
                            'content': line,
                            'issue': 'missing_semicolon'
                        })
    
    def check_state_management_issues(self, file_path: Path, content: str):
        """Check for state management issues."""
        # Check for setState without StatefulWidget
        if 'setState' in content:
            if 'StatefulWidget' not in content:
                self.add_error("setstate_without_statefulwidget", f"{file_path.name}: setState without StatefulWidget", {
                    'file': str(file_path),
                    'issue': 'setstate_without_statefulwidget'
                })
        
        # Check for dispose method without StatefulWidget
        if 'dispose' in content:
            if 'StatefulWidget' not in content:
                self.add_error("dispose_without_statefulwidget", f"{file_path.name}: dispose without StatefulWidget", {
                    'file': str(file_path),
                    'issue': 'dispose_without_statefulwidget'
                })
    
    def apply_automatic_fixes(self):
        """Apply automatic fixes for detected errors."""
        print(f"\n🔧 Applying automatic fixes for {len(self.errors)} errors...")
        
        # Group errors by file for efficient fixing
        errors_by_file = {}
        for error in self.errors:
            file_path = error.get('details', {}).get('file')
            if file_path:
                if file_path not in errors_by_file:
                    errors_by_file[file_path] = []
                errors_by_file[file_path].append(error)
        
        # Apply fixes file by file
        for file_path, file_errors in errors_by_file.items():
            self.fix_file_errors(file_path, file_errors)
    
    def fix_file_errors(self, file_path: str, errors: List[Dict]):
        """Fix errors in a specific file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return
                
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_applied = []
            
            for error in errors:
                error_type = error['type']
                details = error.get('details', {})
                
                if error_type == 'missing_import':
                    content = self.fix_missing_import(content, details)
                    fixes_applied.append(f"Added import for {details['widget']}")
                    
                elif error_type == 'provider_import_missing':
                    content = self.fix_provider_import(content)
                    fixes_applied.append("Added provider import")
                    
                elif error_type == 'changenotifier_import_missing':
                    content = self.fix_changenotifier_import(content)
                    fixes_applied.append("Added ChangeNotifier import")
                    
                elif error_type == 'navigator_import_missing':
                    content = self.fix_navigator_import(content)
                    fixes_applied.append("Added Navigator import")
                    
                elif error_type == 'missing_semicolon':
                    content = self.fix_missing_semicolon(content, details)
                    fixes_applied.append(f"Added semicolon at line {details['line']}")
            
            # Write fixed content if changes were made
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append({
                    'file': file_path,
                    'fixes': fixes_applied,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Fixed {len(fixes_applied)} issues in {path.name}")
                self.log_recovery_action("file_fixed", f"Fixed {len(fixes_applied)} issues in {path.name}")
                
        except Exception as e:
            print(f"❌ Failed to fix {file_path}: {e}")
            self.log_recovery_action("fix_failed", f"Failed to fix {file_path}: {e}")
    
    def fix_missing_import(self, content: str, details: Dict) -> str:
        """Fix missing import statement."""
        import_path = details['import_path']
        widget = details['widget']
        
        # Check if import already exists
        if f"import '{import_path}'" in content:
            return content
        
        # Find the best place to add the import
        lines = content.split('\n')
        import_section_end = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                import_section_end = i + 1
        
        # Insert the import
        lines.insert(import_section_end, f"import '{import_path}';")
        
        return '\n'.join(lines)
    
    def fix_provider_import(self, content: str) -> str:
        """Fix missing provider import."""
        return self.fix_missing_import(content, {
            'import_path': 'package:provider/provider.dart',
            'widget': 'Provider'
        })
    
    def fix_changenotifier_import(self, content: str) -> str:
        """Fix missing ChangeNotifier import."""
        return self.fix_missing_import(content, {
            'import_path': 'package:flutter/foundation.dart',
            'widget': 'ChangeNotifier'
        })
    
    def fix_navigator_import(self, content: str) -> str:
        """Fix missing Navigator import."""
        return self.fix_missing_import(content, {
            'import_path': 'package:flutter/material.dart',
            'widget': 'Navigator'
        })
    
    def fix_missing_semicolon(self, content: str, details: Dict) -> str:
        """Fix missing semicolon."""
        lines = content.split('\n')
        line_num = details['line'] - 1
        
        if line_num < len(lines):
            line = lines[line_num].strip()
            if line and not line.endswith(';'):
                lines[line_num] = lines[line_num].rstrip() + ';'
        
        return '\n'.join(lines)
    
    def verify_fixes(self) -> bool:
        """Verify that fixes worked by running flutter analyze."""
        print("\n🔍 Verifying fixes...")
        
        try:
            # Run flutter analyze
            result = subprocess.run(
                ['flutter', 'analyze'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ All fixes verified - flutter analyze passed")
                self.log_recovery_action("verification_passed", "Flutter analyze passed after fixes")
                return True
            else:
                # Check if we reduced the number of errors
                error_count = len(re.findall(r"error •", result.stdout + result.stderr))
                if error_count < len(self.errors):
                    print(f"⚠️  Reduced errors from {len(self.errors)} to {error_count}")
                    self.log_recovery_action("partial_success", f"Reduced errors from {len(self.errors)} to {error_count}")
                    return True
                else:
                    print(f"❌ Fixes did not resolve errors: {error_count} errors remain")
                    self.log_recovery_action("verification_failed", f"Fixes did not resolve errors: {error_count} errors remain")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to verify fixes: {e}")
            self.log_recovery_action("verification_error", f"Failed to verify fixes: {e}")
            return False
    
    def rollback_changes(self) -> bool:
        """Rollback changes using backup."""
        print("\n🔄 Rolling back changes...")
        
        if not self.backup_dir or not self.backup_dir.exists():
            print("❌ No backup available for rollback")
            return False
        
        try:
            # Remove current app directory
            shutil.rmtree(self.app_root)
            
            # Restore from backup
            shutil.copytree(self.backup_dir, self.app_root)
            
            print("✅ Changes rolled back successfully")
            self.log_recovery_action("rollback_success", "Changes rolled back successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to rollback: {e}")
            self.log_recovery_action("rollback_failed", f"Failed to rollback: {e}")
            return False
    
    def add_error(self, error_type: str, message: str, details: Dict = None):
        """Add an error to the error list."""
        error = {
            'type': error_type,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error)
    
    def log_recovery_action(self, action: str, message: str):
        """Log a recovery action."""
        log_entry = {
            'action': action,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.recovery_log.append(log_entry)
    
    def log_recovery_results(self):
        """Log comprehensive recovery results."""
        print("\n" + "="*60)
        print("📊 ERROR RECOVERY REPORT")
        print("="*60)
        
        duration = datetime.now() - self.start_time
        
        print(f"\n⏱️  Duration: {duration.total_seconds():.1f} seconds")
        print(f"🔍 Errors detected: {len(self.errors)}")
        print(f"🔧 Fixes applied: {len(self.fixes_applied)}")
        
        # Print error summary
        if self.errors:
            print(f"\n❌ ERRORS DETECTED:")
            error_types = {}
            for error in self.errors:
                error_type = error['type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count}")
        
        # Print fixes summary
        if self.fixes_applied:
            print(f"\n✅ FIXES APPLIED:")
            for fix in self.fixes_applied:
                print(f"  {fix['file']}: {', '.join(fix['fixes'])}")
        
        # Print recovery log
        if self.recovery_log:
            print(f"\n📝 RECOVERY LOG:")
            for log_entry in self.recovery_log:
                print(f"  {log_entry['timestamp']}: {log_entry['action']} - {log_entry['message']}")
        
        # Save detailed log to file
        self.save_recovery_log()
        
        print("="*60)
    
    def save_recovery_log(self):
        """Save detailed recovery log to file."""
        try:
            log_file = self.app_root / "error_recovery_log.json"
            log_data = {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'errors_detected': len(self.errors),
                'fixes_applied': len(self.fixes_applied),
                'errors': self.errors,
                'fixes': self.fixes_applied,
                'recovery_log': self.recovery_log,
                'backup_location': str(self.backup_dir) if self.backup_dir else None
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Detailed log saved to: {log_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to save log: {e}")


def main():
    """Main entry point for the error recovery script."""
    parser = argparse.ArgumentParser(
        description="Handle common pipeline failures and automatically fix them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Run error recovery on default app
    python3 Python/error_recovery.py
    
    # Run error recovery on specific app
    APP_ROOT=/path/to/app python3 Python/error_recovery.py
    
    # Run with rollback on failure
    python3 Python/error_recovery.py --rollback-on-failure

ERROR RECOVERY FEATURES:
    ✅ Detect common error patterns (missing imports, provider issues, navigation problems)
    ✅ Automatically fix common issues (update imports, fix provider usage, etc.)
    ✅ Provide detailed error analysis and suggested fixes
    ✅ Create backup of working state before attempting fixes
    ✅ Log all recovery attempts and their results
    ✅ Include rollback functionality if fixes fail

EXIT CODES:
    0    Error recovery successful
    1    Error recovery failed
        """
    )
    
    parser.add_argument(
        '--app-root',
        help='Path to the app root directory (default: $HOME/AppMagician/$APP_DIR)'
    )
    
    parser.add_argument(
        '--rollback-on-failure',
        action='store_true',
        help='Rollback changes if recovery fails'
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
    
    # Create recovery instance and run recovery
    recovery = ErrorRecovery(app_root)
    success = recovery.recover_from_errors()
    
    # Rollback if requested and recovery failed
    if not success and args.rollback_on_failure:
        print("\n🔄 Recovery failed - attempting rollback...")
        rollback_success = recovery.rollback_changes()
        if rollback_success:
            print("✅ Rollback completed successfully")
        else:
            print("❌ Rollback failed")
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Error recovery PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Error recovery FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
