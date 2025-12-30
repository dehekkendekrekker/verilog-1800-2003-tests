#!/usr/bin/env python3
"""
Fix all broken links by converting relative links to full path links.
All links must use full zim path format: [[path:to:element|label]]
"""

import os
import re

BASE_DIR = '/home/dhk/projects/verilog-1800-2003-tests/doc/Structure'

def build_element_index():
    """Build a map of element_name -> zim_path."""
    elements = {}

    for root, dirs, files in os.walk(BASE_DIR):
        for filename in files:
            if not filename.endswith('.txt') or filename.endswith('.py'):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, BASE_DIR)
            zim_path = rel_path[:-4].replace('/', ':')

            # Get element name from file content
            with open(filepath, 'r') as f:
                content = f.read()

            match = re.search(r'^([a-z0-9_][a-z0-9_]*)\s*::=', content, re.MULTILINE)
            if match:
                element_name = match.group(1)
                elements[element_name] = zim_path

            # Also index by filename (with spaces replaced by underscores)
            base_name = filename[:-4].replace(' ', '_')
            if base_name not in elements:
                elements[base_name] = zim_path

    return elements

def fix_file(filepath, elements):
    """Fix all links in a file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content
    current_zim = os.path.relpath(filepath, BASE_DIR)[:-4].replace('/', ':')
    current_dir = ':'.join(current_zim.split(':')[:-1])

    # Find all links
    pattern = r'\[\[([^\]|]+)(\|([^\]]+))?\]\]'

    def replace_link(match):
        link_path = match.group(1)
        has_label = match.group(2) is not None
        label = match.group(3) if has_label else None

        # Skip subpage links (start with +)
        if link_path.startswith('+'):
            return match.group(0)

        # Check if link already has a path with colons
        if ':' in link_path:
            # Verify it resolves
            file_path = link_path.replace(':', '/') + '.txt'
            full_path = os.path.join(BASE_DIR, file_path)
            if os.path.isfile(full_path):
                return match.group(0)
            # Extract element name from path and try to resolve
            element_name = link_path.split(':')[-1]
        else:
            element_name = link_path

        # Look up the element in our index
        if element_name in elements:
            target_zim = elements[element_name]

            # Always use full path with label
            if label:
                return f'[[{target_zim}|{label}]]'
            else:
                return f'[[{target_zim}|{element_name}]]'

        # Element not found, keep original
        return match.group(0)

    content = re.sub(pattern, replace_link, content)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    print("Building element index...")
    elements = build_element_index()
    print(f"Found {len(elements)} elements\n")

    fixed = 0
    for root, dirs, files in os.walk(BASE_DIR):
        for filename in files:
            if not filename.endswith('.txt') or filename.endswith('.py'):
                continue

            filepath = os.path.join(root, filename)
            if fix_file(filepath, elements):
                rel_path = os.path.relpath(filepath, BASE_DIR)
                print(f"Fixed: {rel_path}")
                fixed += 1

    print(f"\nTotal files fixed: {fixed}")

if __name__ == '__main__':
    main()
