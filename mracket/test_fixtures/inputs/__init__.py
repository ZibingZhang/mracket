"""Read the input files."""
from __future__ import annotations

import os
from typing import Generator


def read() -> Generator[str, None, None]:
    """Yield the contents of all Racket files in this directory."""
    # get all files in this directory that end in .rkt
    file_directory = os.path.dirname(os.path.realpath(__file__))
    input_files = list(filter(lambda filename: filename.endswith(".rkt"), os.listdir(file_directory)))
    # for each file, yield its contents
    for input_file in input_files:
        with open(os.path.join(file_directory, input_file)) as f:
            input_file_contents = f.read()
        yield input_file_contents
