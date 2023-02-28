#!/bin/bash
FLAGS=(-s -vv -n auto)

set -eoux pipefail

python -m pytest mracket "${FLAGS[@]}" -m "not slow"
python -m pytest mracket "${FLAGS[@]}" -m "slow"
