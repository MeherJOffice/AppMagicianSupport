#!/usr/bin/env python3
"""
Smart Feature Validation Script for AppMagician Pipeline.
Uses AI-driven validation criteria to validate individual features.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from smart_validation_framework import SmartFeatureValidator, get_smart_validation_criteria


def main():
    """Main entry point for the smart feature validation script."""
    parser = argparse.ArgumentParser(
        description="Smart validate individual features in AppMagician pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    # Smart validate main feature
    python3 Python/smart_validate_feature.py main_feature
    
    # Smart validate savings feature with custom app path
    APP_ROOT=/path/to/app python3 Python/smart_validate_feature.py savings
    
    # Smart validate settings feature
    python3 Python/smart_validate_feature.py settings

SMART VALIDATION FEATURES:
    🧠 AI-driven validation criteria based on feature context
    ✅ Adaptive validation that matches actual app structure
    📊 Comprehensive validation with detailed feedback
    🔄 Fallback to basic validation if smart criteria unavailable
    🎯 Context-aware validation for different feature types

EXIT CODES:
    0    All smart validations passed
    1    Smart validation failures found
        """
    )
    
    parser.add_argument(
        'feature_name',
        help='Name of the feature to validate (e.g., "main_feature", "savings", "settings")'
    )
    
    parser.add_argument(
        '--app-root',
        help='Path to the app root directory (default: $HOME/AppMagician/$APP_DIR)'
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
    
    print(f"🧠 Smart validating feature: {args.feature_name}")
    print(f"📁 App root: {app_root}")
    print("="*60)
    
    # Create context for smart validation
    context = {
        "feature_name": args.feature_name,
        "app_root": app_root,
        "app_dir": app_dir
    }
    
    # Get smart validation criteria
    criteria = get_smart_validation_criteria("feature", context)
    
    # Create smart validator
    validator = SmartFeatureValidator(app_root, args.feature_name)
    
    # Run smart validation
    if args.use_smart_validation:
        print("🧠 Using smart AI-driven validation...")
        success = validator.validate_with_criteria(criteria)
        
        if not success and args.fallback_to_basic:
            print("\n⚠️  Smart validation failed, falling back to basic validation...")
            # Import and run basic validation
            from validate_feature import FeatureValidator
            basic_validator = FeatureValidator(app_root, args.feature_name)
            success = basic_validator.validate()
    else:
        print("📋 Using basic validation...")
        # Import and run basic validation
        from validate_feature import FeatureValidator
        basic_validator = FeatureValidator(app_root, args.feature_name)
        success = basic_validator.validate()
    
    # Exit with appropriate code
    if success:
        print(f"\n✅ Feature '{args.feature_name}' validation PASSED")
        sys.exit(0)
    else:
        print(f"\n❌ Feature '{args.feature_name}' validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
