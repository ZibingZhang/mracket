#!/bin/bash
set -eoux pipefail

python -m pytest mracket -vs
python -m black mracket
python -m pflake8 mracket
python -m isort mracket
python -m mypy mracket --explicit-package-bases
