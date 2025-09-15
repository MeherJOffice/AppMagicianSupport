#!/usr/bin/env python3
"""
Cursor auto-fix script for AppMagician pipeline.
Automatically fixes Flutter analyze and test issues using cursor-agent.
"""

import subprocess
import sys
import os
import signal
import selectors
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description='Cursor auto-fix script for AppMagician pipeline')
    parser.add_argument('--analyze-file', default='.an.tail', help='Path to analyze output file (default: .an.tail)')
    parser.add_argument('--test-file', default='.ts.tail', help='Path to test output file (default: .ts.tail)')
    parser.add_argument('--app-root', help='Path to app root directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    SENTINEL = b"~~CURSOR_DONE~~"
    step = os.environ.get('STEP', '?')
    
    # Check if files exist, use empty strings if not
    an = ""
    ts = ""
    
    if os.path.exists(args.analyze_file):
        try:
            with open(args.analyze_file, 'r', encoding='utf-8', errors='ignore') as f:
                an = f.read()
        except Exception as e:
            if args.verbose:
                print(f"Warning: Could not read analyze file: {e}")
    else:
        if args.verbose:
            print(f"Warning: Analyze file '{args.analyze_file}' not found")
    
    if os.path.exists(args.test_file):
        try:
            with open(args.test_file, 'r', encoding='utf-8', errors='ignore') as f:
                ts = f.read()
        except Exception as e:
            if args.verbose:
                print(f"Warning: Could not read test file: {e}")
    else:
        if args.verbose:
            print(f"Warning: Test file '{args.test_file}' not found")

    prompt = f"""You are a senior Flutter engineer. The previous step ({step}) introduced issues.
Fix the codebase while preserving the intended feature.

Requirements:
- Do NOT add or nest a Flutter project. Edit the existing project in-place.
- If pubspec.yaml changed, update code/imports accordingly.
- Make 'flutter analyze' pass.
- Make tests pass (add/update minimal tests if needed).
- Keep architecture under lib/features/** tidy.

When done, print EXACTLY:
~~CURSOR_DONE~~

Error snippets:
[analyze]
{an}

[tests]
{ts}
"""

    # Use cursor command instead of cursor-agent
    cmd = ["cursor", "--wait", "--new-window"]
    if args.app_root:
        cmd.append(args.app_root)
    
    env = os.environ.copy()
    env.update({
        'CURSOR_CI': '1',
        'CURSOR_NO_INTERACTIVE': '1',
        'CURSOR_EXIT_ON_COMPLETION': '1',
        'TERM': 'xterm-256color'
    })

    sel = selectors.DefaultSelector()
    HARD_LIMIT = 120.0
    IDLE_LIMIT = 45.0
    start = last = time.time()

    p = subprocess.Popen(
        cmd,
        preexec_fn=os.setsid,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        bufsize=0,
        env=env
    )
    # Send prompt to stdin
    try:
        p.stdin.write(prompt.encode('utf-8'))
        p.stdin.close()
    except Exception as e:
        if args.verbose:
            print(f"Warning: Could not send prompt to stdin: {e}")
    
    sel.register(p.stdout, selectors.EVENT_READ)
    sel.register(p.stderr, selectors.EVENT_READ)

    def emit(b, is_out):
        s = b.decode('utf-8', errors='replace')
        (sys.stdout if is_out else sys.stderr).write(s)

    buf_out = b""
    buf_err = b""
    exit_code = 0
    try:
        while True:
            if p.poll() is not None and not sel.get_map():
                exit_code = p.returncode or 0
                break
            now = time.time()
            if now - start > HARD_LIMIT:
                exit_code = 124
                break
            events = sel.select(timeout=0.5)
            if not events:
                if now - last > IDLE_LIMIT:
                    exit_code = 124
                    break
                continue
            for key, _ in events:
                chunk = key.fileobj.read1(4096) if hasattr(key.fileobj, "read1") else key.fileobj.read(4096)
                if not chunk:
                    try:
                        sel.unregister(key.fileobj)
                    except:
                        pass
                    continue
                last = now
                if key.fileobj is p.stdout:
                    buf_out += chunk
                    emit(chunk, True)
                    if SENTINEL in buf_out:
                        raise SystemExit(0)
                    if len(buf_out) > 1_000_000:
                        buf_out = buf_out[-500_000:]
                else:
                    buf_err += chunk
                    emit(chunk, False)
                    if SENTINEL in buf_err:
                        raise SystemExit(0)
                    if len(buf_err) > 1_000_000:
                        buf_err = buf_err[-500_000:]
    except SystemExit:
        exit_code = 0
    finally:
        try:
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
        except Exception:
            pass
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
