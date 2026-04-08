#!/bin/bash

# This script discovers running marimo sessions
# Usage: discover-servers.sh

set -e

# Check if marimo is available
if ! command -v marimo &> /dev/null; then
    echo "marimo could not be found. Please install it with:"
    echo "pip install marimo"
    exit 1
fi

# Discover marimo servers
echo "Discovering marimo servers..."
marimo list