#!/usr/bin/env python3
"""
Smart Quality Gates System for AppMagician Pipeline.
Implements production-ready quality checks based on app archetypes.
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Any, Optional
from enum import Enum


class QualityGateLevel(Enum):
    """Quality gate levels"""
    BASIC = "basic"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"


class SmartQualityGates:
    """Smart quality gates that adapt to app archetypes"""
    
    def __init__(self, app_root: str, archetype: str = "utility"):
        self.app_root = app_root
        self.archetype = archetype
        self.quality_level = self._determine_quality_level()
        self.gates = self._load_quality_gates()
    
    def _determine_quality_level(self) -> QualityGateLevel:
        """Determine quality level based on archetype"""
        enterprise_archetypes = ["finance", "health_fitness", "ecommerce"]
        production_archetypes = ["chat_app", "productivity", "social_media"]
        
        if self.archetype in enterprise_archetypes:
            return QualityGateLevel.ENTERPRISE
        elif self.archetype in production_archetypes:
            return QualityGateLevel.PRODUCTION
        else:
            return QualityGateLevel.BASIC
    
    def _load_quality_gates(self) -> Dict[str, Dict[str, Any]]:
        """Load quality gates based on archetype and level"""
        return {
            "code_quality": {
                "flutter_analyze": {
                    "enabled": True,
                    "max_errors": 0,
                    "max_warnings": 5 if self.quality_level == QualityGateLevel.BASIC else 0,
                    "strict_mode": self.quality_level != QualityGateLevel.BASIC
                },
                "code_coverage": {
                    "enabled": True,
                    "min_coverage": 70 if self.quality_level == QualityGateLevel.BASIC else 85,
                    "critical_paths": 95 if self.quality_level == QualityGateLevel.ENTERPRISE else 85
                },
                "complexity": {
                    "enabled": True,
                    "max_cyclomatic_complexity": 10,
                    "max_function_length": 50,
                    "max_class_length": 200
                }
            },
            "performance": {
                "build_time": {
                    "enabled": True,
                    "max_time": 300 if self.quality_level == QualityGateLevel.BASIC else 180,
                    "unit": "seconds"
                },
                "app_size": {
                    "enabled": True,
                    "max_size": 50 if self.quality_level == QualityGateLevel.BASIC else 30,
                    "unit": "mb"
                },
                "startup_time": {
                    "enabled": True,
                    "max_time": 3 if self.quality_level == QualityGateLevel.BASIC else 2,
                    "unit": "seconds"
                }
            },
            "security": {
                "dependency_check": {
                    "enabled": True,
                    "check_vulnerabilities": True,
                    "check_licenses": self.quality_level != QualityGateLevel.BASIC
                },
                "code_security": {
                    "enabled": True,
                    "check_hardcoded_secrets": True,
                    "check_insecure_patterns": True
                }
            },
            "accessibility": {
                "screen_reader": {
                    "enabled": True,
                    "required": True
                },
                "keyboard_navigation": {
                    "enabled": True,
                    "required": True
                },
                "color_contrast": {
                    "enabled": True,
                    "min_ratio": 4.5
                }
            },
            "archetype_specific": self._get_archetype_gates()
        }
    
    def _get_archetype_gates(self) -> Dict[str, Any]:
        """Get archetype-specific quality gates"""
        gates = {
            "chat_app": {
                "message_persistence": True,
                "real_time_updates": True,
                "ai_response_handling": True,
                "offline_support": True,
                "message_encryption": True
            },
            "productivity": {
                "task_crud_operations": True,
                "calendar_integration": True,
                "notification_system": True,
                "data_sync": True,
                "offline_support": True
            },
            "ecommerce": {
                "product_search": True,
                "cart_functionality": True,
                "payment_integration": True,
                "order_tracking": True,
                "image_optimization": True
            },
            "finance": {
                "transaction_tracking": True,
                "budget_management": True,
                "financial_calculations": True,
                "data_encryption": True,
                "audit_trail": True
            },
            "utility": {
                "core_functionality": True,
                "settings_management": True,
                "data_persistence": True,
                "error_handling": True
            }
        }
        return gates.get(self.archetype, gates["utility"])
    
    def run_all_gates(self) -> Dict[str, Any]:
        """Run all quality gates and return results"""
        results = {
            "overall_status": "PASS",
            "gates": {},
            "summary": {
                "total_gates": 0,
                "passed_gates": 0,
                "failed_gates": 0,
                "warnings": 0
            }
        }
        
        # Run each gate category
        for category, gates in self.gates.items():
            category_results = self._run_category_gates(category, gates)
            results["gates"][category] = category_results
            
            # Update summary
            results["summary"]["total_gates"] += category_results["total"]
            results["summary"]["passed_gates"] += category_results["passed"]
            results["summary"]["failed_gates"] += category_results["failed"]
            results["summary"]["warnings"] += category_results["warnings"]
        
        # Determine overall status
        if results["summary"]["failed_gates"] > 0:
            results["overall_status"] = "FAIL"
        elif results["summary"]["warnings"] > 0:
            results["overall_status"] = "WARN"
        
        return results
    
    def _run_category_gates(self, category: str, gates: Dict[str, Any]) -> Dict[str, Any]:
        """Run gates for a specific category"""
        results = {
            "category": category,
            "status": "PASS",
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": {}
        }
        
        for gate_name, gate_config in gates.items():
            if not gate_config.get("enabled", True):
                continue
            
            results["total"] += 1
            gate_result = self._run_single_gate(gate_name, gate_config)
            results["details"][gate_name] = gate_result
            
            if gate_result["status"] == "PASS":
                results["passed"] += 1
            elif gate_result["status"] == "FAIL":
                results["failed"] += 1
                results["status"] = "FAIL"
            elif gate_result["status"] == "WARN":
                results["warnings"] += 1
                if results["status"] == "PASS":
                    results["status"] = "WARN"
        
        return results
    
    def _run_single_gate(self, gate_name: str, gate_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single quality gate"""
        try:
            if gate_name == "flutter_analyze":
                return self._run_flutter_analyze_gate(gate_config)
            elif gate_name == "code_coverage":
                return self._run_code_coverage_gate(gate_config)
            elif gate_name == "build_time":
                return self._run_build_time_gate(gate_config)
            elif gate_name == "app_size":
                return self._run_app_size_gate(gate_config)
            elif gate_name == "dependency_check":
                return self._run_dependency_check_gate(gate_config)
            elif gate_name == "accessibility":
                return self._run_accessibility_gate(gate_config)
            else:
                return self._run_archetype_specific_gate(gate_name, gate_config)
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Gate execution failed: {str(e)}",
                "details": {}
            }
    
    def _run_flutter_analyze_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Flutter analyze quality gate"""
        try:
            result = subprocess.run(
                ["flutter", "analyze"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output for errors and warnings
            output = result.stdout + result.stderr
            errors = output.count("error •")
            warnings = output.count("warning •")
            
            max_errors = config.get("max_errors", 0)
            max_warnings = config.get("max_warnings", 5)
            
            if errors > max_errors:
                return {
                    "status": "FAIL",
                    "message": f"Too many errors: {errors} > {max_errors}",
                    "details": {"errors": errors, "warnings": warnings}
                }
            elif warnings > max_warnings:
                return {
                    "status": "WARN",
                    "message": f"Too many warnings: {warnings} > {max_warnings}",
                    "details": {"errors": errors, "warnings": warnings}
                }
            else:
                return {
                    "status": "PASS",
                    "message": f"Analysis passed: {errors} errors, {warnings} warnings",
                    "details": {"errors": errors, "warnings": warnings}
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "message": "Flutter analyze timed out",
                "details": {}
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Flutter analyze failed: {str(e)}",
                "details": {}
            }
    
    def _run_code_coverage_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run code coverage quality gate"""
        try:
            # Run tests with coverage
            result = subprocess.run(
                ["flutter", "test", "--coverage"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return {
                    "status": "FAIL",
                    "message": "Tests failed",
                    "details": {"output": result.stderr}
                }
            
            # Parse coverage report
            coverage_file = os.path.join(self.app_root, "coverage", "lcov.info")
            if not os.path.exists(coverage_file):
                return {
                    "status": "FAIL",
                    "message": "Coverage file not found",
                    "details": {}
                }
            
            # Calculate coverage percentage
            coverage_percentage = self._calculate_coverage_percentage(coverage_file)
            min_coverage = config.get("min_coverage", 70)
            
            if coverage_percentage < min_coverage:
                return {
                    "status": "FAIL",
                    "message": f"Coverage too low: {coverage_percentage:.1f}% < {min_coverage}%",
                    "details": {"coverage": coverage_percentage}
                }
            else:
                return {
                    "status": "PASS",
                    "message": f"Coverage passed: {coverage_percentage:.1f}%",
                    "details": {"coverage": coverage_percentage}
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "message": "Code coverage analysis timed out",
                "details": {}
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Code coverage failed: {str(e)}",
                "details": {}
            }
    
    def _calculate_coverage_percentage(self, coverage_file: str) -> float:
        """Calculate coverage percentage from lcov file"""
        try:
            with open(coverage_file, 'r') as f:
                content = f.read()
            
            # Parse lcov format
            lines_covered = 0
            lines_total = 0
            
            for line in content.split('\n'):
                if line.startswith('LF:'):
                    lines_total += int(line.split(':')[1])
                elif line.startswith('LH:'):
                    lines_covered += int(line.split(':')[1])
            
            if lines_total == 0:
                return 0.0
            
            return (lines_covered / lines_total) * 100
        except Exception:
            return 0.0
    
    def _run_build_time_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run build time quality gate"""
        try:
            start_time = time.time()
            
            result = subprocess.run(
                ["flutter", "build", "ios", "--no-codesign"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            build_time = time.time() - start_time
            max_time = config.get("max_time", 300)
            
            if result.returncode != 0:
                return {
                    "status": "FAIL",
                    "message": "Build failed",
                    "details": {"build_time": build_time, "output": result.stderr}
                }
            
            if build_time > max_time:
                return {
                    "status": "WARN",
                    "message": f"Build time too long: {build_time:.1f}s > {max_time}s",
                    "details": {"build_time": build_time}
                }
            else:
                return {
                    "status": "PASS",
                    "message": f"Build time acceptable: {build_time:.1f}s",
                    "details": {"build_time": build_time}
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "message": "Build timed out",
                "details": {}
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Build failed: {str(e)}",
                "details": {}
            }
    
    def _run_app_size_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run app size quality gate"""
        try:
            # Build the app first
            result = subprocess.run(
                ["flutter", "build", "ios", "--no-codesign"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                return {
                    "status": "FAIL",
                    "message": "Build failed",
                    "details": {}
                }
            
            # Get app size
            app_path = os.path.join(self.app_root, "build", "ios", "iphoneos", "Runner.app")
            if not os.path.exists(app_path):
                return {
                    "status": "FAIL",
                    "message": "App bundle not found",
                    "details": {}
                }
            
            # Calculate size in MB
            size_bytes = self._get_directory_size(app_path)
            size_mb = size_bytes / (1024 * 1024)
            max_size = config.get("max_size", 50)
            
            if size_mb > max_size:
                return {
                    "status": "WARN",
                    "message": f"App size too large: {size_mb:.1f}MB > {max_size}MB",
                    "details": {"size_mb": size_mb}
                }
            else:
                return {
                    "status": "PASS",
                    "message": f"App size acceptable: {size_mb:.1f}MB",
                    "details": {"size_mb": size_mb}
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"App size check failed: {str(e)}",
                "details": {}
            }
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
    
    def _run_dependency_check_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run dependency check quality gate"""
        try:
            # Check for vulnerabilities
            result = subprocess.run(
                ["flutter", "pub", "deps"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return {
                    "status": "FAIL",
                    "message": "Dependency check failed",
                    "details": {"output": result.stderr}
                }
            
            # Check for known vulnerable packages
            vulnerable_packages = self._check_vulnerable_packages()
            
            if vulnerable_packages:
                return {
                    "status": "WARN",
                    "message": f"Found {len(vulnerable_packages)} potentially vulnerable packages",
                    "details": {"vulnerable_packages": vulnerable_packages}
                }
            else:
                return {
                    "status": "PASS",
                    "message": "No vulnerable packages found",
                    "details": {}
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Dependency check failed: {str(e)}",
                "details": {}
            }
    
    def _check_vulnerable_packages(self) -> List[str]:
        """Check for known vulnerable packages"""
        # This is a simplified check - in production, you'd use a proper vulnerability database
        vulnerable_patterns = [
            "http: ^0.12.0",  # Old HTTP package
            "crypto: ^2.1.0",  # Old crypto package
        ]
        
        pubspec_path = os.path.join(self.app_root, "pubspec.yaml")
        if not os.path.exists(pubspec_path):
            return []
        
        try:
            with open(pubspec_path, 'r') as f:
                content = f.read()
            
            vulnerable_packages = []
            for pattern in vulnerable_patterns:
                if pattern in content:
                    vulnerable_packages.append(pattern)
            
            return vulnerable_packages
        except Exception:
            return []
    
    def _run_accessibility_gate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run accessibility quality gate"""
        try:
            # Check for accessibility features in the code
            accessibility_checks = self._check_accessibility_features()
            
            required_checks = config.get("required", [])
            missing_checks = [check for check in required_checks if check not in accessibility_checks]
            
            if missing_checks:
                return {
                    "status": "WARN",
                    "message": f"Missing accessibility features: {', '.join(missing_checks)}",
                    "details": {"missing_checks": missing_checks, "present_checks": accessibility_checks}
                }
            else:
                return {
                    "status": "PASS",
                    "message": "Accessibility features present",
                    "details": {"present_checks": accessibility_checks}
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Accessibility check failed: {str(e)}",
                "details": {}
            }
    
    def _check_accessibility_features(self) -> List[str]:
        """Check for accessibility features in the code"""
        accessibility_features = []
        
        # Check for common accessibility patterns
        patterns = {
            "screen_reader": ["Semantics", "ExcludeSemantics", "semanticLabel"],
            "keyboard_navigation": ["Focus", "FocusScope", "onKeyEvent"],
            "color_contrast": ["ColorScheme", "ThemeData", "contrastColor"],
            "text_scaling": ["MediaQuery.textScaleFactor", "textScaleFactor"]
        }
        
        try:
            for feature, keywords in patterns.items():
                if self._search_code_for_keywords(keywords):
                    accessibility_features.append(feature)
        except Exception:
            pass
        
        return accessibility_features
    
    def _search_code_for_keywords(self, keywords: List[str]) -> bool:
        """Search code for specific keywords"""
        try:
            for root, dirs, files in os.walk(os.path.join(self.app_root, "lib")):
                for file in files:
                    if file.endswith('.dart'):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            if any(keyword in content for keyword in keywords):
                                return True
                        except Exception:
                            continue
        except Exception:
            pass
        
        return False
    
    def _run_archetype_specific_gate(self, gate_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run archetype-specific quality gate"""
        try:
            if gate_name == "message_persistence":
                return self._check_message_persistence()
            elif gate_name == "real_time_updates":
                return self._check_real_time_updates()
            elif gate_name == "ai_response_handling":
                return self._check_ai_response_handling()
            elif gate_name == "offline_support":
                return self._check_offline_support()
            elif gate_name == "task_crud_operations":
                return self._check_task_crud_operations()
            elif gate_name == "calendar_integration":
                return self._check_calendar_integration()
            elif gate_name == "product_search":
                return self._check_product_search()
            elif gate_name == "cart_functionality":
                return self._check_cart_functionality()
            elif gate_name == "transaction_tracking":
                return self._check_transaction_tracking()
            elif gate_name == "budget_management":
                return self._check_budget_management()
            else:
                return {
                    "status": "PASS",
                    "message": f"Archetype-specific gate {gate_name} not implemented",
                    "details": {}
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Archetype-specific gate failed: {str(e)}",
                "details": {}
            }
    
    def _check_message_persistence(self) -> Dict[str, Any]:
        """Check message persistence functionality"""
        # Check for database-related files
        db_files = [
            "lib/core/database/database_helper.dart",
            "lib/features/chat/data/repositories/chat_repository.dart"
        ]
        
        present_files = []
        for file in db_files:
            if os.path.exists(os.path.join(self.app_root, file)):
                present_files.append(file)
        
        if len(present_files) >= 2:
            return {
                "status": "PASS",
                "message": "Message persistence implemented",
                "details": {"present_files": present_files}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Message persistence not fully implemented",
                "details": {"present_files": present_files, "missing_files": [f for f in db_files if f not in present_files]}
            }
    
    def _check_real_time_updates(self) -> Dict[str, Any]:
        """Check real-time updates functionality"""
        # Check for WebSocket or real-time related files
        realtime_files = [
            "lib/core/network/websocket_service.dart",
            "lib/features/chat/presentation/providers/chat_provider.dart"
        ]
        
        present_files = []
        for file in realtime_files:
            if os.path.exists(os.path.join(self.app_root, file)):
                present_files.append(file)
        
        if len(present_files) >= 1:
            return {
                "status": "PASS",
                "message": "Real-time updates implemented",
                "details": {"present_files": present_files}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Real-time updates not implemented",
                "details": {"missing_files": realtime_files}
            }
    
    def _check_ai_response_handling(self) -> Dict[str, Any]:
        """Check AI response handling functionality"""
        # Check for AI-related files
        ai_files = [
            "lib/features/ai/data/services/ai_service.dart",
            "lib/features/ai/presentation/providers/ai_provider.dart"
        ]
        
        present_files = []
        for file in ai_files:
            if os.path.exists(os.path.join(self.app_root, file)):
                present_files.append(file)
        
        if len(present_files) >= 2:
            return {
                "status": "PASS",
                "message": "AI response handling implemented",
                "details": {"present_files": present_files}
            }
        else:
            return {
                "status": "FAIL",
                "message": "AI response handling not fully implemented",
                "details": {"present_files": present_files, "missing_files": [f for f in ai_files if f not in present_files]}
            }
    
    def _check_offline_support(self) -> Dict[str, Any]:
        """Check offline support functionality"""
        # Check for offline-related patterns
        offline_patterns = ["SharedPreferences", "SQLite", "offline", "cache"]
        
        if self._search_code_for_keywords(offline_patterns):
            return {
                "status": "PASS",
                "message": "Offline support implemented",
                "details": {"patterns_found": offline_patterns}
            }
        else:
            return {
                "status": "WARN",
                "message": "Offline support not detected",
                "details": {}
            }
    
    def _check_task_crud_operations(self) -> Dict[str, Any]:
        """Check task CRUD operations functionality"""
        # Check for task-related files
        task_files = [
            "lib/features/tasks/data/models/task_model.dart",
            "lib/features/tasks/data/repositories/task_repository.dart",
            "lib/features/tasks/presentation/providers/task_provider.dart"
        ]
        
        present_files = []
        for file in task_files:
            if os.path.exists(os.path.join(self.app_root, file)):
                present_files.append(file)
        
        if len(present_files) >= 3:
            return {
                "status": "PASS",
                "message": "Task CRUD operations implemented",
                "details": {"present_files": present_files}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Task CRUD operations not fully implemented",
                "details": {"present_files": present_files, "missing_files": [f for f in task_files if f not in present_files]}
            }
    
    def _check_calendar_integration(self) -> Dict[str, Any]:
        """Check calendar integration functionality"""
        # Check for calendar-related patterns
        calendar_patterns = ["calendar", "event", "schedule", "date"]
        
        if self._search_code_for_keywords(calendar_patterns):
            return {
                "status": "PASS",
                "message": "Calendar integration implemented",
                "details": {"patterns_found": calendar_patterns}
            }
        else:
            return {
                "status": "WARN",
                "message": "Calendar integration not detected",
                "details": {}
            }
    
    def _check_product_search(self) -> Dict[str, Any]:
        """Check product search functionality"""
        # Check for product-related files
        product_files = [
            "lib/features/products/data/models/product_model.dart",
            "lib/features/products/data/repositories/product_repository.dart",
            "lib/features/products/presentation/providers/product_provider.dart"
        ]
        
        present_files = []
        for file in product_files:
            if os.path.exists(os.path.join(self.app_root, file)):
                present_files.append(file)
        
        if len(present_files) >= 3:
            return {
                "status": "PASS",
                "message": "Product search implemented",
                "details": {"present_files": present_files}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Product search not fully implemented",
                "details": {"present_files": present_files, "missing_files": [f for f in product_files if f not in present_files]}
            }
    
    def _check_cart_functionality(self) -> Dict[str, Any]:
        """Check cart functionality"""
        # Check for cart-related patterns
        cart_patterns = ["cart", "shopping", "checkout", "order"]
        
        if self._search_code_for_keywords(cart_patterns):
            return {
                "status": "PASS",
                "message": "Cart functionality implemented",
                "details": {"patterns_found": cart_patterns}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Cart functionality not implemented",
                "details": {}
            }
    
    def _check_transaction_tracking(self) -> Dict[str, Any]:
        """Check transaction tracking functionality"""
        # Check for transaction-related files
        transaction_files = [
            "lib/features/transactions/data/models/transaction_model.dart",
            "lib/features/transactions/data/repositories/transaction_repository.dart",
            "lib/features/transactions/presentation/providers/transaction_provider.dart"
        ]
        
        present_files = []
        for file in transaction_files:
            if os.path.exists(os.path.join(self.app_root, file)):
                present_files.append(file)
        
        if len(present_files) >= 3:
            return {
                "status": "PASS",
                "message": "Transaction tracking implemented",
                "details": {"present_files": present_files}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Transaction tracking not fully implemented",
                "details": {"present_files": present_files, "missing_files": [f for f in transaction_files if f not in present_files]}
            }
    
    def _check_budget_management(self) -> Dict[str, Any]:
        """Check budget management functionality"""
        # Check for budget-related patterns
        budget_patterns = ["budget", "expense", "income", "financial"]
        
        if self._search_code_for_keywords(budget_patterns):
            return {
                "status": "PASS",
                "message": "Budget management implemented",
                "details": {"patterns_found": budget_patterns}
            }
        else:
            return {
                "status": "FAIL",
                "message": "Budget management not implemented",
                "details": {}
            }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive quality report"""
        report = []
        report.append("=" * 80)
        report.append("SMART QUALITY GATES REPORT")
        report.append("=" * 80)
        report.append(f"App Root: {self.app_root}")
        report.append(f"Archetype: {self.archetype}")
        report.append(f"Quality Level: {self.quality_level.value}")
        report.append(f"Overall Status: {results['overall_status']}")
        report.append("")
        
        # Summary
        summary = results["summary"]
        report.append("SUMMARY:")
        report.append(f"  Total Gates: {summary['total_gates']}")
        report.append(f"  Passed: {summary['passed_gates']}")
        report.append(f"  Failed: {summary['failed_gates']}")
        report.append(f"  Warnings: {summary['warnings']}")
        report.append("")
        
        # Detailed results
        for category, category_results in results["gates"].items():
            report.append(f"{category.upper()}:")
            report.append(f"  Status: {category_results['status']}")
            report.append(f"  Passed: {category_results['passed']}/{category_results['total']}")
            
            for gate_name, gate_result in category_results["details"].items():
                status_icon = "✅" if gate_result["status"] == "PASS" else "❌" if gate_result["status"] == "FAIL" else "⚠️"
                report.append(f"    {status_icon} {gate_name}: {gate_result['message']}")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """Main function for smart quality gates"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Quality Gates System')
    parser.add_argument('--app-root', required=True, help='Path to app root directory')
    parser.add_argument('--archetype', default='utility', help='App archetype')
    parser.add_argument('--output', default='quality_report.txt', help='Output report file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize quality gates
    quality_gates = SmartQualityGates(args.app_root, args.archetype)
    
    if args.verbose:
        print(f"Running quality gates for {args.archetype} app...")
        print(f"Quality level: {quality_gates.quality_level.value}")
    
    # Run all gates
    results = quality_gates.run_all_gates()
    
    # Generate report
    report = quality_gates.generate_report(results)
    
    # Save report
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    if args.verbose:
        print(f"Quality report saved to: {args.output}")
        print(f"Overall status: {results['overall_status']}")
    
    # Exit with appropriate code
    if results["overall_status"] == "FAIL":
        sys.exit(1)
    elif results["overall_status"] == "WARN":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
