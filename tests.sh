#!/bin/bash
FLAGS=(-s -vv)

set -eoux pipefail

python -m pytest mracket "${FLAGS[@]}" -m "not slow"
python -m pytest mracket "${FLAGS[@]}" -n auto -m "slow"
