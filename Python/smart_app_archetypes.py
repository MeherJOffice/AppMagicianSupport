#!/usr/bin/env python3
"""
Smart App Archetype System for AppMagician Pipeline.
Generates production-ready apps based on specific archetypes with tailored prompts and validation.
"""

import json
import os
import sys
from typing import Dict, List, Any
from enum import Enum


class AppArchetype(Enum):
    """App archetypes with specific requirements and patterns"""
    CHAT_APP = "chat_app"
    PRODUCTIVITY = "productivity"
    ECOMMERCE = "ecommerce"
    SOCIAL_MEDIA = "social_media"
    FINANCE = "finance"
    HEALTH_FITNESS = "health_fitness"
    EDUCATION = "education"
    NEWS_MEDIA = "news_media"
    GAMING = "gaming"
    UTILITY = "utility"


class SmartAppArchetypeGenerator:
    """Generates smart, production-ready app specifications based on archetypes"""
    
    def __init__(self):
        self.archetypes = self._load_archetype_definitions()
    
    def _load_archetype_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load archetype-specific definitions and requirements"""
        return {
            AppArchetype.CHAT_APP.value: {
                "name": "AI Chat Application",
                "description": "Production-ready chat app with AI integration",
                "required_features": ["real_time_messaging", "ai_integration", "user_management", "message_history"],
                "ui_patterns": ["chat_interface", "message_bubbles", "typing_indicators", "message_status"],
                "architecture": "clean_architecture_with_providers",
                "quality_requirements": {
                    "performance": "sub_100ms_message_send",
                    "ux": "smooth_animations",
                    "accessibility": "screen_reader_support",
                    "security": "message_encryption"
                },
                "validation_criteria": {
                    "message_persistence": True,
                    "real_time_updates": True,
                    "ai_response_handling": True,
                    "error_recovery": True,
                    "offline_support": True
                }
            },
            AppArchetype.PRODUCTIVITY.value: {
                "name": "Productivity Suite",
                "description": "Task management and productivity app",
                "required_features": ["task_management", "calendar_integration", "notifications", "data_sync"],
                "ui_patterns": ["task_lists", "calendar_view", "priority_indicators", "progress_tracking"],
                "architecture": "mvvm_with_repository_pattern",
                "quality_requirements": {
                    "performance": "instant_task_updates",
                    "ux": "intuitive_gestures",
                    "accessibility": "keyboard_navigation",
                    "security": "data_privacy"
                },
                "validation_criteria": {
                    "task_crud_operations": True,
                    "calendar_integration": True,
                    "notification_system": True,
                    "data_persistence": True,
                    "sync_functionality": True
                }
            },
            AppArchetype.ECOMMERCE.value: {
                "name": "E-commerce Platform",
                "description": "Full-featured e-commerce app with payment integration",
                "required_features": ["product_catalog", "shopping_cart", "payment_processing", "order_management"],
                "ui_patterns": ["product_grid", "shopping_cart", "checkout_flow", "order_tracking"],
                "architecture": "clean_architecture_with_bloc",
                "quality_requirements": {
                    "performance": "fast_image_loading",
                    "ux": "smooth_checkout",
                    "accessibility": "product_descriptions",
                    "security": "secure_payments"
                },
                "validation_criteria": {
                    "product_search": True,
                    "cart_functionality": True,
                    "payment_integration": True,
                    "order_tracking": True,
                    "user_reviews": True
                }
            },
            AppArchetype.FINANCE.value: {
                "name": "Financial Management",
                "description": "Secure financial tracking and management app",
                "required_features": ["transaction_tracking", "budget_management", "financial_reports", "security"],
                "ui_patterns": ["dashboard", "transaction_lists", "charts_graphs", "budget_overview"],
                "architecture": "clean_architecture_with_secure_storage",
                "quality_requirements": {
                    "performance": "real_time_calculations",
                    "ux": "clear_financial_data",
                    "accessibility": "financial_summaries",
                    "security": "bank_level_security"
                },
                "validation_criteria": {
                    "transaction_crud": True,
                    "budget_tracking": True,
                    "financial_calculations": True,
                    "data_encryption": True,
                    "audit_trail": True
                }
            }
        }
    
    def detect_app_archetype(self, app_idea: str) -> AppArchetype:
        """Intelligently detect app archetype from user input"""
        app_idea_lower = app_idea.lower()
        
        # Keyword-based detection with confidence scoring
        archetype_scores = {}
        
        for archetype in AppArchetype:
            keywords = self._get_archetype_keywords(archetype)
            score = sum(1 for keyword in keywords if keyword in app_idea_lower)
            archetype_scores[archetype] = score
        
        # Return archetype with highest score, default to UTILITY if no clear match
        best_archetype = max(archetype_scores, key=archetype_scores.get)
        return best_archetype if archetype_scores[best_archetype] > 0 else AppArchetype.UTILITY
    
    def _get_archetype_keywords(self, archetype: AppArchetype) -> List[str]:
        """Get keywords for archetype detection"""
        keyword_map = {
            AppArchetype.CHAT_APP: ["chat", "messaging", "ai", "conversation", "llm", "gpt", "assistant"],
            AppArchetype.PRODUCTIVITY: ["task", "todo", "productivity", "calendar", "schedule", "organize"],
            AppArchetype.ECOMMERCE: ["shop", "buy", "sell", "ecommerce", "store", "product", "cart", "payment"],
            AppArchetype.SOCIAL_MEDIA: ["social", "share", "post", "feed", "community", "friends"],
            AppArchetype.FINANCE: ["finance", "money", "budget", "expense", "banking", "financial", "transaction"],
            AppArchetype.HEALTH_FITNESS: ["health", "fitness", "workout", "exercise", "medical", "wellness"],
            AppArchetype.EDUCATION: ["learn", "education", "course", "study", "tutorial", "academic"],
            AppArchetype.NEWS_MEDIA: ["news", "media", "article", "blog", "content", "publish"],
            AppArchetype.GAMING: ["game", "gaming", "play", "score", "level", "achievement"],
            AppArchetype.UTILITY: ["utility", "tool", "helper", "assistant", "manager"]
        }
        return keyword_map.get(archetype, [])
    
    def generate_smart_prompts(self, archetype: AppArchetype, app_idea: str, 
                             bundle_id: str, locales: List[str]) -> Dict[str, Any]:
        """Generate smart, archetype-specific prompts"""
        
        archetype_config = self.archetypes[archetype.value]
        
        # Generate app-specific prompts
        prompts = self._generate_archetype_prompts(archetype, app_idea, bundle_id, locales)
        
        # Add quality gates and validation
        quality_gates = self._generate_quality_gates(archetype)
        
        # Add performance requirements
        performance_requirements = self._generate_performance_requirements(archetype)
        
        return {
            "app_name": f"{archetype.value}_app",
            "archetype": archetype.value,
            "archetype_name": archetype_config["name"],
            "description": archetype_config["description"],
            "spec": {
                "theme": "light",
                "locale": locales[0] if locales else "en",
                "platforms": ["ios"],
                "features": archetype_config["required_features"],
                "ui_patterns": archetype_config["ui_patterns"],
                "architecture": archetype_config["architecture"],
                "quality_requirements": archetype_config["quality_requirements"]
            },
            "cursor_prompts": prompts,
            "quality_gates": quality_gates,
            "performance_requirements": performance_requirements,
            "validation_criteria": archetype_config["validation_criteria"]
        }
    
    def _generate_archetype_prompts(self, archetype: AppArchetype, app_idea: str, 
                                  bundle_id: str, locales: List[str]) -> List[Dict[str, Any]]:
        """Generate archetype-specific prompts"""
        
        if archetype == AppArchetype.CHAT_APP:
            return self._generate_chat_app_prompts(app_idea, bundle_id, locales)
        elif archetype == AppArchetype.PRODUCTIVITY:
            return self._generate_productivity_prompts(app_idea, bundle_id, locales)
        elif archetype == AppArchetype.ECOMMERCE:
            return self._generate_ecommerce_prompts(app_idea, bundle_id, locales)
        elif archetype == AppArchetype.FINANCE:
            return self._generate_finance_prompts(app_idea, bundle_id, locales)
        else:
            return self._generate_utility_prompts(app_idea, bundle_id, locales)
    
    def _generate_chat_app_prompts(self, app_idea: str, bundle_id: str, locales: List[str]) -> List[Dict[str, Any]]:
        """Generate production-ready chat app prompts"""
        return [
            {
                "prompt": f"""Create a production-ready AI chat application based on: "{app_idea}"

ARCHITECTURE REQUIREMENTS:
- Clean Architecture with Provider pattern
- Repository pattern for data management
- Proper error handling and loading states
- Offline message persistence with SQLite
- Real-time message updates with WebSocket simulation

CORE FEATURES TO IMPLEMENT:
1. Message input with send button and typing indicators
2. Message bubbles with timestamps and status indicators
3. AI response handling with streaming simulation
4. Message history with pagination
5. User authentication simulation
6. Settings for AI model selection and preferences

TECHNICAL REQUIREMENTS:
- Use Riverpod for state management
- Implement proper error boundaries
- Add loading skeletons for better UX
- Include accessibility features (screen reader support)
- Implement proper keyboard handling
- Add haptic feedback for interactions

UI/UX REQUIREMENTS:
- Material Design 3.0 with custom color scheme
- Smooth animations for message sending/receiving
- Proper RTL support for Arabic
- Responsive design for different screen sizes
- Dark/Light theme support

SECURITY REQUIREMENTS:
- Input sanitization for messages
- Rate limiting for API calls
- Secure storage for user preferences
- Proper error handling without exposing sensitive data

Create the complete app structure with all necessary files, providers, repositories, and UI components.""",
                "validation_criteria": {
                    "file_exists": "lib/features/chat/presentation/screens/chat_screen.dart",
                    "contains_class": "ChatScreen",
                    "has_message_input": True,
                    "has_message_bubbles": True,
                    "has_ai_integration": True,
                    "has_offline_support": True,
                    "has_real_time_updates": True,
                    "has_error_handling": True,
                    "has_loading_states": True,
                    "has_accessibility": True,
                    "has_haptic_feedback": True,
                    "material_3_design": True,
                    "rtl_support": True,
                    "responsive_design": True,
                    "dark_light_theme": True
                }
            },
            {
                "prompt": """Create lib/features/chat/data/models/message_model.dart: Implement Message model with id, content, senderId, timestamp, status (sent, delivered, read), messageType (text, image, file), and AI response flag. Include proper serialization and validation.""",
                "validation_criteria": {
                    "file_exists": "lib/features/chat/data/models/message_model.dart",
                    "contains_class": "Message",
                    "has_fields": ["id", "content", "senderId", "timestamp", "status", "messageType"],
                    "has_serialization": True,
                    "has_validation": True
                }
            },
            {
                "prompt": """Create lib/features/chat/data/repositories/chat_repository.dart: Implement ChatRepository with methods: sendMessage(Message), getMessages(int limit, int offset), markAsRead(String messageId), deleteMessage(String messageId). Include proper error handling and offline support.""",
                "validation_criteria": {
                    "file_exists": "lib/features/chat/data/repositories/chat_repository.dart",
                    "contains_class": "ChatRepository",
                    "has_methods": ["sendMessage", "getMessages", "markAsRead", "deleteMessage"],
                    "has_error_handling": True,
                    "has_offline_support": True
                }
            },
            {
                "prompt": """Create lib/features/chat/presentation/providers/chat_provider.dart: Implement ChatProvider with Riverpod for state management. Include: messages list, loading states, error states, sendMessage method, loadMessages method, and real-time updates simulation.""",
                "validation_criteria": {
                    "file_exists": "lib/features/chat/presentation/providers/chat_provider.dart",
                    "contains_class": "ChatProvider",
                    "extends_changenotifier": True,
                    "has_methods": ["sendMessage", "loadMessages"],
                    "has_state_management": True,
                    "has_real_time_updates": True
                }
            },
            {
                "prompt": """Create lib/features/chat/presentation/widgets/message_bubble.dart: Build animated message bubble widget with proper styling, timestamps, status indicators, and RTL support. Include different styles for sent/received messages.""",
                "validation_criteria": {
                    "file_exists": "lib/features/chat/presentation/widgets/message_bubble.dart",
                    "contains_class": "MessageBubble",
                    "has_animations": True,
                    "has_timestamps": True,
                    "has_status_indicators": True,
                    "has_rtl_support": True,
                    "has_different_styles": True
                }
            },
            {
                "prompt": """Create lib/features/chat/presentation/widgets/message_input.dart: Build message input widget with text field, send button, typing indicator, and proper keyboard handling. Include emoji picker and file attachment options.""",
                "validation_criteria": {
                    "file_exists": "lib/features/chat/presentation/widgets/message_input.dart",
                    "contains_class": "MessageInput",
                    "has_text_field": True,
                    "has_send_button": True,
                    "has_typing_indicator": True,
                    "has_keyboard_handling": True,
                    "has_emoji_picker": True,
                    "has_file_attachment": True
                }
            },
            {
                "prompt": """Create lib/features/ai/data/services/ai_service.dart: Implement AIService with methods: generateResponse(String message), streamResponse(String message), and getAvailableModels(). Include proper error handling and rate limiting.""",
                "validation_criteria": {
                    "file_exists": "lib/features/ai/data/services/ai_service.dart",
                    "contains_class": "AIService",
                    "has_methods": ["generateResponse", "streamResponse", "getAvailableModels"],
                    "has_error_handling": True,
                    "has_rate_limiting": True
                }
            },
            {
                "prompt": """Create lib/features/ai/presentation/providers/ai_provider.dart: Implement AIProvider with Riverpod for AI state management. Include: current model selection, response generation, streaming responses, and error handling.""",
                "validation_criteria": {
                    "file_exists": "lib/features/ai/presentation/providers/ai_provider.dart",
                    "contains_class": "AIProvider",
                    "extends_changenotifier": True,
                    "has_model_selection": True,
                    "has_response_generation": True,
                    "has_streaming_responses": True,
                    "has_error_handling": True
                }
            },
            {
                "prompt": """Create lib/features/settings/presentation/screens/ai_settings_screen.dart: Build AI settings screen with model selection, response length settings, temperature controls, and API key management. Include proper validation and security.""",
                "validation_criteria": {
                    "file_exists": "lib/features/settings/presentation/screens/ai_settings_screen.dart",
                    "contains_class": "AISettingsScreen",
                    "has_model_selection": True,
                    "has_response_length": True,
                    "has_temperature_controls": True,
                    "has_api_key_management": True,
                    "has_validation": True,
                    "has_security": True
                }
            },
            {
                "prompt": """Create lib/features/auth/presentation/screens/login_screen.dart: Build login screen with email/password fields, social login options, and proper validation. Include loading states and error handling.""",
                "validation_criteria": {
                    "file_exists": "lib/features/auth/presentation/screens/login_screen.dart",
                    "contains_class": "LoginScreen",
                    "has_email_field": True,
                    "has_password_field": True,
                    "has_social_login": True,
                    "has_validation": True,
                    "has_loading_states": True,
                    "has_error_handling": True
                }
            },
            {
                "prompt": """Create lib/features/auth/presentation/providers/auth_provider.dart: Implement AuthProvider with Riverpod for authentication state management. Include: login, logout, register, and user state management.""",
                "validation_criteria": {
                    "file_exists": "lib/features/auth/presentation/providers/auth_provider.dart",
                    "contains_class": "AuthProvider",
                    "extends_changenotifier": True,
                    "has_methods": ["login", "logout", "register"],
                    "has_user_state_management": True
                }
            },
            {
                "prompt": """Create lib/core/database/database_helper.dart: Implement SQLite database helper for message persistence. Include: message storage, retrieval, pagination, and offline support.""",
                "validation_criteria": {
                    "file_exists": "lib/core/database/database_helper.dart",
                    "contains_class": "DatabaseHelper",
                    "has_message_storage": True,
                    "has_retrieval": True,
                    "has_pagination": True,
                    "has_offline_support": True
                }
            },
            {
                "prompt": """Create lib/core/network/websocket_service.dart: Implement WebSocket service for real-time message updates. Include: connection management, message broadcasting, and reconnection logic.""",
                "validation_criteria": {
                    "file_exists": "lib/core/network/websocket_service.dart",
                    "contains_class": "WebSocketService",
                    "has_connection_management": True,
                    "has_message_broadcasting": True,
                    "has_reconnection_logic": True
                }
            },
            {
                "prompt": """Create lib/core/utils/haptic_feedback.dart: Implement haptic feedback utility for message sending, receiving, and error states. Include proper platform detection.""",
                "validation_criteria": {
                    "file_exists": "lib/core/utils/haptic_feedback.dart",
                    "contains_class": "HapticFeedback",
                    "has_message_sending_feedback": True,
                    "has_receiving_feedback": True,
                    "has_error_feedback": True,
                    "has_platform_detection": True
                }
            },
            {
                "prompt": """Create lib/core/utils/accessibility.dart: Implement accessibility utilities for screen reader support, keyboard navigation, and semantic labels. Include proper ARIA labels and focus management.""",
                "validation_criteria": {
                    "file_exists": "lib/core/utils/accessibility.dart",
                    "contains_class": "AccessibilityUtils",
                    "has_screen_reader_support": True,
                    "has_keyboard_navigation": True,
                    "has_semantic_labels": True,
                    "has_aria_labels": True,
                    "has_focus_management": True
                }
            }
        ]
    
    def _generate_productivity_prompts(self, app_idea: str, bundle_id: str, locales: List[str]) -> List[Dict[str, Any]]:
        """Generate production-ready productivity app prompts"""
        return [
            {
                "prompt": f"""Create a production-ready productivity application based on: "{app_idea}"

ARCHITECTURE REQUIREMENTS:
- Clean Architecture with MVVM pattern
- Repository pattern for data management
- Proper state management with Riverpod
- Offline data persistence with SQLite
- Real-time synchronization simulation

CORE FEATURES TO IMPLEMENT:
1. Task management with CRUD operations
2. Calendar integration with event management
3. Priority and category system
4. Progress tracking and analytics
5. Notification system
6. Data export/import functionality

TECHNICAL REQUIREMENTS:
- Use Riverpod for state management
- Implement proper error boundaries
- Add loading skeletons for better UX
- Include accessibility features
- Implement proper keyboard handling
- Add haptic feedback for interactions

UI/UX REQUIREMENTS:
- Material Design 3.0 with custom color scheme
- Smooth animations for task operations
- Proper RTL support for Arabic
- Responsive design for different screen sizes
- Dark/Light theme support

SECURITY REQUIREMENTS:
- Input validation for all forms
- Secure storage for sensitive data
- Proper error handling
- Data encryption for sensitive information

Create the complete app structure with all necessary files, providers, repositories, and UI components.""",
                "validation_criteria": {
                    "file_exists": "lib/features/tasks/presentation/screens/task_list_screen.dart",
                    "contains_class": "TaskListScreen",
                    "has_task_crud": True,
                    "has_priority_system": True,
                    "has_category_system": True,
                    "has_progress_tracking": True,
                    "has_notification_system": True,
                    "has_data_export": True,
                    "has_error_handling": True,
                    "has_loading_states": True,
                    "has_accessibility": True,
                    "has_haptic_feedback": True,
                    "material_3_design": True,
                    "rtl_support": True,
                    "responsive_design": True,
                    "dark_light_theme": True
                }
            }
            # Add more productivity-specific prompts...
        ]
    
    def _generate_ecommerce_prompts(self, app_idea: str, bundle_id: str, locales: List[str]) -> List[Dict[str, Any]]:
        """Generate production-ready e-commerce app prompts"""
        return [
            {
                "prompt": f"""Create a production-ready e-commerce application based on: "{app_idea}"

ARCHITECTURE REQUIREMENTS:
- Clean Architecture with BLoC pattern
- Repository pattern for data management
- Proper state management with BLoC
- Offline data persistence with SQLite
- Payment integration simulation

CORE FEATURES TO IMPLEMENT:
1. Product catalog with search and filtering
2. Shopping cart with persistent storage
3. Checkout flow with payment processing
4. Order management and tracking
5. User reviews and ratings
6. Wishlist and favorites

TECHNICAL REQUIREMENTS:
- Use BLoC for state management
- Implement proper error boundaries
- Add loading skeletons for better UX
- Include accessibility features
- Implement proper keyboard handling
- Add haptic feedback for interactions

UI/UX REQUIREMENTS:
- Material Design 3.0 with custom color scheme
- Smooth animations for product interactions
- Proper RTL support for Arabic
- Responsive design for different screen sizes
- Dark/Light theme support

SECURITY REQUIREMENTS:
- Input validation for all forms
- Secure payment processing simulation
- Proper error handling
- Data encryption for sensitive information

Create the complete app structure with all necessary files, providers, repositories, and UI components.""",
                "validation_criteria": {
                    "file_exists": "lib/features/products/presentation/screens/product_list_screen.dart",
                    "contains_class": "ProductListScreen",
                    "has_product_catalog": True,
                    "has_search_filtering": True,
                    "has_shopping_cart": True,
                    "has_checkout_flow": True,
                    "has_payment_processing": True,
                    "has_order_management": True,
                    "has_user_reviews": True,
                    "has_wishlist": True,
                    "has_error_handling": True,
                    "has_loading_states": True,
                    "has_accessibility": True,
                    "has_haptic_feedback": True,
                    "material_3_design": True,
                    "rtl_support": True,
                    "responsive_design": True,
                    "dark_light_theme": True
                }
            }
            # Add more e-commerce-specific prompts...
        ]
    
    def _generate_finance_prompts(self, app_idea: str, bundle_id: str, locales: List[str]) -> List[Dict[str, Any]]:
        """Generate production-ready finance app prompts"""
        return [
            {
                "prompt": f"""Create a production-ready financial management application based on: "{app_idea}"

ARCHITECTURE REQUIREMENTS:
- Clean Architecture with secure storage
- Repository pattern for data management
- Proper state management with Riverpod
- Encrypted data persistence with SQLite
- Financial calculations and reporting

CORE FEATURES TO IMPLEMENT:
1. Transaction tracking and categorization
2. Budget management and monitoring
3. Financial reports and analytics
4. Investment tracking simulation
5. Bill reminders and notifications
6. Data export for tax purposes

TECHNICAL REQUIREMENTS:
- Use Riverpod for state management
- Implement proper error boundaries
- Add loading skeletons for better UX
- Include accessibility features
- Implement proper keyboard handling
- Add haptic feedback for interactions

UI/UX REQUIREMENTS:
- Material Design 3.0 with custom color scheme
- Clear financial data visualization
- Proper RTL support for Arabic
- Responsive design for different screen sizes
- Dark/Light theme support

SECURITY REQUIREMENTS:
- Bank-level data encryption
- Input validation for all forms
- Secure storage for sensitive data
- Proper error handling
- Audit trail for all transactions

Create the complete app structure with all necessary files, providers, repositories, and UI components.""",
                "validation_criteria": {
                    "file_exists": "lib/features/transactions/presentation/screens/transaction_list_screen.dart",
                    "contains_class": "TransactionListScreen",
                    "has_transaction_tracking": True,
                    "has_categorization": True,
                    "has_budget_management": True,
                    "has_financial_reports": True,
                    "has_analytics": True,
                    "has_investment_tracking": True,
                    "has_bill_reminders": True,
                    "has_data_export": True,
                    "has_error_handling": True,
                    "has_loading_states": True,
                    "has_accessibility": True,
                    "has_haptic_feedback": True,
                    "material_3_design": True,
                    "rtl_support": True,
                    "responsive_design": True,
                    "dark_light_theme": True,
                    "has_data_encryption": True,
                    "has_audit_trail": True
                }
            }
            # Add more finance-specific prompts...
        ]
    
    def _generate_utility_prompts(self, app_idea: str, bundle_id: str, locales: List[str]) -> List[Dict[str, Any]]:
        """Generate production-ready utility app prompts"""
        return [
            {
                "prompt": f"""Create a production-ready utility application based on: "{app_idea}"

ARCHITECTURE REQUIREMENTS:
- Clean Architecture with Provider pattern
- Repository pattern for data management
- Proper state management with Riverpod
- Data persistence with SQLite
- Utility-specific functionality

CORE FEATURES TO IMPLEMENT:
1. Core utility functionality
2. Settings and preferences
3. Data management and storage
4. User interface optimization
5. Performance monitoring
6. Error handling and recovery

TECHNICAL REQUIREMENTS:
- Use Riverpod for state management
- Implement proper error boundaries
- Add loading skeletons for better UX
- Include accessibility features
- Implement proper keyboard handling
- Add haptic feedback for interactions

UI/UX REQUIREMENTS:
- Material Design 3.0 with custom color scheme
- Smooth animations for interactions
- Proper RTL support for Arabic
- Responsive design for different screen sizes
- Dark/Light theme support

SECURITY REQUIREMENTS:
- Input validation for all forms
- Secure storage for sensitive data
- Proper error handling
- Data encryption for sensitive information

Create the complete app structure with all necessary files, providers, repositories, and UI components.""",
                "validation_criteria": {
                    "file_exists": "lib/features/core/presentation/screens/main_screen.dart",
                    "contains_class": "MainScreen",
                    "has_core_functionality": True,
                    "has_settings": True,
                    "has_data_management": True,
                    "has_ui_optimization": True,
                    "has_performance_monitoring": True,
                    "has_error_handling": True,
                    "has_loading_states": True,
                    "has_accessibility": True,
                    "has_haptic_feedback": True,
                    "material_3_design": True,
                    "rtl_support": True,
                    "responsive_design": True,
                    "dark_light_theme": True
                }
            }
            # Add more utility-specific prompts...
        ]
    
    def _generate_quality_gates(self, archetype: AppArchetype) -> Dict[str, Any]:
        """Generate quality gates specific to archetype"""
        return {
            "performance": {
                "max_load_time": "2_seconds",
                "max_memory_usage": "100_mb",
                "max_cpu_usage": "50_percent",
                "smooth_animations": True,
                "responsive_ui": True
            },
            "security": {
                "input_validation": True,
                "data_encryption": True,
                "secure_storage": True,
                "error_handling": True,
                "audit_trail": archetype == AppArchetype.FINANCE
            },
            "accessibility": {
                "screen_reader_support": True,
                "keyboard_navigation": True,
                "semantic_labels": True,
                "color_contrast": True,
                "text_scaling": True
            },
            "ux": {
                "intuitive_navigation": True,
                "consistent_design": True,
                "loading_states": True,
                "error_recovery": True,
                "offline_support": True
            }
        }
    
    def _generate_performance_requirements(self, archetype: AppArchetype) -> Dict[str, Any]:
        """Generate performance requirements specific to archetype"""
        requirements = {
            AppArchetype.CHAT_APP: {
                "message_send_time": "< 100ms",
                "message_load_time": "< 500ms",
                "ai_response_time": "< 2s",
                "memory_usage": "< 80MB",
                "battery_optimization": True
            },
            AppArchetype.PRODUCTIVITY: {
                "task_update_time": "< 50ms",
                "calendar_load_time": "< 1s",
                "sync_time": "< 5s",
                "memory_usage": "< 60MB",
                "background_sync": True
            },
            AppArchetype.ECOMMERCE: {
                "product_load_time": "< 1s",
                "image_load_time": "< 2s",
                "checkout_time": "< 3s",
                "memory_usage": "< 100MB",
                "image_optimization": True
            },
            AppArchetype.FINANCE: {
                "calculation_time": "< 100ms",
                "report_generation": "< 3s",
                "data_sync_time": "< 5s",
                "memory_usage": "< 70MB",
                "data_encryption": True
            }
        }
        return requirements.get(archetype, {
            "general_performance": "< 2s",
            "memory_usage": "< 80MB",
            "responsive_ui": True
        })


def main():
    """Main function for smart app archetype generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart App Archetype Generator')
    parser.add_argument('--app-idea', required=True, help='App idea description')
    parser.add_argument('--bundle-id', default='com.example.app', help='Bundle identifier')
    parser.add_argument('--locales', default='en,ar', help='Comma-separated locales')
    parser.add_argument('--output', default='smart_app_spec.json', help='Output file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    generator = SmartAppArchetypeGenerator()
    
    # Detect archetype
    archetype = generator.detect_app_archetype(args.app_idea)
    
    if args.verbose:
        print(f"Detected archetype: {archetype.value}")
        print(f"App idea: {args.app_idea}")
    
    # Generate smart prompts
    locales = [x.strip() for x in args.locales.split(',') if x.strip()]
    spec = generator.generate_smart_prompts(archetype, args.app_idea, args.bundle_id, locales)
    
    # Output to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    if args.verbose:
        print(f"Generated smart app specification: {args.output}")
        print(f"Archetype: {spec['archetype_name']}")
        print(f"Prompts: {len(spec['cursor_prompts'])}")
        print(f"Quality gates: {len(spec['quality_gates'])}")


if __name__ == "__main__":
    main()
