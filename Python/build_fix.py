#!/usr/bin/env python3
"""
Build auto-fix script for AppMagician pipeline.
Automatically fixes Flutter build issues using cursor-agent.
"""

import subprocess
import sys
import argparse
import os


def main():
    parser = argparse.ArgumentParser(description='Build auto-fix script for AppMagician pipeline')
    parser.add_argument('--prompt-file', default='.prompt.txt', help='Path to prompt file (default: .prompt.txt)')
    parser.add_argument('--app-root', help='Path to app root directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Check if prompt file exists
    if not os.path.exists(args.prompt_file):
        print(f"Error: Prompt file '{args.prompt_file}' not found")
        print("Usage: python3 build_fix.py [--prompt-file PATH] [--app-root PATH] [--verbose]")
        sys.exit(1)
    
    try:
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        sys.exit(1)
    
    if args.verbose:
        print(f"Using prompt file: {args.prompt_file}")
        print(f"Prompt content length: {len(prompt)} characters")
    
    # Use cursor command instead of cursor-agent
    cmd = ["cursor", "--wait", "--new-window"]
    if args.app_root:
        cmd.append(args.app_root)
    
    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        out, _ = p.communicate(prompt)
        print(out)
        
        if p.returncode != 0:
            print(f"Cursor command failed with exit code: {p.returncode}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running cursor command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
