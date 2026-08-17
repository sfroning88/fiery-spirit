#!/bin/sh
set -e

echo "Checking Python formatting (black)..."
black --check apps/backend apps/ai packages/python
