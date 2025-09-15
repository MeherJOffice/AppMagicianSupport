#!/usr/bin/env python3
"""
Cursor run script for AppMagician pipeline.
Executes cursor-agent with prompts and handles output with sentinel detection.
"""

import subprocess
import sys
import os
import signal
import selectors
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description='Cursor run script for AppMagician pipeline')
    parser.add_argument('--prompt-file', default='.prompt.txt', help='Path to prompt file (default: .prompt.txt)')
    parser.add_argument('--app-root', help='Path to app root directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    SENTINEL = b"~~CURSOR_DONE~~"
    
    # Check if prompt file exists
    if not os.path.exists(args.prompt_file):
        print(f"Error: Prompt file '{args.prompt_file}' not found")
        print("Usage: python3 cursor_run.py [--prompt-file PATH] [--app-root PATH] [--verbose]")
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
    
    env = os.environ.copy()
    env.update({
        'CURSOR_CI': '1',
        'CURSOR_NO_INTERACTIVE': '1',
        'CURSOR_EXIT_ON_COMPLETION': '1',
        'TERM': 'xterm-256color'
    })

    sel = selectors.DefaultSelector()
    HARD_LIMIT = 300.0
    IDLE_LIMIT = 60.0
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
