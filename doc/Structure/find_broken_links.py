#!/usr/bin/env python3
"""
Find all broken links across all files.
"""

import os
import re

BASE_DIR = '/home/dhk/projects/verilog-1800-2003-tests/doc/Structure'

def check_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    broken = []

    # Find all links
    pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
    for match in re.finditer(pattern, content):
        link_path = match.group(1)
        label = match.group(2)

        # Convert zim path to file path
        file_path = link_path.replace(':', '/') + '.txt'
        full_path = os.path.join(BASE_DIR, file_path)

        if not os.path.isfile(full_path):
            broken.append({
                'link': match.group(0),
                'path': link_path,
                'label': label,
                'expected': file_path
            })

    return broken

def main():
    all_broken = []

    for root, dirs, files in os.walk(BASE_DIR):
        for filename in files:
            if not filename.endswith('.txt') or filename.endswith('.py'):
                continue

            filepath = os.path.join(root, filename)
            broken = check_file(filepath)

            if broken:
                rel_path = os.path.relpath(filepath, BASE_DIR)
                all_broken.append((rel_path, broken))

    if all_broken:
        print("Found broken links:\n")
        for rel_path, broken in all_broken:
            print(f"{rel_path}:")
            for b in broken:
                print(f"  {b['link']}")
                print(f"    Expected: {b['expected']}")
            print()
        print(f"Total files with broken links: {len(all_broken)}")
    else:
        print("No broken links found!")

if __name__ == '__main__':
    main()
