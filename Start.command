#!/bin/bash
# Navigate to the directory where this script is located
cd "$(dirname "$0")"

# Execute the start script
./scripts/start.sh

# Prompt to close the terminal window
echo ""
echo "----------------------------------------------------------------------"
echo "Press any key or close this Terminal window to exit."
read -n 1 -s
