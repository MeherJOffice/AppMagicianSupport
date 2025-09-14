#!/usr/bin/env python3
"""
Smart Integration Validation Script for AppMagician Pipeline.
Uses AI-driven validation criteria to validate app integration.
"""

import os
import sys
import json
from pathlib import Path
from smart_validation_framework import SmartIntegrationValidator, get_smart_validation_criteria


def main():
    """Main entry point for the smart integration validation script."""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
🧠 Smart Integration Validation Script for AppMagician Pipeline

USAGE:
    python3 Python/smart_validate_integration.py [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    --use-smart-validation    Use smart AI-driven validation (default: True)
    --fallback-to-basic      Fallback to basic validation if smart validation fails (default: True)

ENVIRONMENT VARIABLES:
    APP_DIR             App directory name (default: 'generated_app')
    APP_ROOT            Full path to app root (default: '$HOME/AppMagician/$APP_DIR')

SMART VALIDATION FEATURES:
    🧠 AI-driven validation criteria based on app context
    ✅ Adaptive validation that matches actual app structure
    📊 Comprehensive validation with detailed feedback
    🔄 Fallback to basic validation if smart criteria unavailable
    🎯 Context-aware validation for different app types

SMART VALIDATION CHECKS:
    ✅ App structure and required directories (AI-optimized)
    ✅ Feature screen imports and file existence (context-aware)
    ✅ Provider usage in screens (pattern-matching)
    ✅ Screen implementations and required elements (adaptive)
    ✅ File locations and core files (intelligent)
    ✅ Duplicate screen implementations (smart detection)
    ✅ Routing integration (comprehensive)

EXIT CODES:
    0    All smart validations passed
    1    Smart validation failures found

EXAMPLES:
    # Smart validate default app
    python3 Python/smart_validate_integration.py
    
    # Smart validate specific app
    APP_DIR=my_app python3 Python/smart_validate_integration.py
    
    # Smart validate with custom path
    APP_ROOT=/path/to/app python3 Python/smart_validate_integration.py
        """)
        sys.exit(0)
    
    # Parse command line arguments
    use_smart_validation = True
    fallback_to_basic = True
    
    for arg in sys.argv[1:]:
        if arg == '--use-smart-validation':
            use_smart_validation = True
        elif arg == '--fallback-to-basic':
            fallback_to_basic = True
        elif arg.startswith('--'):
            print(f"Unknown option: {arg}")
            sys.exit(1)
    
    # Get app directory from environment or use default
    app_dir = os.environ.get('APP_DIR', 'generated_app')
    app_root = os.environ.get('APP_ROOT', f"{os.environ.get('HOME', '/tmp')}/AppMagician/{app_dir}")
    
    print(f"🧠 Smart validating integration for app: {app_dir}")
    print(f"📁 App root: {app_root}")
    print("="*60)
    
    # Create context for smart validation
    context = {
        "app_root": app_root,
        "app_dir": app_dir
    }
    
    # Get smart validation criteria
    criteria = get_smart_validation_criteria("integration", context)
    
    # Create smart validator
    validator = SmartIntegrationValidator(app_root)
    
    # Run smart validation
    if use_smart_validation:
        print("🧠 Using smart AI-driven validation...")
        success = validator.validate_with_criteria(criteria)
        
        if not success and fallback_to_basic:
            print("\n⚠️  Smart validation failed, falling back to basic validation...")
            # Import and run basic validation
            from validate_integration import IntegrationValidator
            basic_validator = IntegrationValidator(app_root)
            success = basic_validator.validate()
    else:
        print("📋 Using basic validation...")
        # Import and run basic validation
        from validate_integration import IntegrationValidator
        basic_validator = IntegrationValidator(app_root)
        success = basic_validator.validate()
    
    # Exit with appropriate code
    if success:
        print("\n✅ Smart integration validation PASSED")
        sys.exit(0)
    else:
        print("\n❌ Smart integration validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
