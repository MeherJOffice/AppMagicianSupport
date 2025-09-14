#!/usr/bin/env python3
"""
Build auto-fix script for AppMagician pipeline.
Automatically fixes Flutter build issues using cursor-agent.
"""

import subprocess
import sys


def main():
    with open('.prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    p = subprocess.Popen(
        ["cursor-agent", "edit", "--apply", "--from", "pipeline"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    out, _ = p.communicate(prompt)
    print(out)
    if "~~CURSOR_DONE~~" not in out:
        sys.exit(1)


if __name__ == "__main__":
    main()
