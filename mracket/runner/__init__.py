"""The mutation testing runner."""
from __future__ import annotations

import itertools
import os.path
import subprocess
import tempfile
import uuid
from collections.abc import Generator, Iterable
from typing import cast

from mracket import mutation, reader
from mracket.mutation import applier, mutator
from mracket.reader import lexer, parser, syntax
from mracket.runner import logger, output, result

DRRACKET_PREFIX = ";; The first three lines of this file were inserted by DrRacket."
PROGRAM_SUFFIX = "(require test-engine/racket-tests)\n(test)"


class Runner:
    """Runs a set of mutations on a file."""

    BATCH_SIZE = 100
    DIR = tempfile.gettempdir()

    def __init__(self, mutator_: mutator.Mutator, filepath: str) -> None:
        self.mutator = mutator_
        self.filepath = filepath

        self.result: result.RunnerResult = cast(result.RunnerResult, None)

    def run(self) -> None:
        """Evaluate the program and its mutants."""
        try:
            success = result.RunnerSuccess(filepath=self.filepath)
            self.check_file_exists(self.filepath)
            success.unmodified_result = self.run_unmodified(self.filepath)
            program = self.build_syntax_tree(self.filepath)
            success.mutations = self.generate_mutations(self.mutator, program)
            mutation_mutants = self.apply_mutations(program, success.mutations)
            success.mutant_results = self.run_mutants(mutation_mutants)
            self.result = success
        except result.RunnerFailure as e:
            e.filepath = self.filepath
            self.result = e
        except BaseException as e:
            self.result = result.RunnerFailure(reason=result.RunnerFailure.Reason.UNKNOWN_ERROR, cause=str(e))

    @staticmethod
    def check_file_exists(filename: str) -> None:
        """Check that the file exists.

        :param filename: Racket program filename
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"{filename} not found.")

    @staticmethod
    def run_unmodified(filepath: str) -> output.ProgramOutput:
        """Run the original program.

        The source code is not being run but rather the stringified program. The reason
        is that we want the positions of the errors, if any exist, to be the same
        between the original and the mutants.

        :param filepath: Racket program filename
        :return: Result of running the unmodified program
        """
        logger.LOGGER.debug("Running the unmodified program")
        process = Runner._run_program(filepath)
        stdout, stderr = process.communicate()
        if process.returncode != 0 or len(stderr) > 0:
            raise result.RunnerFailure(
                reason=result.RunnerFailure.Reason.NON_ZERO_UNMODIFIED_RETURNCODE,
                returncode=process.returncode,
                stderr=stderr.decode("utf-8"),
            )
        unmodified_result = output.ProgramOutput(stdout.decode("utf-8"))
        if unmodified_result.failed > 0:
            raise result.RunnerFailure(reason=result.RunnerFailure.Reason.UNMODIFIED_TEST_FAILURE)
        return unmodified_result

    @staticmethod
    def build_syntax_tree(filepath: str) -> syntax.RacketProgramNode:
        """Build an abstract syntax tree of the Racket program.

        :param filepath: Racket program filepath
        :return: A program abstract syntax tree
        """
        with open(filepath) as f:
            source = f.read()
        if not source.startswith(DRRACKET_PREFIX):
            raise result.RunnerFailure(reason=result.RunnerFailure.Reason.NOT_DRRACKETY)
        try:
            logger.LOGGER.debug("Tokenizing")
            tokens = lexer.Lexer().tokenize(source)
            logger.LOGGER.debug("Parsing")
            program = parser.Parser().parse(tokens)
        except reader.errors.ReaderError as e:
            raise result.RunnerFailure(reason=result.RunnerFailure.Reason.READER_ERROR, cause=str(e))
        return program

    @staticmethod
    def generate_mutations(mutator_: mutator.Mutator, program: syntax.RacketProgramNode) -> list[mutation.Mutation]:
        """Generate mutations.

        :param mutator_: A mutator
        :param program: A program to be mutated
        :return: List of mutations
        """
        logger.LOGGER.debug("Generating mutations")
        mutations = list(mutator_.generate_mutations(program))
        logger.LOGGER.debug(f"Generated {len(mutations)} mutations")
        return mutations

    @staticmethod
    def apply_mutations(
        program: syntax.RacketProgramNode, mutations: Iterable[mutation.Mutation]
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        """Apply the mutations.

        :param program: A program to mutate
        :param mutations: Iterator of mutations to apply to the program
        :return: Generator of mutation-mutant pairs
        """
        mutation_applier = applier.MutationApplier(program, list(mutations))
        mutation_mutants = mutation_applier.apply_mutations()
        return mutation_mutants

    @staticmethod
    def run_mutants(
        mutation_mutants: Iterable[tuple[mutation.Mutation, str]]
    ) -> Generator[output.MutantOutput, None, None]:
        """Run the mutants.

        :param mutation_mutants: An iterator of mutation-mutant pairs
        :return: Generator of mutant execution results
        """
        logger.LOGGER.debug("Running the mutated programs")
        for batch in Runner._batched(mutation_mutants):
            filenames = [Runner._random_filename() for _ in range(Runner.BATCH_SIZE)]
            mutation_processes = []
            for (mut, mutant), filename in zip(batch, filenames):
                Runner._create_file(filename, mutant)
                process = Runner._run_program(filename)
                mutation_processes.append((mut, process))

            for (mut, process), filename in zip(mutation_processes, filenames):
                stdout, stderr = process.communicate()
                Runner._delete_file(filename)
                if process.returncode != 0 or len(stderr) > 0:
                    yield output.MutantOutput(mut=mut, returncode=process.returncode, stderr=stderr.decode("utf-8"))
                else:
                    yield output.MutantOutput(mut=mut, returncode=process.returncode, stdout=stdout.decode("utf-8"))

    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    @staticmethod
    def _batched(iterable: Iterable):
        it = iter(iterable)
        while batch := tuple(itertools.islice(it, Runner.BATCH_SIZE)):
            yield batch

    @staticmethod
    def _random_filename() -> str:
        return os.path.join(Runner.DIR, str(uuid.uuid4()))

    @staticmethod
    def _create_file(filepath: str, source: str) -> None:
        with open(filepath, "w") as f:
            f.write(f"{source}\n{PROGRAM_SUFFIX}")

    @staticmethod
    def _delete_file(filepath: str) -> None:
        os.remove(filepath)

    @staticmethod
    def _run_program(filepath: str) -> subprocess.Popen:
        process = subprocess.Popen(["racket", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
