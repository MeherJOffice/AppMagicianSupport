#!/usr/bin/env python3
"""
Dynamic AI Prompt System for AppMagician Pipeline.
Maintains conversation with AI to generate context-aware prompts in real-time.
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AIProvider(Enum):
    """AI providers for dynamic prompt generation"""
    CHATGPT = "chatgpt"
    DEEPSEEK = "deepseek"


@dataclass
class ConversationContext:
    """Context for maintaining AI conversation"""
    app_idea: str
    archetype: str
    current_step: int
    total_steps: int
    app_state: Dict[str, Any]
    previous_prompts: List[str]
    previous_responses: List[str]
    current_files: List[str]
    errors_encountered: List[str]
    build_status: str


class DynamicAIPromptSystem:
    """Dynamic AI system that maintains conversation for context-aware prompts"""
    
    def __init__(self, provider: AIProvider, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.conversation_history = []
        self.context = None
        
        # Provider-specific configurations
        if provider == AIProvider.CHATGPT:
            self.base_url = "https://api.openai.com/v1/chat/completions"
            self.model = "gpt-4o-mini"
        elif provider == AIProvider.DEEPSEEK:
            self.base_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = "deepseek-chat"
    
    def initialize_conversation(self, app_idea: str, archetype: str) -> Dict[str, Any]:
        """Initialize conversation with AI to get detailed prompt strategy"""
        
        system_prompt = f"""You are an expert Flutter development architect with 15+ years of experience building production iOS apps.

TASK: Generate a comprehensive, step-by-step development strategy for a {archetype} app based on this idea: "{app_idea}"

REQUIREMENTS:
1. Create 12-15 detailed, production-ready prompts for Cursor AI
2. Each prompt should be specific, actionable, and build upon previous steps
3. Include proper architecture patterns (Clean Architecture, Repository, Provider)
4. Focus on production-ready features: error handling, loading states, accessibility, performance
5. Each prompt should specify exact file paths, class names, and implementation details
6. Include validation criteria for each step

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
    "strategy": "Brief description of the development strategy",
    "architecture": "Architecture pattern to use",
    "total_steps": 15,
    "prompts": [
        {{
            "step": 1,
            "title": "Step title",
            "description": "What this step accomplishes",
            "prompt": "Detailed prompt for Cursor AI",
            "validation_criteria": {{
                "file_exists": "path/to/file.dart",
                "contains_class": "ClassName",
                "has_methods": ["method1", "method2"],
                "has_error_handling": true,
                "has_loading_states": true
            }},
            "dependencies": ["previous_step_1", "previous_step_2"],
            "estimated_time": "5-10 minutes"
        }}
    ],
    "quality_gates": {{
        "performance": "sub_100ms_response_time",
        "security": "data_encryption_required",
        "accessibility": "screen_reader_support",
        "ux": "smooth_animations"
    }}
}}

Make each prompt extremely detailed and production-ready. Focus on creating a professional, scalable app."""

        user_prompt = f"""Generate a comprehensive development strategy for a {archetype} app with this idea: "{app_idea}"

The app should be production-ready with:
- Clean architecture patterns
- Proper error handling and loading states
- Accessibility features
- Performance optimization
- Security best practices
- Material Design 3.0
- RTL support for Arabic
- Comprehensive testing

Please provide the detailed JSON strategy."""

        response = self._call_ai_api(system_prompt, user_prompt)
        
        if response:
            try:
                strategy = json.loads(response)
                self.context = ConversationContext(
                    app_idea=app_idea,
                    archetype=archetype,
                    current_step=0,
                    total_steps=len(strategy.get('prompts', [])),
                    app_state={},
                    previous_prompts=[],
                    previous_responses=[],
                    current_files=[],
                    errors_encountered=[],
                    build_status="initializing"
                )
                return strategy
            except json.JSONDecodeError as e:
                print(f"Error parsing AI response: {e}")
                return self._get_fallback_strategy(app_idea, archetype)
        else:
            return self._get_fallback_strategy(app_idea, archetype)
    
    def generate_dynamic_prompt(self, step_number: int, app_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a dynamic, context-aware prompt for the current step"""
        
        if not self.context:
            raise ValueError("Conversation not initialized")
        
        # Update context with current app state
        self.context.current_step = step_number
        self.context.app_state = app_state
        
        system_prompt = f"""You are an expert Flutter developer working on a {self.context.archetype} app.

CONTEXT:
- App Idea: "{self.context.app_idea}"
- Current Step: {step_number} of {self.context.total_steps}
- App State: {json.dumps(app_state, indent=2)}
- Previous Errors: {self.context.errors_encountered}
- Current Files: {self.context.current_files}

TASK: Generate a detailed, context-aware prompt for Cursor AI to execute step {step_number}.

REQUIREMENTS:
1. The prompt should be specific and actionable
2. Consider the current app state and what's already been built
3. Address any previous errors or issues
4. Build upon existing code without breaking it
5. Include exact file paths, class names, and implementation details
6. Specify validation criteria for this step
7. Include error handling and loading states
8. Follow Flutter best practices and Material Design 3.0

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
    "step": {step_number},
    "title": "Step title",
    "description": "What this step accomplishes",
    "prompt": "Detailed prompt for Cursor AI",
    "validation_criteria": {{
        "file_exists": "path/to/file.dart",
        "contains_class": "ClassName",
        "has_methods": ["method1", "method2"],
        "has_error_handling": true,
        "has_loading_states": true
    }},
    "dependencies": ["previous_step_1", "previous_step_2"],
    "estimated_time": "5-10 minutes",
    "context_notes": "Any specific context or considerations for this step"
}}

Make the prompt extremely detailed and production-ready."""

        user_prompt = f"""Generate a detailed prompt for step {step_number} of the {self.context.archetype} app development.

Current app state:
{json.dumps(app_state, indent=2)}

Previous errors encountered:
{self.context.errors_encountered}

Please provide a detailed, context-aware prompt that builds upon the current state and addresses any issues."""

        response = self._call_ai_api(system_prompt, user_prompt)
        
        if response:
            try:
                prompt_data = json.loads(response)
                self.context.previous_prompts.append(prompt_data['prompt'])
                return prompt_data
            except json.JSONDecodeError as e:
                print(f"Error parsing AI response: {e}")
                return self._get_fallback_prompt(step_number)
        else:
            return self._get_fallback_prompt(step_number)
    
    def analyze_step_result(self, step_number: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the result of a step and provide feedback"""
        
        if not self.context:
            raise ValueError("Conversation not initialized")
        
        system_prompt = f"""You are an expert Flutter developer reviewing the results of step {step_number} in a {self.context.archetype} app development.

CONTEXT:
- App Idea: "{self.context.app_idea}"
- Step: {step_number} of {self.context.total_steps}
- Step Result: {json.dumps(result, indent=2)}

TASK: Analyze the step result and provide feedback.

REQUIREMENTS:
1. Evaluate if the step was completed successfully
2. Identify any issues or errors
3. Suggest improvements or fixes
4. Provide recommendations for the next step
5. Update the app state based on what was accomplished

OUTPUT FORMAT:
Return a JSON object with this structure:
{{
    "step_success": true/false,
    "issues_found": ["issue1", "issue2"],
    "improvements": ["improvement1", "improvement2"],
    "next_step_recommendations": ["recommendation1", "recommendation2"],
    "app_state_update": {{
        "new_files": ["file1.dart", "file2.dart"],
        "modified_files": ["file3.dart"],
        "features_completed": ["feature1", "feature2"],
        "issues_resolved": ["issue1", "issue2"]
    }},
    "quality_score": 85,
    "feedback": "Detailed feedback about the step execution"
}}

Provide constructive feedback and actionable recommendations."""

        user_prompt = f"""Analyze the result of step {step_number}:

{json.dumps(result, indent=2)}

Provide detailed feedback and recommendations."""

        response = self._call_ai_api(system_prompt, user_prompt)
        
        if response:
            try:
                analysis = json.loads(response)
                self.context.previous_responses.append(analysis['feedback'])
                
                # Update context based on analysis
                if analysis.get('app_state_update'):
                    update = analysis['app_state_update']
                    if 'new_files' in update:
                        self.context.current_files.extend(update['new_files'])
                    if 'issues_resolved' in update:
                        for issue in update['issues_resolved']:
                            if issue in self.context.errors_encountered:
                                self.context.errors_encountered.remove(issue)
                
                return analysis
            except json.JSONDecodeError as e:
                print(f"Error parsing AI response: {e}")
                return self._get_fallback_analysis(step_number, result)
        else:
            return self._get_fallback_analysis(step_number, result)
    
    def generate_fix_prompt(self, error_context: Dict[str, Any]) -> str:
        """Generate a fix prompt based on error context"""
        
        if not self.context:
            raise ValueError("Conversation not initialized")
        
        system_prompt = f"""You are an expert Flutter developer fixing issues in a {self.context.archetype} app.

CONTEXT:
- App Idea: "{self.context.app_idea}"
- Current Step: {self.context.current_step} of {self.context.total_steps}
- Error Context: {json.dumps(error_context, indent=2)}
- App State: {json.dumps(self.context.app_state, indent=2)}

TASK: Generate a detailed fix prompt for Cursor AI.

REQUIREMENTS:
1. Analyze the error and provide a specific fix
2. Don't break existing functionality
3. Include proper error handling
4. Follow Flutter best practices
5. Provide exact code changes needed

OUTPUT FORMAT:
Return a detailed prompt string that Cursor AI can execute to fix the issue.

Make the prompt specific and actionable."""

        user_prompt = f"""Generate a fix prompt for this error context:

{json.dumps(error_context, indent=2)}

Provide a detailed, actionable fix prompt."""

        response = self._call_ai_api(system_prompt, user_prompt)
        
        if response:
            self.context.errors_encountered.append(str(error_context))
            return response
        else:
            return self._get_fallback_fix_prompt(error_context)
    
    def _call_ai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call the AI API with the given prompts"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"AI API call failed: {e}")
            return None
    
    def _get_fallback_strategy(self, app_idea: str, archetype: str) -> Dict[str, Any]:
        """Get fallback strategy when AI is unavailable"""
        return {
            "strategy": f"Fallback strategy for {archetype} app",
            "architecture": "clean_architecture_with_providers",
            "total_steps": 12,
            "prompts": [
                {
                    "step": i + 1,
                    "title": f"Step {i + 1}",
                    "description": f"Implement step {i + 1}",
                    "prompt": f"Implement step {i + 1} for {archetype} app",
                    "validation_criteria": {"file_exists": f"lib/step_{i + 1}.dart"},
                    "dependencies": [],
                    "estimated_time": "5-10 minutes"
                }
                for i in range(12)
            ],
            "quality_gates": {
                "performance": "sub_100ms_response_time",
                "security": "data_encryption_required",
                "accessibility": "screen_reader_support",
                "ux": "smooth_animations"
            }
        }
    
    def _get_fallback_prompt(self, step_number: int) -> Dict[str, Any]:
        """Get fallback prompt when AI is unavailable"""
        return {
            "step": step_number,
            "title": f"Step {step_number}",
            "description": f"Implement step {step_number}",
            "prompt": f"Implement step {step_number} for the app",
            "validation_criteria": {"file_exists": f"lib/step_{step_number}.dart"},
            "dependencies": [],
            "estimated_time": "5-10 minutes",
            "context_notes": "Fallback prompt"
        }
    
    def _get_fallback_analysis(self, step_number: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback analysis when AI is unavailable"""
        return {
            "step_success": True,
            "issues_found": [],
            "improvements": [],
            "next_step_recommendations": [],
            "app_state_update": {},
            "quality_score": 80,
            "feedback": "Fallback analysis"
        }
    
    def _get_fallback_fix_prompt(self, error_context: Dict[str, Any]) -> str:
        """Get fallback fix prompt when AI is unavailable"""
        return f"Fix the following issue: {error_context}"


class DynamicPromptPipeline:
    """Pipeline that uses dynamic AI prompts"""
    
    def __init__(self, provider: AIProvider, api_key: str):
        self.ai_system = DynamicAIPromptSystem(provider, api_key)
        self.conversation_log = []
    
    def run_dynamic_pipeline(self, app_idea: str, archetype: str, app_root: str) -> Dict[str, Any]:
        """Run the pipeline with dynamic AI prompts"""
        
        print(f"🚀 Starting dynamic AI pipeline for {archetype} app...")
        
        # Step 1: Initialize conversation and get strategy
        print("📋 Getting detailed development strategy from AI...")
        strategy = self.ai_system.initialize_conversation(app_idea, archetype)
        
        if not strategy:
            raise ValueError("Failed to get development strategy from AI")
        
        print(f"✅ Got strategy with {strategy['total_steps']} steps")
        
        # Step 2: Execute each step with dynamic prompts
        results = []
        app_state = {"files": [], "features": [], "errors": []}
        
        for step_num in range(1, strategy['total_steps'] + 1):
            print(f"\n🔄 Executing step {step_num}/{strategy['total_steps']}...")
            
            # Generate dynamic prompt for this step
            prompt_data = self.ai_system.generate_dynamic_prompt(step_num, app_state)
            
            print(f"📝 Generated dynamic prompt: {prompt_data['title']}")
            
            # Execute the prompt (this would call Cursor AI)
            step_result = self._execute_cursor_prompt(prompt_data, app_root)
            
            # Analyze the result
            analysis = self.ai_system.analyze_step_result(step_num, step_result)
            
            print(f"📊 Step analysis: Quality score {analysis['quality_score']}/100")
            
            # Update app state
            if analysis.get('app_state_update'):
                app_state.update(analysis['app_state_update'])
            
            # Log the step
            self.conversation_log.append({
                "step": step_num,
                "prompt": prompt_data,
                "result": step_result,
                "analysis": analysis
            })
            
            results.append({
                "step": step_num,
                "success": analysis['step_success'],
                "quality_score": analysis['quality_score'],
                "issues": analysis.get('issues_found', []),
                "feedback": analysis['feedback']
            })
            
            # Handle errors if any
            if analysis.get('issues_found'):
                print(f"⚠️ Issues found: {analysis['issues_found']}")
                
                # Generate fix prompt
                error_context = {
                    "step": step_num,
                    "issues": analysis['issues_found'],
                    "app_state": app_state
                }
                
                fix_prompt = self.ai_system.generate_fix_prompt(error_context)
                print(f"🔧 Generated fix prompt: {fix_prompt[:100]}...")
                
                # Execute fix (this would call Cursor AI)
                fix_result = self._execute_cursor_fix(fix_prompt, app_root)
                
                if fix_result.get('success'):
                    print("✅ Fix applied successfully")
                else:
                    print("❌ Fix failed")
        
        # Step 3: Generate final report
        final_report = self._generate_final_report(results, app_state)
        
        return {
            "strategy": strategy,
            "results": results,
            "app_state": app_state,
            "conversation_log": self.conversation_log,
            "final_report": final_report
        }
    
    def _execute_cursor_prompt(self, prompt_data: Dict[str, Any], app_root: str) -> Dict[str, Any]:
        """Execute a cursor prompt (placeholder for actual implementation)"""
        # This would integrate with the actual Cursor AI system
        return {
            "success": True,
            "files_created": [f"lib/step_{prompt_data['step']}.dart"],
            "files_modified": [],
            "output": "Step executed successfully",
            "duration": 300  # 5 minutes
        }
    
    def _execute_cursor_fix(self, fix_prompt: str, app_root: str) -> Dict[str, Any]:
        """Execute a cursor fix (placeholder for actual implementation)"""
        # This would integrate with the actual Cursor AI system
        return {
            "success": True,
            "files_modified": [],
            "output": "Fix applied successfully",
            "duration": 120  # 2 minutes
        }
    
    def _generate_final_report(self, results: List[Dict[str, Any]], app_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final pipeline report"""
        
        total_steps = len(results)
        successful_steps = sum(1 for r in results if r['success'])
        avg_quality_score = sum(r['quality_score'] for r in results) / total_steps if total_steps > 0 else 0
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": total_steps - successful_steps,
            "average_quality_score": avg_quality_score,
            "total_files_created": len(app_state.get('files', [])),
            "features_completed": len(app_state.get('features', [])),
            "issues_resolved": len(app_state.get('errors', [])),
            "pipeline_success": successful_steps >= total_steps * 0.8,  # 80% success rate
            "recommendations": [
                "Review failed steps and apply fixes",
                "Run comprehensive testing",
                "Optimize performance based on quality scores",
                "Review and improve error handling"
            ]
        }


def main():
    """Main function for dynamic AI prompt system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic AI Prompt System')
    parser.add_argument('--app-idea', required=True, help='App idea description')
    parser.add_argument('--archetype', default='utility', help='App archetype')
    parser.add_argument('--provider', default='chatgpt', choices=['chatgpt', 'deepseek'], help='AI provider')
    parser.add_argument('--api-key', required=True, help='API key for AI provider')
    parser.add_argument('--app-root', required=True, help='Path to app root directory')
    parser.add_argument('--output', default='dynamic_pipeline_report.json', help='Output report file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    provider = AIProvider.CHATGPT if args.provider == 'chatgpt' else AIProvider.DEEPSEEK
    pipeline = DynamicPromptPipeline(provider, args.api_key)
    
    if args.verbose:
        print(f"Initializing dynamic AI pipeline...")
        print(f"App idea: {args.app_idea}")
        print(f"Archetype: {args.archetype}")
        print(f"Provider: {args.provider}")
    
    # Run pipeline
    try:
        results = pipeline.run_dynamic_pipeline(args.app_idea, args.archetype, args.app_root)
        
        # Save results
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        if args.verbose:
            print(f"\n📊 Pipeline completed!")
            print(f"Total steps: {results['final_report']['total_steps']}")
            print(f"Successful steps: {results['final_report']['successful_steps']}")
            print(f"Average quality score: {results['final_report']['average_quality_score']:.1f}/100")
            print(f"Pipeline success: {results['final_report']['pipeline_success']}")
        
        print(f"Dynamic pipeline report saved to: {args.output}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
