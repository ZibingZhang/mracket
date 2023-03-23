"""The mutation testing runner."""
from __future__ import annotations

import os.path
import subprocess
import tempfile
import time
import uuid
from collections.abc import Generator, Iterator
from typing import cast

from mracket import mutation, reader
from mracket.mutation import applier, mutator
from mracket.reader import lexer, parser, syntax
from mracket.runner import logger, output, result

DRRACKET_PREFIX = ";; The first three lines of this file were inserted by DrRacket."
PROGRAM_SUFFIX = "(require test-engine/racket-tests)\n(test)"


class Runner:
    """Runs a set of mutations on a file."""

    MAX_PROCESS_COUNT = BATCH_SIZE = 100
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
            with open(self.filepath) as f:
                source = f.read()
            success.unmodified_result = self.run_unmodified(source)
            program = self.build_syntax_tree(source)
            success.mutations = self.generate_mutations(self.mutator, program)
            mutants = self.apply_mutations(program, success.mutations)
            success.mutant_results = self.run_mutants(mutants)
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
    def run_unmodified(source: str) -> output.ProgramOutput:
        """Run the original program.

        The source code is not being run but rather the stringified program. The reason
        is that we want the positions of the errors, if any exist, to be the same
        between the original and the mutants.

        :param source: Racket program source
        :return: Result of running the unmodified program
        """
        logger.LOGGER.debug("Running the unmodified program")
        program = TemporaryRacketProgram(source)
        while True:
            if program.finished:
                program.delete()
                break
            time.sleep(0.1)
        stdout, stderr = program.result
        if program.returncode != 0 or len(stderr) > 0:
            raise result.RunnerFailure(
                reason=result.RunnerFailure.Reason.NON_ZERO_UNMODIFIED_RETURNCODE,
                returncode=program.returncode,
                stderr=stderr.decode("utf-8"),
            )
        unmodified_result = output.ProgramOutput(stdout.decode("utf-8"))
        if unmodified_result.failed > 0:
            raise result.RunnerFailure(reason=result.RunnerFailure.Reason.UNMODIFIED_TEST_FAILURE)
        return unmodified_result

    @staticmethod
    def build_syntax_tree(source: str) -> syntax.RacketProgramNode:
        """Build an abstract syntax tree of the Racket program.

        :param source: Racket program source
        :return: A program abstract syntax tree
        """
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
        program: syntax.RacketProgramNode, mutations: list[mutation.Mutation]
    ) -> Generator[mutation.Mutant, None, None]:
        """Apply the mutations.

        :param program: A program to mutate
        :param mutations: List of mutations to apply to the program
        :return: Generator of mutation-mutant pairs
        """
        mutation_applier = applier.MutationApplier(program, mutations)
        mutants = mutation_applier.apply_mutations()
        return mutants

    @staticmethod
    def run_mutants(mutants: Iterator[mutation.Mutant]) -> Generator[output.MutantOutput, None, None]:
        """Run the mutants.

        :param mutants: An iterator of mutants pairs
        :return: Generator of mutant execution results
        """
        logger.LOGGER.debug("Running the mutated programs")
        process_count = 0
        running_programs = []
        while True:
            try:
                # TODO: fix output to be deterministic
                if process_count < Runner.MAX_PROCESS_COUNT:
                    mutant = next(mutants)
                    program = TemporaryRacketProgram(mutant.source, mutant.mutation)
                    running_programs.append(program)

                for program in running_programs:
                    try:
                        if program.finished:
                            running_programs.remove(program)
                            program.delete()
                            stdout, stderr = program.result
                            yield output.MutantOutput(
                                mut=cast(mutation.Mutation, program.mut),
                                returncode=program.returncode,
                                stdout=stdout.decode("utf-8"),
                                stderr=stderr.decode("utf-8"),
                            )
                    except result.RunnerFailure as e:
                        running_programs.remove(program)
                        program.delete()
                        yield output.MutantOutput(
                            mut=cast(mutation.Mutation, program.mut),
                            returncode=program.returncode,
                            stderr=e.reason.value,
                        )

                time.sleep(0.1)
            except StopIteration:
                break

        while len(running_programs) > 0:
            # duplicate of code above
            # TODO: consider if possible to abstract out duplication
            for program in running_programs:
                try:
                    if program.finished:
                        running_programs.remove(program)
                        program.delete()
                        stdout, stderr = program.result
                        yield output.MutantOutput(
                            mut=cast(mutation.Mutation, program.mut),
                            returncode=program.returncode,
                            stdout=stdout.decode("utf-8"),
                            stderr=stderr.decode("utf-8"),
                        )
                except result.RunnerFailure as e:
                    running_programs.remove(program)
                    program.delete()
                    yield output.MutantOutput(
                        mut=cast(mutation.Mutation, program.mut),
                        returncode=program.returncode,
                        stderr=e.reason.value,
                    )

            time.sleep(0.1)


class TemporaryRacketProgram:
    DIR = tempfile.gettempdir()
    TIMEOUT = 10

    def __init__(self, source: str, mut: mutation.Mutation | None = None) -> None:
        self.source = source
        self.mut = mut

        self.filepath = os.path.join(self.DIR, str(uuid.uuid4()))
        with open(self.filepath, "w") as f:
            f.write(f"{self.source}\n{PROGRAM_SUFFIX}")
        self.process = subprocess.Popen(["racket", self.filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.starttime = time.time()

    @property
    def returncode(self) -> int:
        return self.process.returncode

    @property
    def finished(self) -> bool:
        if time.time() - self.starttime > self.TIMEOUT:
            raise result.RunnerFailure(reason=result.RunnerFailure.Reason.TIMEOUT)
        return self.process.poll() is not None

    @property
    def result(self) -> tuple[bytes, bytes]:
        return self.process.communicate()

    # TODO: better name for method?
    def delete(self) -> None:
        self.process.kill()
        os.remove(self.filepath)
