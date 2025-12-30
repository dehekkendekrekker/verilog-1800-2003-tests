#!/bin/bash
# Verify all links (forward and backward) in Zim Wiki structure files
# Usage:
#   ./verify_all_links.sh         # Check only
#   ./verify_all_links.sh --fix   # Check and fix

cd "$(dirname "$0")"

echo "========================================"
echo "Checking forward links..."
echo "========================================"
python3 verify_forward_links.py "$@"
forward_status=$?

echo ""
echo "========================================"
echo "Checking backlinks..."
echo "========================================"
python3 verify_backlinks.py "$@"
backlinks_status=$?

echo ""
echo "========================================"
echo "OVERALL STATUS"
echo "========================================"
if [ $forward_status -eq 0 ] && [ $backlinks_status -eq 0 ]; then
    echo "All links are correct!"
    exit 0
else
    echo "Issues found. Run with --fix to repair."
    exit 1
fi
