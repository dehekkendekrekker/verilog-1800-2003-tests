#!/usr/bin/env python3
"""
Verify and optionally fix forward-facing links in Zim Wiki files.

This script checks that all [[link]] references in the grammar content
point to valid files and uses the correct path format.

Usage:
    python3 verify_forward_links.py          # Check only, report issues
    python3 verify_forward_links.py --fix    # Check and fix issues
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


def get_content_section(content):
    """Get content before the Backlinks section."""
    backlinks_match = re.search(r'===== Backlinks =====.*', content, re.DOTALL)
    if backlinks_match:
        return content[:backlinks_match.start()], content[backlinks_match.start():]
    return content, ""


def resolve_link_target(link_path, source_file, name_to_files):
    """
    Try to resolve a link to a target file.
    Returns (target_file, is_resolved) tuple.
    """
    source_dir = source_file.parent

    if ':' in link_path:
        # Qualified path like "1_Source_text:1.4_Module_items:module_item"
        parts = link_path.split(':')
        target = STRUCTURE_DIR
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                target = target / part
            else:
                target = target / (part + '.txt')
        if target.exists():
            return target, True
    else:
        # Simple link - check same directory first
        target = source_dir / (link_path + '.txt')
        if target.exists():
            return target, True

    # Fallback: search by name
    if ':' in link_path:
        name = link_path.split(':')[-1]
    else:
        name = link_path

    if name in name_to_files:
        matches = name_to_files[name]
        if len(matches) == 1:
            return matches[0], True
        elif len(matches) > 1:
            # Multiple matches - ambiguous
            return matches, False

    return None, False


def get_correct_link_format(source_file, target_file, display_name=None):
    """
    Generate the correct link format from source to target.
    If display_name is provided and differs from target name, preserve it.
    """
    source_dir = source_file.parent
    target_dir = target_file.parent
    target_name = target_file.stem

    # Check if we need a custom display name
    needs_custom_display = display_name and display_name != target_name

    if source_dir == target_dir:
        # Same directory - simple link
        if needs_custom_display:
            return f"[[{target_name}|{display_name}]]"
        else:
            return f"[[{target_name}]]"
    else:
        # Different directory - need qualified path
        rel_parts = target_file.relative_to(STRUCTURE_DIR).with_suffix('').parts
        path = ':'.join(rel_parts)
        if needs_custom_display:
            return f"[[{path}|{display_name}]]"
        else:
            return f"[[{path}|{target_name}]]"


def find_all_links(content):
    """
    Find all wiki links in content with their positions.
    Returns list of dicts with link info.
    """
    links = []
    # Match [[path|display]] or [[path]] but not [[+child]]
    pattern = r'\[\[(?!\+)([^\]|]+)(?:\|([^\]]+))?\]\]'
    for match in re.finditer(pattern, content):
        links.append({
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0),
            'link_path': match.group(1),
            'display_name': match.group(2)  # May be None
        })
    return links


def check_and_fix_file(source_file, name_to_files, fix_mode):
    """
    Check and optionally fix forward links in a file.
    Returns (issues_found, issues_fixed) counts.
    """
    with open(source_file, 'r') as f:
        content = f.read()

    content_section, backlinks_section = get_content_section(content)
    links = find_all_links(content_section)

    issues = []

    for link_info in links:
        link_path = link_info['link_path']
        display_name = link_info['display_name']

        result, resolved = resolve_link_target(link_path, source_file, name_to_files)

        if not resolved:
            if result is None:
                # Completely unresolved
                issues.append({
                    'type': 'unresolved',
                    'link_info': link_info,
                    'message': f"Cannot find target for [[{link_path}]]"
                })
            elif isinstance(result, list):
                # Ambiguous - multiple matches
                issues.append({
                    'type': 'ambiguous',
                    'link_info': link_info,
                    'candidates': result,
                    'message': f"Ambiguous link [[{link_path}]] - {len(result)} matches"
                })
        else:
            # Resolved - check if format is correct
            target_file = result
            correct_format = get_correct_link_format(source_file, target_file, display_name)
            current_format = link_info['full_match']

            if current_format != correct_format:
                issues.append({
                    'type': 'wrong_format',
                    'link_info': link_info,
                    'target': target_file,
                    'correct_format': correct_format,
                    'message': f"{current_format} -> {correct_format}"
                })

    if not issues:
        return 0, 0

    # Report issues
    rel_path = source_file.relative_to(STRUCTURE_DIR)
    print(f"\n{rel_path}:")

    fixable_count = 0
    for issue in issues:
        if issue['type'] == 'unresolved':
            print(f"  ERROR: {issue['message']}")
        elif issue['type'] == 'ambiguous':
            print(f"  WARNING: {issue['message']}")
            for c in issue['candidates'][:3]:
                print(f"           -> {c.relative_to(STRUCTURE_DIR)}")
        elif issue['type'] == 'wrong_format':
            print(f"  FIX: {issue['message']}")
            fixable_count += 1

    # Fix if requested
    fixed_count = 0
    if fix_mode:
        # Apply fixes in reverse order to preserve positions
        fixable_issues = [i for i in issues if i['type'] == 'wrong_format']
        fixable_issues.sort(key=lambda x: x['link_info']['start'], reverse=True)

        new_content = content_section
        for issue in fixable_issues:
            link_info = issue['link_info']
            new_content = (
                new_content[:link_info['start']] +
                issue['correct_format'] +
                new_content[link_info['end']:]
            )
            fixed_count += 1

        if fixed_count > 0:
            with open(source_file, 'w') as f:
                f.write(new_content + backlinks_section)
            print(f"  -> Fixed {fixed_count} links")

    return len(issues), fixed_count


def main():
    fix_mode = '--fix' in sys.argv

    files = get_all_txt_files()
    print(f"Scanning {len(files)} files for forward link issues...")

    # Build name -> files map
    name_to_files = defaultdict(list)
    for f in files:
        name_to_files[f.stem].append(f)

    # Check for duplicate names (informational)
    duplicates = {name: paths for name, paths in name_to_files.items() if len(paths) > 1}
    if duplicates:
        print(f"\nNote: {len(duplicates)} grammar elements exist in multiple locations:")
        for name, paths in sorted(duplicates.items())[:5]:
            print(f"  {name}:")
            for p in paths:
                print(f"    - {p.relative_to(STRUCTURE_DIR)}")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")

    # Process all files
    total_issues = 0
    total_fixed = 0
    files_with_issues = 0

    print(f"\n{'='*60}")
    print("FORWARD LINK ANALYSIS")
    print('='*60)

    for source_file in sorted(files):
        issues, fixed = check_and_fix_file(source_file, name_to_files, fix_mode)
        if issues > 0:
            files_with_issues += 1
            total_issues += issues
            total_fixed += fixed

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)

    if total_issues == 0:
        print("All forward links are correct!")
        return 0
    else:
        print(f"Files with issues: {files_with_issues}")
        print(f"Total issues found: {total_issues}")
        if fix_mode:
            print(f"Issues fixed: {total_fixed}")
            unfixed = total_issues - total_fixed
            if unfixed > 0:
                print(f"Issues requiring manual attention: {unfixed}")
        else:
            print("\nRun with --fix to repair fixable issues")
        return 1


if __name__ == '__main__':
    sys.exit(main())
