"""Utilities to access input files for tests."""
from __future__ import annotations

import os
import re
from collections.abc import Generator


def file_names() -> Generator[str, None, None]:
    """Yield the names of the Racket files in this directory."""
    file_directory = os.path.dirname(os.path.realpath(__file__))
    files = list(filter(lambda filename: filename.endswith(".rkt"), os.listdir(file_directory)))
    for file in files:
        yield os.path.join(file_directory, file)


def read_contents(file_name_pattern: str = ".*") -> Generator[str, None, None]:
    """Yield the contents of all Racket files in this directory."""
    for file_name in file_names():
        if re.match(rf".*{file_name_pattern}", file_name):
            with open(file_name) as f:
                input_file_contents = f.read()
            yield input_file_contents
