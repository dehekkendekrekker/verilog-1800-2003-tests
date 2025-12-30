#!/bin/bash
# Verify backlinks in Zim Wiki structure files
# Usage:
#   ./verify_backlinks.sh         # Check only
#   ./verify_backlinks.sh --fix   # Check and fix

cd "$(dirname "$0")"
python3 verify_backlinks.py "$@"
