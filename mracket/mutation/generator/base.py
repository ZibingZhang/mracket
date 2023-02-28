"""The mutation generator base class."""

from __future__ import annotations

from collections.abc import Generator

from mracket import mutation
from mracket.reader import syntax


class BaseMutationGenerator(syntax.RacketASTVisitor):
    def visit_program_node(self, node: syntax.RacketProgramNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_reader_directive_node(
        self, node: syntax.RacketReaderDirectiveNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_name_definition_node(
        self, node: syntax.RacketNameDefinitionNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_structure_definition_node(
        self, node: syntax.RacketStructureDefinitionNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_literal_node(self, node: syntax.RacketLiteralNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_name_node(self, node: syntax.RacketNameNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_cond_node(self, node: syntax.RacketCondNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_local_node(self, node: syntax.RacketLocalNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_procedure_application_node(
        self, node: syntax.RacketProcedureApplicationNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_check_expect_node(self, node: syntax.RacketCheckExpectNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_library_require_node(
        self, node: syntax.RacketLibraryRequireNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield
