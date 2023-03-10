"""Program execution result."""
from __future__ import annotations

import re

from mracket import mutation


class ProgramOutput:
    """A Racket program output."""

    def __init__(self, stdout: str) -> None:
        self.passed = 0
        self.failed = 0
        self.stdout = stdout

        if "The test passed!" in self.stdout:
            self.passed = 1
            return
        if "Both tests passed!" in self.stdout:
            self.passed = 2
            return
        if re_match := re.search(r"(\d+) tests passed!", self.stdout):
            self.passed = int(re_match.groups()[0])
            return

        if re_match := re.search(r"Ran (\d+) test.*?0 tests passed\.", self.stdout, re.DOTALL):
            groups = re_match.groups()
            self.passed = 0
            self.failed = int(groups[0])
        elif re_match := re.search(r"(\d+) of the (\d+) tests failed\.", self.stdout):
            groups = re_match.groups()
            self.failed = int(groups[0])
            self.passed = int(groups[1]) - self.failed

    @property
    def total(self) -> int:
        return self.passed + self.failed


class MutantOutput(ProgramOutput):
    """A mutant Racket program output."""

    def __init__(self, mut: mutation.Mutation, returncode: int, stdout: str = "", stderr: str = "") -> None:
        super().__init__(stdout)
        self.mutation = mut
        self.stderr = stderr
        self.returncode = returncode
