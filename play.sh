#!/bin/bash
# Temple of Kharkenshar: The Doors of Becoming
# Quick launcher

DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/adventure/scripts/adventure.py" --play temple-of-kharkenshar "$@"
