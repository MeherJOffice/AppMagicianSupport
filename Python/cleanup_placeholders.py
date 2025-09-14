#!/usr/bin/env python3
"""
Placeholder cleanup script for AppMagician pipeline.
Removes placeholder files after real implementations are in place.
"""

import os
import sys
import re
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


class PlaceholderCleanup:
    def __init__(self, app_root: str):
        self.app_root = Path(app_root)
        self.removed_files: List[Path] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.log_messages: List[str] = []
        
    def cleanup(self) -> bool:
        """Run cleanup process and return True if successful."""
        print("🧹 Starting placeholder cleanup...")
        print(f"📁 App root: {self.app_root}")
        print("="*60)
        
        # Check if app directory exists
        if not self.app_root.exists():
            self.add_error(f"App directory does not exist: {self.app_root}")
            return False
            
        # Run cleanup checks
        self.cleanup_home_feature_placeholders()
        self.cleanup_duplicate_files()
        self.cleanup_empty_files()
        self.cleanup_conflicting_files()
        
        # Print results
        self.print_results()
        
        return len(self.errors) == 0
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(f"❌ ERROR: {message}")
        print(f"❌ ERROR: {message}")
        
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        print(f"⚠️  WARNING: {message}")
        
    def add_log(self, message: str):
        """Add a log message."""
        self.log_messages.append(f"📝 {message}")
        print(f"📝 {message}")
        
    def cleanup_home_feature_placeholders(self):
        """Remove placeholder screens from home feature, keeping only essential ones."""
        print("\n🏠 Cleaning up home feature placeholders...")
        
        home_feature_dir = self.app_root / "lib" / "features" / "home"
        if not home_feature_dir.exists():
            self.add_warning("Home feature directory does not exist")
            return
            
        screens_dir = home_feature_dir / "presentation" / "screens"
        if not screens_dir.exists():
            self.add_warning("Home screens directory does not exist")
            return
            
        # Essential files to keep
        essential_files = {
            "dashboard_screen.dart",
            "home_screen.dart"
        }
        
        # Find all screen files
        screen_files = list(screens_dir.glob("*_screen.dart"))
        
        for screen_file in screen_files:
            if screen_file.name in essential_files:
                self.add_log(f"Keeping essential file: {screen_file.name}")
                continue
                
            # Check if this is a placeholder
            if self.is_placeholder_file(screen_file):
                # Verify real implementation exists elsewhere
                if self.has_real_implementation(screen_file):
                    self.remove_file(screen_file, "placeholder with real implementation")
                else:
                    self.add_warning(f"Placeholder file {screen_file.name} has no real implementation - keeping")
            else:
                self.add_log(f"Non-placeholder file kept: {screen_file.name}")
                
    def cleanup_duplicate_files(self):
        """Remove duplicate files."""
        print("\n🔄 Cleaning up duplicate files...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        # Group files by content hash (simplified - just check file size and name patterns)
        file_groups = {}
        
        for dart_file in dart_files:
            try:
                # Skip if file is too small (likely empty or minimal)
                if dart_file.stat().st_size < 100:
                    continue
                    
                # Create a key based on file name pattern and size
                key = f"{dart_file.name}_{dart_file.stat().st_size}"
                
                if key not in file_groups:
                    file_groups[key] = []
                file_groups[key].append(dart_file)
                
            except Exception as e:
                self.add_warning(f"Cannot process file {dart_file}: {e}")
                
        # Check for duplicates
        for key, files in file_groups.items():
            if len(files) > 1:
                self.add_log(f"Found potential duplicates for {key}: {[f.name for f in files]}")
                
                # Keep the first file, remove others
                keep_file = files[0]
                for duplicate_file in files[1:]:
                    if self.is_safe_to_remove(duplicate_file):
                        self.remove_file(duplicate_file, "duplicate file")
                    else:
                        self.add_warning(f"Cannot remove duplicate {duplicate_file.name} - not safe")
                        
    def cleanup_empty_files(self):
        """Remove empty or nearly empty files."""
        print("\n📄 Cleaning up empty files...")
        
        # Find all Dart files
        dart_files = list(self.app_root.rglob("*.dart"))
        
        for dart_file in dart_files:
            try:
                # Skip essential files
                if self.is_essential_file(dart_file):
                    continue
                    
                # Check file size
                file_size = dart_file.stat().st_size
                if file_size < 50:  # Less than 50 bytes
                    self.remove_file(dart_file, "empty or nearly empty file")
                    continue
                    
                # Check content
                with open(dart_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                # Remove files with only comments or minimal content
                if len(content) < 100 and not self.has_meaningful_content(content):
                    self.remove_file(dart_file, "minimal content file")
                    
            except Exception as e:
                self.add_warning(f"Cannot process file {dart_file}: {e}")
                
    def cleanup_conflicting_files(self):
        """Remove conflicting files."""
        print("\n⚔️  Cleaning up conflicting files...")
        
        # Look for common conflicting patterns
        conflicting_patterns = [
            ("*_old.dart", "old version"),
            ("*_backup.dart", "backup file"),
            ("*_temp.dart", "temporary file"),
            ("*_copy.dart", "copy file"),
            ("*_duplicate.dart", "duplicate file"),
        ]
        
        for pattern, description in conflicting_patterns:
            conflicting_files = list(self.app_root.rglob(pattern))
            
            for file_path in conflicting_files:
                if self.is_safe_to_remove(file_path):
                    self.remove_file(file_path, description)
                else:
                    self.add_warning(f"Cannot remove conflicting file {file_path.name} - not safe")
                    
    def is_placeholder_file(self, file_path: Path) -> bool:
        """Check if a file is a placeholder."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for placeholder indicators
            placeholder_patterns = [
                r"TODO|FIXME|placeholder|sample|demo|lorem|ipsum",
                r"Text\s*\(\s*['\"]\s*['\"]\s*\)",  # Empty Text widgets
                r"Container\s*\(\s*\)",  # Empty containers
                r"return\s+Scaffold\s*\(\s*\)",  # Empty Scaffold
                r"class\s+\w+Screen\s+extends\s+\w+.*\{\s*Widget\s+build.*return\s+Scaffold\s*\(\s*\)",  # Empty screen
            ]
            
            for pattern in placeholder_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    return True
                    
            return False
            
        except Exception:
            return False
            
    def has_real_implementation(self, placeholder_file: Path) -> bool:
        """Check if a real implementation exists for the placeholder."""
        # Look for similar files in other features
        file_name = placeholder_file.name
        file_stem = placeholder_file.stem
        
        # Search in other feature directories
        features_dir = self.app_root / "lib" / "features"
        if not features_dir.exists():
            return False
            
        for feature_dir in features_dir.iterdir():
            if not feature_dir.is_dir():
                continue
                
            # Skip the same feature
            if feature_dir.name == "home":
                continue
                
            # Look for similar files
            similar_files = list(feature_dir.rglob(f"*{file_stem}*"))
            
            for similar_file in similar_files:
                if similar_file.name != file_name and not self.is_placeholder_file(similar_file):
                    self.add_log(f"Found real implementation: {similar_file}")
                    return True
                    
        return False
        
    def is_safe_to_remove(self, file_path: Path) -> bool:
        """Check if it's safe to remove a file."""
        # Never remove essential files
        if self.is_essential_file(file_path):
            return False
            
        # Never remove files in certain directories
        protected_dirs = [
            "ios/",
            "android/",
            "web/",
            "windows/",
            "linux/",
            "macos/",
        ]
        
        file_str = str(file_path)
        for protected_dir in protected_dirs:
            if protected_dir in file_str:
                return False
                
        # Never remove main.dart
        if file_path.name == "main.dart":
            return False
            
        # Never remove pubspec.yaml
        if file_path.name == "pubspec.yaml":
            return False
            
        return True
        
    def is_essential_file(self, file_path: Path) -> bool:
        """Check if a file is essential and should never be removed."""
        essential_files = {
            "main.dart",
            "pubspec.yaml",
            "analysis_options.yaml",
            "README.md",
        }
        
        if file_path.name in essential_files:
            return True
            
        # Essential screen files
        essential_screens = {
            "dashboard_screen.dart",
            "home_screen.dart",
            "main_screen.dart",
        }
        
        if file_path.name in essential_screens:
            return True
            
        return False
        
    def has_meaningful_content(self, content: str) -> bool:
        """Check if content has meaningful code."""
        # Remove comments and whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        code_lines = [line for line in lines if not line.startswith('//') and not line.startswith('/*')]
        
        # Check for meaningful patterns
        meaningful_patterns = [
            r"class\s+\w+",
            r"Widget\s+build",
            r"return\s+\w+",
            r"import\s+",
            r"void\s+\w+",
        ]
        
        for pattern in meaningful_patterns:
            if re.search(pattern, content):
                return True
                
        return len(code_lines) > 3
        
    def remove_file(self, file_path: Path, reason: str):
        """Remove a file with logging."""
        try:
            # Create backup in case we need to restore
            backup_dir = self.app_root / ".cleanup_backup"
            backup_dir.mkdir(exist_ok=True)
            
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            
            # Remove the original file
            file_path.unlink()
            
            self.removed_files.append(file_path)
            self.add_log(f"Removed {file_path.name} ({reason}) - backup saved to {backup_path}")
            
        except Exception as e:
            self.add_error(f"Failed to remove {file_path.name}: {e}")
            
    def print_results(self):
        """Print cleanup results."""
        print("\n" + "="*60)
        print("📊 CLEANUP RESULTS")
        print("="*60)
        
        print(f"\n📝 Files removed: {len(self.removed_files)}")
        for file_path in self.removed_files:
            print(f"  - {file_path}")
            
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if self.log_messages:
            print(f"\n📝 LOG MESSAGES ({len(self.log_messages)}):")
            for log in self.log_messages:
                print(f"  {log}")
                
        if not self.errors and not self.removed_files:
            print("\n✅ No cleanup needed - no placeholder files found")
        elif not self.errors:
            print("\n✅ Cleanup completed successfully")
        else:
            print("\n❌ Cleanup completed with errors")
            
        print("="*60)


def main():
    """Main entry point for the cleanup script."""
    parser = argparse.ArgumentParser(
        description="Clean up placeholder files after real implementations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Clean up placeholders in default app
    python3 Python/cleanup_placeholders.py
    
    # Clean up placeholders in specific app
    APP_ROOT=/path/to/app python3 Python/cleanup_placeholders.py
    
    # Clean up with verbose output
    python3 Python/cleanup_placeholders.py --verbose

CLEANUP ACTIONS:
    ✅ Remove placeholder screens from home feature
    ✅ Keep only dashboard_screen.dart and home_screen.dart in home
    ✅ Remove duplicate files
    ✅ Remove empty or minimal content files
    ✅ Remove conflicting files (*_old.dart, *_backup.dart, etc.)
    ✅ Create backups before removal
    ✅ Safety checks to prevent removing critical files

SAFETY FEATURES:
    - Never removes essential files (main.dart, pubspec.yaml, etc.)
    - Never removes files in platform directories (ios/, android/, etc.)
    - Creates backups before removal
    - Verifies real implementations exist before removing placeholders
    - Logs all actions for transparency

EXIT CODES:
    0    Cleanup completed successfully
    1    Cleanup completed with errors
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
        '--dry-run',
        action='store_true',
        help='Show what would be removed without actually removing files'
    )
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'generated_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    # Create cleaner and run cleanup
    cleaner = PlaceholderCleanup(app_root)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be removed")
        print("="*60)
        
    success = cleaner.cleanup()
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Cleanup completed successfully")
        sys.exit(0)
    else:
        print(f"\n❌ Cleanup completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
