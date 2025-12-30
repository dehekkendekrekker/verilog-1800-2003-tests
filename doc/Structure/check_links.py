#!/usr/bin/env python3
"""
Check all links in a specific file.
"""

import os
import re
import sys

BASE_DIR = '/home/dhk/projects/verilog-1800-2003-tests/doc/Structure'

def check_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, BASE_DIR)
    print(f"Checking: {rel_path}\n")

    # Find all links
    pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
    for match in re.finditer(pattern, content):
        link_path = match.group(1)
        label = match.group(2)

        # Convert zim path to file path
        file_path = link_path.replace(':', '/') + '.txt'
        full_path = os.path.join(BASE_DIR, file_path)

        exists = os.path.isfile(full_path)
        status = "OK" if exists else "BROKEN"

        print(f"  [{status}] [[{link_path}|{label}]]")
        if not exists:
            print(f"         Expected: {file_path}")

if len(sys.argv) > 1:
    check_file(sys.argv[1])
else:
    print("Usage: python3 check_links.py <file>")
