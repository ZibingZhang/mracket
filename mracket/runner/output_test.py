"""Tests for mracket.runner.output."""

from __future__ import annotations

import subprocess

import pytest

from mracket import test
from mracket.runner.output import ProgramOutput


@pytest.mark.parametrize(
    "filename,passed,failed",
    [
        ["test-case-0-0.rkt", 0, 0],
        ["test-case-1-0.rkt", 1, 0],
        ["test-case-2-0.rkt", 2, 0],
        ["test-case-3-0.rkt", 3, 0],
        ["test-case-0-1.rkt", 0, 1],
        ["test-case-0-2.rkt", 0, 2],
        ["test-case-2-1.rkt", 2, 1],
    ],
)
@pytest.mark.slow
def test_program_output_parsing(filename: str, passed: int, failed: int) -> None:
    filepath = next(test.inputs.file_paths(filename))
    process = subprocess.Popen(["racket", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    output = ProgramOutput(stdout.decode("utf-8"))

    assert process.returncode == 0
    assert len(stderr) == 0
    assert output.passed == passed
    assert output.failed == failed
