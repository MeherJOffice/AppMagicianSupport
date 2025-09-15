#!/usr/bin/env python3
"""
Smart Prompt Generator for AppMagician Pipeline.
Replaces generic prompt generation with intelligent, archetype-specific prompts.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any
from smart_app_archetypes import SmartAppArchetypeGenerator, AppArchetype


class SmartPromptGenerator:
    """Generates intelligent, production-ready prompts based on app archetypes"""
    
    def __init__(self):
        self.archetype_generator = SmartAppArchetypeGenerator()
    
    def generate_smart_prompts(self, app_idea: str, bundle_id: str, locales: List[str], 
                             provider: str = "chatgpt") -> Dict[str, Any]:
        """Generate smart prompts based on app idea"""
        
        # Detect app archetype
        archetype = self.archetype_generator.detect_app_archetype(app_idea)
        
        # Generate archetype-specific prompts
        spec = self.archetype_generator.generate_smart_prompts(archetype, app_idea, bundle_id, locales)
        
        # Add provider-specific optimizations
        spec = self._optimize_for_provider(spec, provider)
        
        # Add production readiness enhancements
        spec = self._add_production_enhancements(spec, archetype)
        
        return spec
    
    def _optimize_for_provider(self, spec: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Optimize prompts for specific LLM provider"""
        
        if provider == "chatgpt":
            # Optimize for GPT-4
            for prompt in spec["cursor_prompts"]:
                prompt["prompt"] = self._optimize_for_gpt4(prompt["prompt"])
        elif provider == "deepseek":
            # Optimize for DeepSeek
            for prompt in spec["cursor_prompts"]:
                prompt["prompt"] = self._optimize_for_deepseek(prompt["prompt"])
        
        return spec
    
    def _optimize_for_gpt4(self, prompt: str) -> str:
        """Optimize prompt for GPT-4"""
        # GPT-4 works well with detailed, structured prompts
        return f"""You are an expert Flutter developer with 10+ years of experience building production iOS apps.

{prompt}

EXPERT REQUIREMENTS:
- Follow Flutter best practices and Material Design 3.0
- Implement proper error handling and loading states
- Use clean architecture patterns (Repository, Provider, etc.)
- Include comprehensive validation and testing
- Optimize for performance and accessibility
- Ensure production-ready code quality

When complete, verify all functionality works correctly."""
    
    def _optimize_for_deepseek(self, prompt: str) -> str:
        """Optimize prompt for DeepSeek"""
        # DeepSeek works well with concise, focused prompts
        return f"""Expert Flutter developer task:

{prompt}

Requirements:
- Production-ready code
- Clean architecture
- Proper error handling
- Material Design 3.0
- Performance optimized
- Accessibility compliant

Deliver complete, working implementation."""
    
    def _add_production_enhancements(self, spec: Dict[str, Any], archetype: AppArchetype) -> Dict[str, Any]:
        """Add production readiness enhancements"""
        
        # Add production-specific prompts
        production_prompts = self._generate_production_prompts(archetype)
        spec["cursor_prompts"].extend(production_prompts)
        
        # Add monitoring and analytics
        spec["monitoring"] = self._generate_monitoring_config(archetype)
        
        # Add deployment configuration
        spec["deployment"] = self._generate_deployment_config(archetype)
        
        return spec
    
    def _generate_production_prompts(self, archetype: AppArchetype) -> List[Dict[str, Any]]:
        """Generate production-specific prompts"""
        return [
            {
                "prompt": """Create lib/core/analytics/analytics_service.dart: Implement comprehensive analytics service with Firebase Analytics integration. Track user interactions, feature usage, performance metrics, and error events. Include privacy-compliant data collection and GDPR compliance.""",
                "validation_criteria": {
                    "file_exists": "lib/core/analytics/analytics_service.dart",
                    "contains_class": "AnalyticsService",
                    "has_firebase_integration": True,
                    "has_user_tracking": True,
                    "has_feature_tracking": True,
                    "has_performance_tracking": True,
                    "has_error_tracking": True,
                    "has_privacy_compliance": True,
                    "has_gdpr_compliance": True
                }
            },
            {
                "prompt": """Create lib/core/monitoring/performance_monitor.dart: Implement performance monitoring service that tracks app startup time, memory usage, CPU usage, and network performance. Include crash reporting and performance alerts.""",
                "validation_criteria": {
                    "file_exists": "lib/core/monitoring/performance_monitor.dart",
                    "contains_class": "PerformanceMonitor",
                    "has_startup_tracking": True,
                    "has_memory_tracking": True,
                    "has_cpu_tracking": True,
                    "has_network_tracking": True,
                    "has_crash_reporting": True,
                    "has_performance_alerts": True
                }
            },
            {
                "prompt": """Create lib/core/security/security_service.dart: Implement comprehensive security service with data encryption, secure storage, input validation, and security monitoring. Include threat detection and security alerts.""",
                "validation_criteria": {
                    "file_exists": "lib/core/security/security_service.dart",
                    "contains_class": "SecurityService",
                    "has_data_encryption": True,
                    "has_secure_storage": True,
                    "has_input_validation": True,
                    "has_security_monitoring": True,
                    "has_threat_detection": True,
                    "has_security_alerts": True
                }
            },
            {
                "prompt": """Create lib/core/error_handling/error_handler.dart: Implement comprehensive error handling service with error logging, user-friendly error messages, error recovery, and error reporting to analytics.""",
                "validation_criteria": {
                    "file_exists": "lib/core/error_handling/error_handler.dart",
                    "contains_class": "ErrorHandler",
                    "has_error_logging": True,
                    "has_user_friendly_messages": True,
                    "has_error_recovery": True,
                    "has_error_reporting": True
                }
            },
            {
                "prompt": """Create lib/core/network/network_service.dart: Implement robust network service with retry logic, offline support, request caching, and network monitoring. Include proper error handling and timeout management.""",
                "validation_criteria": {
                    "file_exists": "lib/core/network/network_service.dart",
                    "contains_class": "NetworkService",
                    "has_retry_logic": True,
                    "has_offline_support": True,
                    "has_request_caching": True,
                    "has_network_monitoring": True,
                    "has_error_handling": True,
                    "has_timeout_management": True
                }
            },
            {
                "prompt": """Create lib/core/cache/cache_service.dart: Implement intelligent caching service with memory and disk caching, cache invalidation, and cache optimization. Include cache size management and performance monitoring.""",
                "validation_criteria": {
                    "file_exists": "lib/core/cache/cache_service.dart",
                    "contains_class": "CacheService",
                    "has_memory_caching": True,
                    "has_disk_caching": True,
                    "has_cache_invalidation": True,
                    "has_cache_optimization": True,
                    "has_size_management": True,
                    "has_performance_monitoring": True
                }
            },
            {
                "prompt": """Create lib/core/logging/logger.dart: Implement comprehensive logging service with different log levels, structured logging, log rotation, and log analysis. Include privacy-compliant logging and performance optimization.""",
                "validation_criteria": {
                    "file_exists": "lib/core/logging/logger.dart",
                    "contains_class": "Logger",
                    "has_log_levels": True,
                    "has_structured_logging": True,
                    "has_log_rotation": True,
                    "has_log_analysis": True,
                    "has_privacy_compliance": True,
                    "has_performance_optimization": True
                }
            },
            {
                "prompt": """Create lib/core/config/app_config.dart: Implement application configuration service with environment-specific settings, feature flags, and configuration management. Include secure configuration storage and runtime configuration updates.""",
                "validation_criteria": {
                    "file_exists": "lib/core/config/app_config.dart",
                    "contains_class": "AppConfig",
                    "has_environment_settings": True,
                    "has_feature_flags": True,
                    "has_configuration_management": True,
                    "has_secure_storage": True,
                    "has_runtime_updates": True
                }
            },
            {
                "prompt": """Create lib/core/updates/update_service.dart: Implement application update service with version checking, update notifications, and automatic updates. Include update rollback and update verification.""",
                "validation_criteria": {
                    "file_exists": "lib/core/updates/update_service.dart",
                    "contains_class": "UpdateService",
                    "has_version_checking": True,
                    "has_update_notifications": True,
                    "has_automatic_updates": True,
                    "has_update_rollback": True,
                    "has_update_verification": True
                }
            },
            {
                "prompt": """Create lib/core/backup/backup_service.dart: Implement data backup service with automatic backups, backup verification, and backup restoration. Include backup encryption and backup scheduling.""",
                "validation_criteria": {
                    "file_exists": "lib/core/backup/backup_service.dart",
                    "contains_class": "BackupService",
                    "has_automatic_backups": True,
                    "has_backup_verification": True,
                    "has_backup_restoration": True,
                    "has_backup_encryption": True,
                    "has_backup_scheduling": True
                }
            }
        ]
    
    def _generate_monitoring_config(self, archetype: AppArchetype) -> Dict[str, Any]:
        """Generate monitoring configuration"""
        return {
            "analytics": {
                "enabled": True,
                "provider": "firebase",
                "track_user_events": True,
                "track_performance": True,
                "track_errors": True,
                "privacy_compliant": True
            },
            "crash_reporting": {
                "enabled": True,
                "provider": "firebase_crashlytics",
                "collect_logs": True,
                "collect_user_info": False,
                "automatic_reporting": True
            },
            "performance_monitoring": {
                "enabled": True,
                "track_startup_time": True,
                "track_memory_usage": True,
                "track_cpu_usage": True,
                "track_network_performance": True,
                "alert_thresholds": {
                    "startup_time": 3.0,
                    "memory_usage": 100,
                    "cpu_usage": 80
                }
            }
        }
    
    def _generate_deployment_config(self, archetype: AppArchetype) -> Dict[str, Any]:
        """Generate deployment configuration"""
        return {
            "ios": {
                "bundle_identifier": "com.example.app",
                "version": "1.0.0",
                "build_number": 1,
                "deployment_target": "12.0",
                "capabilities": [
                    "push_notifications",
                    "background_processing",
                    "network_access"
                ],
                "permissions": [
                    "camera",
                    "microphone",
                    "location",
                    "notifications"
                ]
            },
            "app_store": {
                "category": "productivity",
                "content_rating": "4+",
                "keywords": ["flutter", "productivity", "mobile"],
                "description": "A powerful productivity app built with Flutter",
                "screenshots_required": True,
                "app_review_required": True
            },
            "testing": {
                "unit_tests": True,
                "integration_tests": True,
                "widget_tests": True,
                "performance_tests": True,
                "accessibility_tests": True
            }
        }
    
    def save_spec(self, spec: Dict[str, Any], output_file: str) -> None:
        """Save specification to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
    
    def print_summary(self, spec: Dict[str, Any]) -> None:
        """Print specification summary"""
        print("=" * 80)
        print("SMART PROMPT GENERATION SUMMARY")
        print("=" * 80)
        print(f"App Name: {spec['app_name']}")
        print(f"Archetype: {spec['archetype_name']}")
        print(f"Description: {spec['description']}")
        print(f"Total Prompts: {len(spec['cursor_prompts'])}")
        print(f"Quality Gates: {len(spec['quality_gates'])}")
        print(f"Performance Requirements: {len(spec['performance_requirements'])}")
        print("")
        print("FEATURES:")
        for feature in spec['spec']['features']:
            print(f"  ✅ {feature}")
        print("")
        print("UI PATTERNS:")
        for pattern in spec['spec']['ui_patterns']:
            print(f"  🎨 {pattern}")
        print("")
        print("ARCHITECTURE:")
        print(f"  🏗️ {spec['spec']['architecture']}")
        print("")
        print("QUALITY REQUIREMENTS:")
        for req, value in spec['spec']['quality_requirements'].items():
            print(f"  🔍 {req}: {value}")
        print("")


def main():
    """Main function for smart prompt generation"""
    parser = argparse.ArgumentParser(description='Smart Prompt Generator')
    parser.add_argument('--app-idea', required=True, help='App idea description')
    parser.add_argument('--bundle-id', default='com.example.app', help='Bundle identifier')
    parser.add_argument('--locales', default='en,ar', help='Comma-separated locales')
    parser.add_argument('--provider', default='chatgpt', choices=['chatgpt', 'deepseek'], help='LLM provider')
    parser.add_argument('--output', default='smart_app_spec.json', help='Output file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = SmartPromptGenerator()
    
    if args.verbose:
        print("Generating smart prompts...")
        print(f"App idea: {args.app_idea}")
        print(f"Provider: {args.provider}")
    
    # Generate smart prompts
    locales = [x.strip() for x in args.locales.split(',') if x.strip()]
    spec = generator.generate_smart_prompts(args.app_idea, args.bundle_id, locales, args.provider)
    
    # Save specification
    generator.save_spec(spec, args.output)
    
    # Print summary
    if args.verbose:
        generator.print_summary(spec)
    
    print(f"Smart app specification generated: {args.output}")


if __name__ == "__main__":
    main()
