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

    def __init__(self, filepath: str, execution_succeeded: bool) -> None:
        self.filepath = filepath
        self.execution_succeeded = execution_succeeded

    @property
    def score(self) -> MutationScore:
        return MutationScore(-1, -1, -1)

    def to_dict(self) -> dict:
        return {
            "filepath": self.filepath,
            "execution-succeeded": self.execution_succeeded,
        }


class RunnerFailure(RunnerResult, Exception):
    """A runner failure."""

    class Reason(enum.Enum):
        """Runner failure reason."""

        READER_ERROR = "Reader unable to read program"
        NOT_DRRACKETY = "Program missing DrRacket prefix"
        NOT_WELL_FORMED_PROGRAM = "Program not well-formed"
        NON_ZERO_MUTANT_RETURNCODE = "Non-zero returncode when running mutant"
        NON_ZERO_UNMODIFIED_RETURNCODE = "Non-zero returncode when running unmodified source"
        UNKNOWN_ERROR = "Unknown error"
        UNMODIFIED_TEST_FAILURE = "Test failure when running unmodified source"

    def __init__(self, reason: Reason, **kwargs) -> None:
        RunnerResult.__init__(self, filepath="", execution_succeeded=False)
        Exception.__init__(self, reason.value)
        self.reason = reason
        self.dict = kwargs

    def to_dict(self) -> dict:
        return {
            **RunnerResult.to_dict(self),
            "reason": self.reason.value,
            **self.dict,
        }


class RunnerSuccess(RunnerResult):
    """A runner success."""

    def __init__(self, filepath: str) -> None:
        super().__init__(filepath=filepath, execution_succeeded=True)
        self.mutations: list[mutation.Mutation] = []
        self.unmodified_result: ProgramExecutionResult | None = None
        self.mutant_results: Iterator[MutantExecutionResult] | None = None

        self._evaluated_mutant_results: list[MutantExecutionResult] = []
        self._total = 0
        self._killed = 0
        self._execution_error = 0

    @property
    def score(self) -> MutationScore:
        self._evaluate_mutants()
        return MutationScore(total=self._total, killed=self._killed, execution_error=self._execution_error)

    def to_dict(self) -> dict:
        self._evaluate_mutants()
        mutation_results: list[dict[str, bool | str]] = []
        for evaluated_mutant_result in self._evaluated_mutant_results:
            mutation_result: dict[str, bool | str] = {"explanation": evaluated_mutant_result.mutation.explanation}
            if evaluated_mutant_result.stderr != "":
                mutation_result["execution-error"] = evaluated_mutant_result.stderr
            else:
                mutation_result["killed"] = len(evaluated_mutant_result.failures) > 0
            mutation_results.append(mutation_result)

        return {
            **super().to_dict(),
            "summary": {"total": self._total, "killed": self._killed, "execution-error": self._execution_error},
            "mutations": mutation_results,
        }

    def _evaluate_mutants(self) -> None:
        if self.mutant_results is None:
            return None

        killed = 0
        execution_error = 0
        i = -1
        for i, result in enumerate(self.mutant_results):
            self._evaluated_mutant_results.append(result)
            if result.stderr:
                execution_error += 1
            elif len(result.failures) > 0:
                killed += 1

        self._total = i + 1
        self._killed = killed
        self._execution_error = execution_error
        self.mutant_results = None


class ProgramExecutionResult:
    """A Racket program result."""

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


class MutantExecutionResult(ProgramExecutionResult):
    """A mutant Racket program result."""

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


@dataclasses.dataclass
class MutationScore:
    """A mutation score."""

    total: int
    killed: int
    execution_error: int
