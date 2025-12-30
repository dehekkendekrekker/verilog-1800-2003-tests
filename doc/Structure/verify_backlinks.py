#!/usr/bin/env python3
"""
Verify and optionally fix backlinks in Zim Wiki files.

Usage:
    python3 verify_backlinks.py          # Check only, report issues
    python3 verify_backlinks.py --fix    # Check and fix issues
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

STRUCTURE_DIR = Path(__file__).parent.resolve()


def get_all_txt_files():
    """Get all .txt files in the Structure directory."""
    files = []
    for root, dirs, filenames in os.walk(STRUCTURE_DIR):
        for f in filenames:
            if f.endswith('.txt'):
                files.append(Path(root) / f)
    return files


def extract_links(content, file_path):
    """Extract all wiki links from content, excluding backlinks section."""
    # Remove backlinks section before extracting links
    backlinks_match = re.search(r'===== Backlinks =====.*', content, re.DOTALL)
    if backlinks_match:
        content = content[:backlinks_match.start()]

    # Find all [[...]] links (not [[+...]] which are child page links)
    links = []
    # Match [[path:to:file|display]] or [[simple_name]]
    pattern = r'\[\[(?!\+)([^\]|]+)(?:\|[^\]]+)?\]\]'
    for match in re.finditer(pattern, content):
        link_target = match.group(1)
        links.append(link_target)
    return links


def resolve_link(link, source_file, name_to_files):
    """Resolve a link to an absolute file path."""
    source_dir = source_file.parent

    if ':' in link:
        # Qualified link like "1_Source_text:1.4_Module_items:module_item"
        parts = link.split(':')
        # Start from Structure root
        target = STRUCTURE_DIR
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                # Directory part
                target = target / part
            else:
                # File part
                target = target / (part + '.txt')
        if target.exists():
            return target
    else:
        # Simple link - same directory
        target = source_dir / (link + '.txt')
        if target.exists():
            return target

    # Fallback: try to find by name only
    target_name = link.split(':')[-1] if ':' in link else link
    if target_name in name_to_files and len(name_to_files[target_name]) == 1:
        return name_to_files[target_name][0]

    return None


def get_link_format(source_file, target_file):
    """Generate the correct link format from source to target."""
    source_dir = source_file.parent
    target_dir = target_file.parent
    target_name = target_file.stem

    if source_dir == target_dir:
        # Same directory - simple link
        return f"[[{target_name}]]"
    else:
        # Different directory - need qualified path
        # Build path from Structure root
        rel_parts = target_file.relative_to(STRUCTURE_DIR).with_suffix('').parts
        path = ':'.join(rel_parts)
        return f"[[{path}|{target_name}]]"


def fix_backlinks_in_file(target_file, expected_sources):
    """Fix the backlinks section in a file."""
    with open(target_file, 'r') as f:
        content = f.read()

    # Find the backlinks section
    backlinks_match = re.search(r'(===== Backlinks =====\n)(.*)', content, re.DOTALL)
    if not backlinks_match:
        return False  # No backlinks section to fix

    header = backlinks_match.group(1)
    content_before = content[:backlinks_match.start()]

    # Generate new backlinks
    if not expected_sources:
        new_backlinks = "(no backlinks)\n"
    else:
        links = []
        for source in sorted(expected_sources, key=lambda x: x.stem):
            link = get_link_format(target_file, source)
            links.append(link)
        new_backlinks = '\n'.join(links) + '\n'

    new_content = content_before + header + new_backlinks

    # Write back
    with open(target_file, 'w') as f:
        f.write(new_content)

    return True


def main():
    fix_mode = '--fix' in sys.argv

    files = get_all_txt_files()
    print(f"Scanning {len(files)} files...")

    # Map from canonical name to file path(s)
    name_to_files = defaultdict(list)
    for f in files:
        name_to_files[f.stem].append(f)

    # Build reverse links map: file -> list of files that link to it
    reverse_links = defaultdict(list)
    unresolved_links = []

    # First pass: extract all forward links and build reverse map
    for source_file in files:
        with open(source_file, 'r') as f:
            content = f.read()

        links = extract_links(content, source_file)
        for link in links:
            target_file = resolve_link(link, source_file, name_to_files)
            if target_file:
                reverse_links[target_file].append(source_file)
            else:
                unresolved_links.append((source_file, link))

    # Report unresolved links
    if unresolved_links:
        print(f"\nWARNING: {len(unresolved_links)} unresolved links found:")
        for source, link in unresolved_links[:10]:  # Show first 10
            print(f"  {source.relative_to(STRUCTURE_DIR)}: [[{link}]]")
        if len(unresolved_links) > 10:
            print(f"  ... and {len(unresolved_links) - 10} more")

    # Second pass: check backlinks
    issues = []

    for target_file in sorted(files):
        with open(target_file, 'r') as f:
            content = f.read()

        # Check if file has backlinks section
        backlinks_match = re.search(r'===== Backlinks =====\n(.*)', content, re.DOTALL)
        if not backlinks_match:
            continue  # No backlinks section

        current_backlinks_text = backlinks_match.group(1).strip()

        # Parse current backlinks
        current_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        current_links = re.findall(current_pattern, current_backlinks_text)

        # Compute expected backlinks
        expected_sources = reverse_links.get(target_file, [])
        expected_sources = sorted(set(expected_sources), key=lambda x: x.stem)

        # Compare current vs expected
        current_set = set()
        for link in current_links:
            resolved = resolve_link(link, target_file, name_to_files)
            if resolved:
                current_set.add(resolved)

        expected_set = set(expected_sources)

        # Check for special markers
        is_no_backlinks = 'no backlinks' in current_backlinks_text.lower() or \
                          'root production' in current_backlinks_text.lower()

        if current_set != expected_set or (is_no_backlinks and expected_set):
            missing = expected_set - current_set
            extra = current_set - expected_set
            issues.append({
                'file': target_file,
                'missing': missing,
                'extra': extra,
                'expected': expected_sources
            })

    # Report and optionally fix issues
    if issues:
        print(f"\n{'='*60}")
        print(f"BACKLINK ISSUES: {len(issues)} files")
        print('='*60)

        for issue in issues:
            rel_path = issue['file'].relative_to(STRUCTURE_DIR)
            print(f"\n{rel_path}:")
            if issue['missing']:
                print(f"  Missing ({len(issue['missing'])}):")
                for m in sorted(issue['missing'], key=lambda x: x.stem):
                    print(f"    + {m.relative_to(STRUCTURE_DIR)}")
            if issue['extra']:
                print(f"  Extra ({len(issue['extra'])}):")
                for e in sorted(issue['extra'], key=lambda x: x.stem):
                    print(f"    - {e.relative_to(STRUCTURE_DIR)}")

            if fix_mode:
                fix_backlinks_in_file(issue['file'], issue['expected'])
                print(f"  -> FIXED")

        if fix_mode:
            print(f"\n\nFixed {len(issues)} files")
        else:
            print(f"\n\nRun with --fix to repair these issues")

        return 1  # Exit with error code if issues found (useful for CI)
    else:
        print("\nAll backlinks are correct!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
