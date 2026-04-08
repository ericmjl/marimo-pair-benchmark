#!/bin/bash

# This script executes code in a marimo notebook kernel
# Usage: execute-code.sh [-c "code"] [file.py]

set -e

# Check if marimo is available
if ! command -v marimo &> /dev/null; then
    echo "marimo could not be found. Please install it with:"
    echo "pip install marimo"
    exit 1
fi

# Function to show usage
usage() {
    echo "Usage: $0 [-c \"code\"] [--url URL] [file.py]"
    echo "  -c \"code\"     : Execute code string"
    echo "  --url URL     : Target specific server URL (skips auto-discovery)"
    echo "  file.py       : Execute code from file"
    exit 1
}

# Parse arguments
CODE=""
URL=""
FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -c)
            CODE="$2"
            shift 2
            ;;
        --url)
            URL="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option $1"
            usage
            ;;
        *)
            FILE="$1"
            shift
            ;;
    esac
done

# Validate inputs
if [[ -n "$CODE" && -n "$FILE" ]]; then
    echo "Error: Cannot specify both -c and a file"
    usage
fi

if [[ -z "$CODE" && -z "$FILE" ]]; then
    echo "Error: Must specify either -c or a file"
    usage
fi

# If we have a file, read the code from it
if [[ -n "$FILE" ]]; then
    if [[ ! -f "$FILE" ]]; then
        echo "Error: File $FILE not found"
        exit 1
    fi
    CODE=$(cat "$FILE")
fi

# Execute the code
if [[ -n "$URL" ]]; then
    # Direct URL mode
    echo "Executing code on $URL..."
    marimo run --url "$URL" -c "$CODE"
else
    # Auto-discovery mode
    echo "Discovering marimo servers and executing code..."
    marimo run -c "$CODE"
fi