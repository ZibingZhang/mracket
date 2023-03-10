#!/bin/bash
set -eoux pipefail

python -m pytest mracket -sm "not slow"
python -m black mracket
python -m pflake8 mracket
python -m isort mracket
python -m mypy --explicit-package-bases --ignore-missing-imports mracket
