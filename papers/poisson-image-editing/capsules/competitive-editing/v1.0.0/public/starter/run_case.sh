#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$2"
python solve.py "$1" "$2/result.json"
