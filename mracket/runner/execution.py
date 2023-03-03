"""Program execution result."""
from __future__ import annotations

import dataclasses
import re

from mracket import mutation


class ProgramOutput:
    """A Racket program output."""

    def __init__(self, stdout: str = "") -> None:
        self.passed = -1
        self.failures: list[TestFailure] = []
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

        if "0 tests passed." in self.stdout:
            self.passed = 0
        elif re_match := re.search(r"(\d+) of the (\d+) tests failed.", self.stdout):
            groups = re_match.groups()
            self.passed = int(groups[1]) - int(groups[0])
        else:
            return

        if "Check failures:" in self.stdout:
            re_matchs = re.finditer(
                r"Actual value │ (.*?) │ differs from │ (.*?) │, the expected value.*?line (\d+), column (\d+)",
                self.stdout,
                re.DOTALL,
            )
            for re_match in re_matchs:
                groups = re_match.groups()
                actual = groups[0]
                expected = groups[1]
                lineno = int(groups[2])
                colno = int(groups[3])
                self.failures.append(TestFailure(actual, expected, lineno, colno))

    @property
    def total(self) -> int:
        return self.passed + len(self.failures)


class MutantOutput(ProgramOutput):
    """A mutant Racket program output."""

    def __init__(self, mut: mutation.Mutation, returncode: int, stdout: str = "", stderr: str = "") -> None:
        super().__init__(stdout)
        self.mutation = mut
        self.stderr = stderr
        self.returncode = returncode


@dataclasses.dataclass
class TestFailure:
    """A test-case failure."""

    actual: str
    expected: str
    lineno: int
    colno: int

    def __str__(self) -> str:
        return f"Actual value {self.actual} differs from {self.expected}, the expected value"
