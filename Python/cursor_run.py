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


def main():
    SENTINEL = b"~~CURSOR_DONE~~"
    
    with open('.prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    cmd = ["cursor-agent", "-p", "--force", "--output-format", "text", prompt]
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        bufsize=0,
        env=env
    )
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
