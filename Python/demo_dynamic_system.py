#!/usr/bin/env python3
"""
Demo of the Dynamic AI Prompt System.
Shows how the conversational AI system works without requiring API keys.
"""

import json
import os
from typing import Dict, List, Any


class MockAISystem:
    """Mock AI system for demonstration purposes"""
    
    def __init__(self):
        self.conversation_history = []
    
    def generate_strategy(self, app_idea: str, archetype: str) -> Dict[str, Any]:
        """Generate a mock development strategy"""
        
        return {
            "strategy": f"Build a production-ready {archetype} app with clean architecture",
            "architecture": "clean_architecture_with_providers",
            "total_steps": 8,
            "prompts": [
                {
                    "step": 1,
                    "title": "Setup Project Structure",
                    "description": "Create clean architecture folder structure",
                    "prompt": "Create lib/features/ directory structure with data/, domain/, and presentation/ folders. Add proper barrel exports.",
                    "validation_criteria": {
                        "file_exists": "lib/features/",
                        "has_folders": ["data", "domain", "presentation"],
                        "has_barrel_exports": True
                    },
                    "dependencies": [],
                    "estimated_time": "5 minutes"
                },
                {
                    "step": 2,
                    "title": "Setup Dependencies",
                    "description": "Configure pubspec.yaml with required packages",
                    "prompt": "Update pubspec.yaml with provider, shared_preferences, and other essential packages for the app.",
                    "validation_criteria": {
                        "file_exists": "pubspec.yaml",
                        "has_dependencies": ["provider", "shared_preferences"],
                        "version_compatible": True
                    },
                    "dependencies": ["step_1"],
                    "estimated_time": "3 minutes"
                },
                {
                    "step": 3,
                    "title": "Create Data Models",
                    "description": "Implement data models and DTOs",
                    "prompt": "Create data models in lib/features/*/data/models/ with proper serialization and validation.",
                    "validation_criteria": {
                        "file_exists": "lib/features/*/data/models/",
                        "has_models": True,
                        "has_serialization": True
                    },
                    "dependencies": ["step_1", "step_2"],
                    "estimated_time": "10 minutes"
                },
                {
                    "step": 4,
                    "title": "Implement Repositories",
                    "description": "Create repository pattern for data access",
                    "prompt": "Implement repositories in lib/features/*/data/repositories/ with proper error handling and data persistence.",
                    "validation_criteria": {
                        "file_exists": "lib/features/*/data/repositories/",
                        "has_repositories": True,
                        "has_error_handling": True
                    },
                    "dependencies": ["step_3"],
                    "estimated_time": "15 minutes"
                },
                {
                    "step": 5,
                    "title": "Create Providers",
                    "description": "Implement state management with providers",
                    "prompt": "Create providers in lib/features/*/presentation/providers/ using Riverpod for state management.",
                    "validation_criteria": {
                        "file_exists": "lib/features/*/presentation/providers/",
                        "has_providers": True,
                        "uses_riverpod": True
                    },
                    "dependencies": ["step_4"],
                    "estimated_time": "12 minutes"
                },
                {
                    "step": 6,
                    "title": "Build UI Screens",
                    "description": "Create presentation layer screens",
                    "prompt": "Build screens in lib/features/*/presentation/screens/ with Material Design 3.0 and proper accessibility.",
                    "validation_criteria": {
                        "file_exists": "lib/features/*/presentation/screens/",
                        "has_screens": True,
                        "material_3_design": True,
                        "has_accessibility": True
                    },
                    "dependencies": ["step_5"],
                    "estimated_time": "20 minutes"
                },
                {
                    "step": 7,
                    "title": "Add Error Handling",
                    "description": "Implement comprehensive error handling",
                    "prompt": "Add error handling throughout the app with proper error boundaries and user-friendly messages.",
                    "validation_criteria": {
                        "has_error_boundaries": True,
                        "has_user_friendly_errors": True,
                        "has_error_recovery": True
                    },
                    "dependencies": ["step_6"],
                    "estimated_time": "8 minutes"
                },
                {
                    "step": 8,
                    "title": "Add Testing",
                    "description": "Implement comprehensive testing",
                    "prompt": "Add unit tests, widget tests, and integration tests for all components.",
                    "validation_criteria": {
                        "has_unit_tests": True,
                        "has_widget_tests": True,
                        "has_integration_tests": True,
                        "test_coverage": ">80%"
                    },
                    "dependencies": ["step_7"],
                    "estimated_time": "15 minutes"
                }
            ],
            "quality_gates": {
                "performance": "sub_100ms_response_time",
                "security": "data_encryption_required",
                "accessibility": "screen_reader_support",
                "ux": "smooth_animations"
            }
        }
    
    def generate_dynamic_prompt(self, step_number: int, app_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a dynamic prompt based on current app state"""
        
        # Simulate dynamic prompt generation based on app state
        base_prompts = {
            1: "Create lib/features/ directory structure with data/, domain/, and presentation/ folders. Add proper barrel exports.",
            2: "Update pubspec.yaml with provider, shared_preferences, and other essential packages for the app.",
            3: "Create data models in lib/features/*/data/models/ with proper serialization and validation.",
            4: "Implement repositories in lib/features/*/data/repositories/ with proper error handling and data persistence.",
            5: "Create providers in lib/features/*/presentation/providers/ using Riverpod for state management.",
            6: "Build screens in lib/features/*/presentation/screens/ with Material Design 3.0 and proper accessibility.",
            7: "Add error handling throughout the app with proper error boundaries and user-friendly messages.",
            8: "Add unit tests, widget tests, and integration tests for all components."
        }
        
        # Add context-aware modifications
        context_modifications = []
        
        if app_state.get("errors"):
            context_modifications.append("Address previous errors and ensure robust error handling.")
        
        if app_state.get("files"):
            context_modifications.append(f"Build upon existing {len(app_state['files'])} files.")
        
        if app_state.get("features"):
            context_modifications.append(f"Integrate with existing features: {', '.join(app_state['features'])}.")
        
        # Combine base prompt with context modifications
        dynamic_prompt = base_prompts.get(step_number, f"Execute step {step_number}")
        
        if context_modifications:
            dynamic_prompt += "\n\nCONTEXT AWARENESS:\n" + "\n".join(f"- {mod}" for mod in context_modifications)
        
        return {
            "step": step_number,
            "title": f"Dynamic Step {step_number}",
            "description": f"Context-aware execution of step {step_number}",
            "prompt": dynamic_prompt,
            "validation_criteria": {
                "file_exists": f"lib/step_{step_number}.dart",
                "has_context_awareness": True,
                "builds_on_previous": True
            },
            "dependencies": [f"step_{i}" for i in range(1, step_number)],
            "estimated_time": "5-15 minutes",
            "context_notes": f"Generated dynamically based on app state: {len(app_state)} items"
        }
    
    def analyze_step_result(self, step_number: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze step result and provide feedback"""
        
        # Simulate analysis based on result
        success = result.get("success", True)
        quality_score = 85 if success else 60
        
        if success:
            issues_found = []
            improvements = ["Consider adding more error handling", "Optimize performance"]
            feedback = f"Step {step_number} completed successfully with good quality."
        else:
            issues_found = ["Build error detected", "Missing dependencies"]
            improvements = ["Fix build errors", "Add missing dependencies"]
            feedback = f"Step {step_number} encountered issues that need attention."
        
        return {
            "step_success": success,
            "issues_found": issues_found,
            "improvements": improvements,
            "next_step_recommendations": ["Continue with next step", "Review error handling"],
            "app_state_update": {
                "new_files": [f"lib/step_{step_number}.dart"],
                "modified_files": [],
                "features_completed": [f"step_{step_number}"],
                "issues_resolved": issues_found if success else []
            },
            "quality_score": quality_score,
            "feedback": feedback
        }


def demo_dynamic_system():
    """Demonstrate the dynamic AI prompt system"""
    
    print("🚀 Dynamic AI Prompt System Demo")
    print("=" * 50)
    
    # Initialize mock AI system
    ai_system = MockAISystem()
    
    # Generate initial strategy
    print("\n📋 Step 1: Getting development strategy from AI...")
    strategy = ai_system.generate_strategy("A chat app with AI integration", "chat_app")
    
    print(f"✅ Strategy generated with {strategy['total_steps']} steps")
    print(f"🏗️ Architecture: {strategy['architecture']}")
    print(f"🎯 Quality gates: {len(strategy['quality_gates'])}")
    
    # Simulate dynamic execution
    print("\n🔄 Step 2: Executing steps with dynamic prompts...")
    
    app_state = {"files": [], "features": [], "errors": []}
    results = []
    
    for step_num in range(1, strategy['total_steps'] + 1):
        print(f"\n--- Step {step_num}/{strategy['total_steps']} ---")
        
        # Generate dynamic prompt
        prompt_data = ai_system.generate_dynamic_prompt(step_num, app_state)
        print(f"📝 Dynamic prompt: {prompt_data['title']}")
        print(f"🎯 Context notes: {prompt_data['context_notes']}")
        
        # Simulate execution result
        execution_result = {
            "success": step_num % 3 != 0,  # Simulate some failures
            "output": f"Step {step_num} executed",
            "error": "" if step_num % 3 != 0 else f"Error in step {step_num}",
            "files_created": [f"lib/step_{step_num}.dart"],
            "files_modified": [],
            "duration": 5.0 + step_num
        }
        
        print(f"⏱️ Execution time: {execution_result['duration']:.1f}s")
        print(f"✅ Success: {execution_result['success']}")
        
        # Analyze result
        analysis = ai_system.analyze_step_result(step_num, execution_result)
        print(f"📊 Quality score: {analysis['quality_score']}/100")
        print(f"💬 Feedback: {analysis['feedback']}")
        
        # Update app state
        if analysis.get('app_state_update'):
            update = analysis['app_state_update']
            app_state['files'].extend(update.get('new_files', []))
            app_state['features'].extend(update.get('features_completed', []))
            if not execution_result['success']:
                app_state['errors'].append(f"Step {step_num} error")
        
        results.append({
            "step": step_num,
            "success": execution_result['success'],
            "quality_score": analysis['quality_score'],
            "feedback": analysis['feedback']
        })
    
    # Generate final report
    print("\n📊 Final Report")
    print("=" * 30)
    
    total_steps = len(results)
    successful_steps = sum(1 for r in results if r['success'])
    avg_quality = sum(r['quality_score'] for r in results) / total_steps
    
    print(f"Total steps: {total_steps}")
    print(f"Successful steps: {successful_steps}")
    print(f"Failed steps: {total_steps - successful_steps}")
    print(f"Success rate: {successful_steps/total_steps*100:.1f}%")
    print(f"Average quality score: {avg_quality:.1f}/100")
    print(f"Files created: {len(app_state['files'])}")
    print(f"Features completed: {len(app_state['features'])}")
    print(f"Issues encountered: {len(app_state['errors'])}")
    
    # Show conversation context
    print(f"\n💬 Conversation Context")
    print("=" * 25)
    print(f"App state items: {len(app_state)}")
    print(f"Dynamic adaptations: {total_steps}")
    print(f"Context-aware prompts: {total_steps}")
    
    return {
        "strategy": strategy,
        "results": results,
        "app_state": app_state,
        "conversation_summary": {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps/total_steps*100,
            "average_quality": avg_quality
        }
    }


def main():
    """Main function for demo"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic AI Prompt System Demo')
    parser.add_argument('--app-idea', default='A chat app with AI integration', help='App idea description')
    parser.add_argument('--archetype', default='chat_app', help='App archetype')
    parser.add_argument('--output', default='demo_results.json', help='Output file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Running demo with:")
        print(f"  App idea: {args.app_idea}")
        print(f"  Archetype: {args.archetype}")
    
    # Run demo
    results = demo_dynamic_system()
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Demo results saved to: {args.output}")
    print("\n🎉 Dynamic AI Prompt System Demo Complete!")
    print("\nKey Benefits:")
    print("✅ Context-aware prompt generation")
    print("✅ Real-time adaptation to app state")
    print("✅ Conversational AI feedback")
    print("✅ Dynamic error analysis and fixes")
    print("✅ Production-ready app generation")


if __name__ == "__main__":
    main()
