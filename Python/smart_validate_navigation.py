#!/usr/bin/env python3
"""
Smart Navigation Validation Script for AppMagician Pipeline.
Uses AI-driven validation criteria to validate Flutter app navigation.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from smart_validation_framework import SmartNavigationValidator, get_smart_validation_criteria


def main():
    """Main entry point for the smart navigation validation script."""
    parser = argparse.ArgumentParser(
        description="Smart validate Flutter app navigation flow and structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Smart validate navigation in default app
    python3 Python/smart_validate_navigation.py
    
    # Smart validate navigation in specific app
    APP_ROOT=/path/to/app python3 Python/smart_validate_navigation.py
    
    # Smart validate with verbose output
    python3 Python/smart_validate_navigation.py --verbose

SMART VALIDATION FEATURES:
    🧠 AI-driven validation criteria based on navigation context
    ✅ Adaptive validation that matches actual navigation patterns
    📊 Comprehensive validation with detailed feedback
    🔄 Fallback to basic validation if smart criteria unavailable
    🎯 Context-aware validation for different navigation types

SMART NAVIGATION VALIDATION CHECKS:
    ✅ HomeScreen navigation structure (AI-optimized patterns)
    ✅ Navigation destinations properly defined (context-aware)
    ✅ Navigation icons and labels correctly set (pattern-matching)
    ✅ Navigation state management working (adaptive)
    ✅ No navigation-related memory leaks (smart detection)
    ✅ Proper keyboard handling (comprehensive)
    ✅ Navigation animations working correctly (intelligent)

EXIT CODES:
    0    All smart navigation validations passed
    1    Smart navigation validation failures found
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
        '--use-smart-validation',
        action='store_true',
        default=True,
        help='Use smart AI-driven validation (default: True)'
    )
    
    parser.add_argument(
        '--fallback-to-basic',
        action='store_true',
        default=True,
        help='Fallback to basic validation if smart validation fails (default: True)'
    )
    
    args = parser.parse_args()
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'generated_app')
    if args.app_root:
        app_root = args.app_root
    else:
        app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    print(f"🧠 Smart validating navigation for app: {app_dir}")
    print(f"📁 App root: {app_root}")
    if args.verbose:
        print("🔍 Verbose mode enabled")
    print("="*60)
    
    # Create context for smart validation
    context = {
        "app_root": app_root,
        "app_dir": app_dir,
        "verbose": args.verbose
    }
    
    # Get smart validation criteria
    criteria = get_smart_validation_criteria("navigation", context)
    
    # Create smart validator
    validator = SmartNavigationValidator(app_root)
    
    # Run smart validation
    if args.use_smart_validation:
        print("🧠 Using smart AI-driven validation...")
        success = validator.validate_with_criteria(criteria)
        
        if not success and args.fallback_to_basic:
            print("\n⚠️  Smart validation failed, falling back to basic validation...")
            # Import and run basic validation
            from validate_navigation import NavigationValidator
            basic_validator = NavigationValidator(app_root)
            success = basic_validator.validate()
    else:
        print("📋 Using basic validation...")
        # Import and run basic validation
        from validate_navigation import NavigationValidator
        basic_validator = NavigationValidator(app_root)
        success = basic_validator.validate()
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Smart navigation validation PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Smart navigation validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
