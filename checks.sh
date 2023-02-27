#!/bin/bash
set -eoux pipefail

python -m pytest mracket -vs -m "not slow"
python -m black mracket
python -m pflake8 mracket
python -m isort mracket
python -m mypy mracket --explicit-package-bases
