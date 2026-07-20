#!/usr/bin/env bash
set -euo pipefail
python solve.py "$1" "$2"
printf '{"renderer":"public-baseline"}' > "$3"
