#!/usr/bin/env python3
"""
Cursor AI Integration Module for Dynamic Prompt System.
Handles communication with Cursor AI and maintains conversation context.
"""

import os
import sys
import json
import subprocess
import time
import selectors
import signal
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CursorExecutionResult:
    """Result of Cursor AI execution"""
    success: bool
    output: str
    error: str
    duration: float
    files_created: List[str]
    files_modified: List[str]
    sentinel_found: bool


class CursorAIIntegration:
    """Integration with Cursor AI for dynamic prompt execution"""
    
    def __init__(self, app_root: str, timeout: int = 300):
        self.app_root = app_root
        self.timeout = timeout
        self.sentinel = "~~CURSOR_DONE~~"
        self.conversation_context = []
    
    def execute_prompt(self, prompt: str, context: Dict[str, Any] = None) -> CursorExecutionResult:
        """Execute a prompt with Cursor AI"""
        
        start_time = time.time()
        
        # Prepare the prompt with context
        full_prompt = self._prepare_prompt_with_context(prompt, context)
        
        # Create prompt file
        prompt_file = os.path.join(self.app_root, ".dynamic_prompt.txt")
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(full_prompt)
        
        try:
            # Execute cursor command
            result = self._execute_cursor_command(prompt_file)
            
            # Parse result
            execution_result = self._parse_cursor_result(result, start_time)
            
            # Update conversation context
            self.conversation_context.append({
                "prompt": prompt,
                "context": context,
                "result": execution_result,
                "timestamp": time.time()
            })
            
            return execution_result
            
        except Exception as e:
            return CursorExecutionResult(
                success=False,
                output="",
                error=str(e),
                duration=time.time() - start_time,
                files_created=[],
                files_modified=[],
                sentinel_found=False
            )
        finally:
            # Clean up prompt file
            if os.path.exists(prompt_file):
                os.remove(prompt_file)
    
    def execute_fix_prompt(self, fix_prompt: str, error_context: Dict[str, Any]) -> CursorExecutionResult:
        """Execute a fix prompt with Cursor AI"""
        
        # Add error context to the prompt
        contextual_prompt = f"""ERROR CONTEXT:
{json.dumps(error_context, indent=2)}

FIX REQUIREMENTS:
{fix_prompt}

INSTRUCTIONS:
- Analyze the error context above
- Apply the fix requirements
- Don't break existing functionality
- Test the fix before completing
- When done, print: {self.sentinel}"""
        
        return self.execute_prompt(contextual_prompt, error_context)
    
    def _prepare_prompt_with_context(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Prepare prompt with conversation context"""
        
        # Base context
        context_info = f"""CONVERSATION CONTEXT:
- App Root: {self.app_root}
- Previous Steps: {len(self.conversation_context)}
- Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # Add conversation history
        if self.conversation_context:
            context_info += "RECENT CONVERSATION:\n"
            for i, conv in enumerate(self.conversation_context[-3:]):  # Last 3 conversations
                context_info += f"Step {len(self.conversation_context) - 3 + i + 1}:\n"
                context_info += f"  Prompt: {conv['prompt'][:100]}...\n"
                context_info += f"  Success: {conv['result'].success}\n"
                if conv['result'].error:
                    context_info += f"  Error: {conv['result'].error}\n"
                context_info += "\n"
        
        # Add specific context if provided
        if context:
            context_info += f"SPECIFIC CONTEXT:\n{json.dumps(context, indent=2)}\n\n"
        
        # Add the main prompt
        full_prompt = f"""{context_info}

MAIN PROMPT:
{prompt}

COMPLETION REQUIREMENTS:
- When you have COMPLETED the requested step, print EXACTLY this line on its own as the final output:
{self.sentinel}
- If no changes are needed, print: {self.sentinel} (no changes needed)
- If you encounter an error you cannot resolve, print: {self.sentinel} (error: <brief>)
- The sentinel must be the very last output from your response.

Now perform the requested step. Be explicit about file paths and contents you create or modify."""
        
        return full_prompt
    
    def _execute_cursor_command(self, prompt_file: str) -> Dict[str, Any]:
        """Execute cursor command with the prompt file"""
        
        # Use cursor command with proper parameters
        cmd = [
            "cursor",
            "--wait",
            "--new-window",
            self.app_root
        ]
        
        env = os.environ.copy()
        env.update({
            'CURSOR_CI': '1',
            'CURSOR_NO_INTERACTIVE': '1',
            'CURSOR_EXIT_ON_COMPLETION': '1',
            'TERM': 'xterm-256color'
        })
        
        # Execute with timeout and output capture
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.app_root,
                env=env
            )
            
            # Send prompt to stdin
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            
            stdout, stderr = process.communicate(input=prompt_content, timeout=self.timeout)
            
            return {
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "success": process.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "returncode": 124,  # Timeout exit code
                "stdout": "",
                "stderr": "Command timed out",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def _parse_cursor_result(self, result: Dict[str, Any], start_time: float) -> CursorExecutionResult:
        """Parse cursor execution result"""
        
        duration = time.time() - start_time
        output = result.get("stdout", "")
        error = result.get("stderr", "")
        
        # Check for sentinel
        sentinel_found = self.sentinel in output or self.sentinel in error
        
        # Determine success
        success = result.get("success", False) and sentinel_found
        
        # Extract file information (simplified)
        files_created = self._extract_files_created(output)
        files_modified = self._extract_files_modified(output)
        
        return CursorExecutionResult(
            success=success,
            output=output,
            error=error,
            duration=duration,
            files_created=files_created,
            files_modified=files_modified,
            sentinel_found=sentinel_found
        )
    
    def _extract_files_created(self, output: str) -> List[str]:
        """Extract created files from output"""
        files = []
        lines = output.split('\n')
        
        for line in lines:
            if 'created' in line.lower() or 'added' in line.lower():
                # Simple extraction - could be improved with regex
                if '.dart' in line:
                    # Extract file path
                    parts = line.split()
                    for part in parts:
                        if '.dart' in part and '/' in part:
                            files.append(part.strip())
        
        return files
    
    def _extract_files_modified(self, output: str) -> List[str]:
        """Extract modified files from output"""
        files = []
        lines = output.split('\n')
        
        for line in lines:
            if 'modified' in line.lower() or 'updated' in line.lower():
                # Simple extraction - could be improved with regex
                if '.dart' in line:
                    # Extract file path
                    parts = line.split()
                    for part in parts:
                        if '.dart' in part and '/' in part:
                            files.append(part.strip())
        
        return files
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation context"""
        
        total_steps = len(self.conversation_context)
        successful_steps = sum(1 for conv in self.conversation_context if conv['result'].success)
        failed_steps = total_steps - successful_steps
        
        total_duration = sum(conv['result'].duration for conv in self.conversation_context)
        
        all_files_created = []
        all_files_modified = []
        
        for conv in self.conversation_context:
            all_files_created.extend(conv['result'].files_created)
            all_files_modified.extend(conv['result'].files_modified)
        
        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "total_duration": total_duration,
            "average_duration": total_duration / total_steps if total_steps > 0 else 0,
            "files_created": list(set(all_files_created)),
            "files_modified": list(set(all_files_modified)),
            "conversation_context": self.conversation_context
        }
    
    def save_conversation_log(self, output_file: str) -> None:
        """Save conversation log to file"""
        
        log_data = {
            "app_root": self.app_root,
            "conversation_summary": self.get_conversation_summary(),
            "detailed_log": self.conversation_context
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)


class DynamicCursorPipeline:
    """Complete dynamic pipeline with Cursor AI integration"""
    
    def __init__(self, app_root: str, provider: str, api_key: str):
        self.app_root = app_root
        self.cursor_integration = CursorAIIntegration(app_root)
        
        # Import dynamic AI system
        from dynamic_ai_prompt_system import DynamicAIPromptSystem, AIProvider
        
        provider_enum = AIProvider.CHATGPT if provider == 'chatgpt' else AIProvider.DEEPSEEK
        self.ai_system = DynamicAIPromptSystem(provider_enum, api_key)
    
    def run_complete_pipeline(self, app_idea: str, archetype: str) -> Dict[str, Any]:
        """Run the complete dynamic pipeline"""
        
        print(f"🚀 Starting complete dynamic pipeline for {archetype} app...")
        
        # Step 1: Get strategy from AI
        print("📋 Getting development strategy from AI...")
        strategy = self.ai_system.initialize_conversation(app_idea, archetype)
        
        if not strategy:
            raise ValueError("Failed to get development strategy from AI")
        
        print(f"✅ Got strategy with {strategy['total_steps']} steps")
        
        # Step 2: Execute each step
        results = []
        app_state = {"files": [], "features": [], "errors": []}
        
        for step_num in range(1, strategy['total_steps'] + 1):
            print(f"\n🔄 Executing step {step_num}/{strategy['total_steps']}...")
            
            # Generate dynamic prompt
            prompt_data = self.ai_system.generate_dynamic_prompt(step_num, app_state)
            print(f"📝 Generated prompt: {prompt_data['title']}")
            
            # Execute with Cursor AI
            cursor_result = self.cursor_integration.execute_prompt(
                prompt_data['prompt'], 
                {"step": step_num, "app_state": app_state}
            )
            
            print(f"⏱️ Execution time: {cursor_result.duration:.1f}s")
            print(f"✅ Success: {cursor_result.success}")
            
            if cursor_result.success:
                print(f"📁 Files created: {len(cursor_result.files_created)}")
                print(f"📝 Files modified: {len(cursor_result.files_modified)}")
            else:
                print(f"❌ Error: {cursor_result.error}")
            
            # Analyze result
            analysis = self.ai_system.analyze_step_result(step_num, {
                "success": cursor_result.success,
                "output": cursor_result.output,
                "error": cursor_result.error,
                "files_created": cursor_result.files_created,
                "files_modified": cursor_result.files_modified,
                "duration": cursor_result.duration
            })
            
            print(f"📊 Quality score: {analysis['quality_score']}/100")
            
            # Update app state
            if analysis.get('app_state_update'):
                app_state.update(analysis['app_state_update'])
            
            # Handle errors
            if analysis.get('issues_found'):
                print(f"⚠️ Issues found: {analysis['issues_found']}")
                
                # Generate and execute fix
                error_context = {
                    "step": step_num,
                    "issues": analysis['issues_found'],
                    "app_state": app_state,
                    "cursor_output": cursor_result.output,
                    "cursor_error": cursor_result.error
                }
                
                fix_prompt = self.ai_system.generate_fix_prompt(error_context)
                print("🔧 Applying fix...")
                
                fix_result = self.cursor_integration.execute_fix_prompt(fix_prompt, error_context)
                
                if fix_result.success:
                    print("✅ Fix applied successfully")
                else:
                    print(f"❌ Fix failed: {fix_result.error}")
            
            # Record step result
            results.append({
                "step": step_num,
                "prompt_data": prompt_data,
                "cursor_result": cursor_result,
                "analysis": analysis,
                "app_state": app_state.copy()
            })
        
        # Step 3: Generate final report
        conversation_summary = self.cursor_integration.get_conversation_summary()
        
        final_report = {
            "strategy": strategy,
            "results": results,
            "conversation_summary": conversation_summary,
            "app_state": app_state,
            "pipeline_success": conversation_summary["success_rate"] >= 80,
            "total_duration": conversation_summary["total_duration"],
            "recommendations": [
                "Review failed steps and apply fixes",
                "Run comprehensive testing",
                "Optimize performance based on quality scores",
                "Review and improve error handling"
            ]
        }
        
        return final_report


def main():
    """Main function for dynamic cursor pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic Cursor AI Pipeline')
    parser.add_argument('--app-idea', required=True, help='App idea description')
    parser.add_argument('--archetype', default='utility', help='App archetype')
    parser.add_argument('--provider', default='chatgpt', choices=['chatgpt', 'deepseek'], help='AI provider')
    parser.add_argument('--api-key', required=True, help='API key for AI provider')
    parser.add_argument('--app-root', required=True, help='Path to app root directory')
    parser.add_argument('--output', default='dynamic_cursor_report.json', help='Output report file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = DynamicCursorPipeline(args.app_root, args.provider, args.api_key)
    
    if args.verbose:
        print(f"Initializing dynamic cursor pipeline...")
        print(f"App idea: {args.app_idea}")
        print(f"Archetype: {args.archetype}")
        print(f"Provider: {args.provider}")
        print(f"App root: {args.app_root}")
    
    # Run pipeline
    try:
        results = pipeline.run_complete_pipeline(args.app_idea, args.archetype)
        
        # Save results
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save conversation log
        log_file = args.output.replace('.json', '_conversation.json')
        pipeline.cursor_integration.save_conversation_log(log_file)
        
        if args.verbose:
            print(f"\n📊 Pipeline completed!")
            print(f"Total steps: {len(results['results'])}")
            print(f"Success rate: {results['conversation_summary']['success_rate']:.1f}%")
            print(f"Total duration: {results['total_duration']:.1f}s")
            print(f"Pipeline success: {results['pipeline_success']}")
        
        print(f"Dynamic cursor report saved to: {args.output}")
        print(f"Conversation log saved to: {log_file}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
