#!/bin/sh
set -e
cd "$(dirname "$0")/.."
for dir in apps/dashboard apps/backend apps/ai apps/trainer; do
  [ -d "$dir" ] && ln -sf ../../../.env "$dir/.env"
done
