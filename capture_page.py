#!/usr/bin/env python3
"""
DWI Page Capture & Wait-Page Bypass CLI (Python Wrapper)
Usage:
    python3 capture_page.py https://example.com [--output ./captures] [--no-bypass] [--json]
"""
import sys
import subprocess
import os

def main():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_page.cjs")
    cmd = ["node", script_path] + sys.argv[1:]
    try:
        proc = subprocess.run(cmd)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        print("\n[!] Capture interrupted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
