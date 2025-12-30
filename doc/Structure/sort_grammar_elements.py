#!/usr/bin/env python3
"""
Sort grammar elements alphabetically within each section of grammar_elements.txt
Preserves the Zim wiki header and section headers (A1.1, A2.1.1, etc.)
"""

import re
import sys

def sort_grammar_elements(input_file, output_file=None):
    if output_file is None:
        output_file = input_file

    with open(input_file, 'r') as f:
        content = f.read()

    # Split into lines
    lines = content.split('\n')

    # Find the header (everything before first section)
    header_lines = []
    # Match section headers with or without ===== formatting
    section_pattern = re.compile(r'^(=====\s*)?(A\d+(\.\d+)*\.?)(\s*=====)?$')

    i = 0
    while i < len(lines):
        match = section_pattern.match(lines[i].strip())
        if match:
            break
        header_lines.append(lines[i])
        i += 1

    # Process sections
    sections = []
    current_section = None
    current_elements = []

    while i < len(lines):
        line = lines[i].strip()
        match = section_pattern.match(line)

        if match:
            # Save previous section if exists
            if current_section is not None:
                sections.append((current_section, sorted([e for e in current_elements if e])))
            # Extract just the section number (e.g., A1.1, A2.2.1)
            current_section = match.group(2).rstrip('.')
            current_elements = []
        elif line:  # Non-empty line that's not a section header
            current_elements.append(line)

        i += 1

    # Don't forget the last section
    if current_section is not None:
        sections.append((current_section, sorted([e for e in current_elements if e])))

    # Build output
    output_lines = header_lines

    for section_name, elements in sections:
        # Format section header with ===== on both sides (Zim wiki format)
        output_lines.append(f'===== {section_name} =====')
        for elem in elements:
            output_lines.append(elem)
        output_lines.append('')  # Empty line after each section

    # Write output
    with open(output_file, 'w') as f:
        f.write('\n'.join(output_lines))

    print(f"Sorted {len(sections)} sections in {input_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        input_file = '/home/dhk/projects/verilog-1800-2003-tests/doc/grammar_elements.txt'
    else:
        input_file = sys.argv[1]

    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    sort_grammar_elements(input_file, output_file)
