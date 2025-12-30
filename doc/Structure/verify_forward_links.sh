#!/bin/bash
# Verify forward-facing links in Zim Wiki structure files
# Usage:
#   ./verify_forward_links.sh         # Check only
#   ./verify_forward_links.sh --fix   # Check and fix

cd "$(dirname "$0")"
python3 verify_forward_links.py "$@"
