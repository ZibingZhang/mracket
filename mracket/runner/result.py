"""The mutation runner result."""
from __future__ import annotations

import abc
import dataclasses
import enum
import inspect
import re
from collections.abc import Generator, Iterator
from typing import cast

from mracket import mutation


class Reason(enum.Enum):
    """Runner failure reasons."""

    NOT_DRRACKETY = "Program missing DrRacket prefix."
    NOT_WELL_FORMED_PROGRAM = "Program not well-formed."
    NON_ZERO_MUTANT_RETURNCODE = "Non-zero returncode when running mutant."
    NON_ZERO_ORIGINAL_RETURNCODE = "Non-zero returncode when running original."


class RunnerResult(metaclass=abc.ABCMeta):
    """A runner result."""


class RunnerFailure(RunnerResult, Exception):
    """A runner failure."""

    def __init__(self, reason: Reason, **kwargs) -> None:
        super(Exception, self).__init__(reason.value)
        self.reason = reason
        self.dict = kwargs


class UnmodifiedResult:
    """The result of the original program."""

    def __get__(self, obj: RunnerSuccess, objtype: type) -> ProgramExecutionResult | None:
        if obj._unmodified_result is None:
            return None
        if inspect.isgenerator(obj._unmodified_result):
            obj._unmodified_result = next(obj._unmodified_result)
        return cast(ProgramExecutionResult, obj._unmodified_result)

    def __set__(self, obj: RunnerSuccess, value: Generator[ProgramExecutionResult, None, None]) -> None:
        obj._unmodified_result = value


class RunnerSuccess(RunnerResult):
    """A runner success."""

    unmodified_result = UnmodifiedResult()

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.mutations: list[mutation.Mutation] = []
        self.mutant_results: Iterator[MutantExecutionResult] | None = None

        self._unmodified_result: Generator[ProgramExecutionResult, None, None] | ProgramExecutionResult | None = None

    def pprint(self) -> None:
        if self.unmodified_result is not None:
            print("===================================== ORIGINAL PROGRAM RESULT =====================================")
            print(f"total: {self.unmodified_result.total}")
            print(f"    passed: {self.unmodified_result.passed}")
            print(f"    failed: {len(self.unmodified_result.failures)}")

        if self.mutant_results is not None:
            print("======================================== MUTATION RESULTS =========================================")
            for i, result in enumerate(self.mutant_results):
                print(f"-------------------------------------- MUTATION {i + 1} --------------------------------------")
                print(f"mutation: {result.mutation.explanation}")
                print(f"total: {result.total}")
                print(f"    passed: {result.passed}")
                print(f"    failed: {len(result.failures)}")


class ProgramExecutionResult:
    """A Racket program result."""

    def __init__(self, stdout: bytes) -> None:
        self.passed = -1
        self.failures: list[TestFailure] = []
        self.output = stdout.decode("utf-8")

        if "The test passed!" in self.output:
            self.passed = 1
            return
        if "Both tests passed!" in self.output:
            self.passed = 2
            return
        if re_match := re.search(r"(\d+) tests passed!", self.output):
            self.passed = int(re_match.groups()[0])
            return

        if "0 tests passed." in self.output:
            self.passed = 0
        elif re_match := re.search(r"(\d+) of the (\d+) tests failed.", self.output):
            groups = re_match.groups()
            self.passed = int(groups[1]) - int(groups[0])
        else:
            return

        assert "Check failures:" in self.output

        re_matchs = re.finditer(
            r"Actual value │ (.*?) │ differs from │ (.*?) │, the expected value.*?line (\d+), column (\d+)",
            self.output,
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


class MutantExecutionResult(ProgramExecutionResult):
    """A mutant Racket program result."""

    def __init__(self, stdout: bytes, mut: mutation.Mutation) -> None:
        super().__init__(stdout)
        self.mutation = mut


@dataclasses.dataclass
class TestFailure:
    """A test-case failure."""

    actual: str
    expected: str
    lineno: int
    colno: int

    def __str__(self) -> str:
        return f"Actual value {self.actual} differs from {self.expected}, the expected value"
