"""The mutation runner result."""
from __future__ import annotations

import abc
import dataclasses
import enum
import re
from collections.abc import Iterator

from mracket import mutation


class RunnerResult(metaclass=abc.ABCMeta):
    """A runner result."""


class RunnerFailure(RunnerResult, Exception):
    """A runner failure."""

    class Reason(enum.Enum):
        """Runner failure reason."""

        NOT_DRRACKETY = "Program missing DrRacket prefix"
        NOT_WELL_FORMED_PROGRAM = "Program not well-formed"
        NON_ZERO_MUTANT_RETURNCODE = "Non-zero returncode when running mutant"
        NON_ZERO_UNMODIFIED_RETURNCODE = "Non-zero returncode when running unmodified source"
        UNMODIFIED_TEST_FAILURE = "Test failure when running unmodified source"

    def __init__(self, reason: Reason, **kwargs) -> None:
        super(Exception, self).__init__(reason.value)
        self.reason = reason
        self.dict = kwargs


class RunnerSuccess(RunnerResult):
    """A runner success."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.mutations: list[mutation.Mutation] = []
        self.unmodified_result: ProgramExecutionResult | None = None
        self.mutant_results: Iterator[MutantExecutionResult] | None = None

    @property
    def score(self) -> MutationScore:
        if self.mutant_results is None:
            return MutationScore(total=0, killed=0, execution_error=0)

        killed = 0
        execution_error = 0
        i = -1
        for i, result in enumerate(self.mutant_results):
            if result.stderr:
                execution_error += 1
            elif len(result.failures) > 0:
                killed += 1
        return MutationScore(total=i + 1, killed=killed, execution_error=execution_error)

    def pprint(self) -> None:
        if self.unmodified_result is not None:
            print("===================================== ORIGINAL PROGRAM RESULT =====================================")
            print(f"total: {self.unmodified_result.total}")
            print(f"    passed: {self.unmodified_result.passed}")
            print(f"    failed: {len(self.unmodified_result.failures)}")

        if self.mutant_results is not None:
            killed = 0
            execution_error = 0
            i = -1
            print("======================================== MUTATION RESULTS =========================================")
            for i, result in enumerate(self.mutant_results):
                print(f"-------------------------------------- MUTATION {i + 1} --------------------------------------")
                print(f"mutation: {result.mutation.explanation}")
                if result.stderr:
                    print(f"error: {result.stderr.decode('utf-8')}")
                    execution_error += 1
                else:
                    print(f"total: {result.total}")
                    print(f"    passed: {result.passed}")
                    print(f"    failed: {len(result.failures)}")
                    if len(result.failures) > 0:
                        killed += 1

            print("-------------------------------------- MUTATION SUMMARY --------------------------------------")
            print(f"total: {i + 1}")
            print(f"    killed: {killed}")
            print(f"    execution errors: {execution_error}")


class ProgramExecutionResult:
    """A Racket program result."""

    def __init__(self, stdout: bytes = b"") -> None:
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

        if "Check failures:" in self.output:
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

    def __init__(self, mut: mutation.Mutation, returncode: int, stdout: bytes = b"", stderr: bytes = b"") -> None:
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


@dataclasses.dataclass
class MutationScore:
    """A mutation score."""

    total: int
    killed: int
    execution_error: int
