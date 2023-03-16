"""A code mutation applier."""
from __future__ import annotations

import itertools
from collections.abc import Generator
from typing import cast

from mracket import mutation
from mracket.reader import stringify, syntax


class MutationApplier(syntax.RacketASTVisitor):
    """Applies mutations to the program.

    For each node of the program, if there exists a mutation where that node is
    replaced, it replaces the node and yields a stringified version of the entire
    program with the updated node. The node is then swapped back.
    """

    stringifier: stringify.Stringifier = stringify.Stringifier()

    def __init__(self, program: syntax.RacketProgramNode, mutations: list[mutation.Mutation]) -> None:
        self.program = program
        self.mutations = mutations

    def apply_mutations(self) -> Generator[mutation.Mutant, None, None]:
        yield from self.visit(self.program)

    def visit_program_node(self, node: syntax.RacketProgramNode) -> Generator[mutation.Mutant, None, None]:
        reader_directive = node.reader_directive
        for mut in self._get_mutations(node.reader_directive):
            node.reader_directive = cast(syntax.RacketReaderDirectiveNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.reader_directive = reader_directive

        statements = node.statements.copy()
        for i, statement in enumerate(node.statements):
            for mut in self._get_mutations(statement):
                node.statements[i] = cast(syntax.RacketStatementNode, mut.replacement)
                yield mutation.Mutant(mut, self.stringifier.visit(self.program))
            node.statements = statements

        for child_node in [node.reader_directive, *node.statements]:
            yield from self.visit(child_node)

    def visit_reader_directive_node(
        self, node: syntax.RacketReaderDirectiveNode
    ) -> Generator[mutation.Mutant, None, None]:
        return
        yield

    def visit_name_definition_node(
        self, node: syntax.RacketNameDefinitionNode
    ) -> Generator[mutation.Mutant, None, None]:
        name = node.name
        for mut in self._get_mutations(node.name):
            node.name = cast(syntax.RacketNameNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.name = name

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.expression = expression

        for child_node in [node.name, node.expression]:
            yield from self.visit(child_node)

    def visit_structure_definition_node(
        self, node: syntax.RacketStructureDefinitionNode
    ) -> Generator[mutation.Mutant, None, None]:
        name = node.name
        for mut in self._get_mutations(node.name):
            node.name = cast(syntax.RacketNameNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.name = name

        fields = node.fields.copy()
        for i, field in enumerate(node.fields):
            for mut in self._get_mutations(field):
                node.fields[i] = cast(syntax.RacketNameNode, mut.replacement)
                yield mutation.Mutant(mut, self.stringifier.visit(self.program))
            node.fields = fields

        for child_node in [node.name, *node.fields]:
            yield from self.visit(child_node)

    def visit_literal_node(self, node: syntax.RacketLiteralNode) -> Generator[mutation.Mutant, None, None]:
        return
        yield

    def visit_name_node(self, node: syntax.RacketNameNode) -> Generator[mutation.Mutant, None, None]:
        return
        yield

    def visit_cond_node(self, node: syntax.RacketCondNode) -> Generator[mutation.Mutant, None, None]:
        branches = node.branches.copy()
        for i, (condition, expression) in enumerate(node.branches):
            for mut in self._get_mutations(condition):
                node.branches[i] = (cast(syntax.RacketExpressionNode, mut.replacement), node.branches[i][1])
            node.branches = branches

            for mut in self._get_mutations(expression):
                node.branches[i] = (node.branches[i][0], cast(syntax.RacketExpressionNode, mut.replacement))
            node.branches = branches

        for child_node in itertools.chain.from_iterable(node.branches):
            yield from self.visit(child_node)

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> Generator[mutation.Mutant, None, None]:
        variables = node.variables.copy()
        for i, variable in enumerate(node.variables):
            for mut in self._get_mutations(variable):
                node.variables[i] = cast(syntax.RacketNameNode, mut.replacement)
            node.variables = variables

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.expression = expression

        for child_node in [*node.variables, node.expression]:
            yield from self.visit(child_node)

    def visit_let_node(self, node: syntax.RacketLetNode) -> Generator[mutation.Mutant, None, None]:
        local_definitions = node.local_definitions.copy()
        for i, (name, expression) in enumerate(node.local_definitions):
            for mut in self._get_mutations(name):
                node.local_definitions[i] = (cast(syntax.RacketNameNode, mut.replacement), node.local_definitions[i][1])
            node.local_definitions = local_definitions

            for mut in self._get_mutations(expression):
                node.local_definitions[i] = (
                    node.local_definitions[i][0],
                    cast(syntax.RacketExpressionNode, mut.replacement),
                )
            node.local_definitions = local_definitions

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.expression = expression

        for child_node in (*itertools.chain.from_iterable(node.local_definitions), node.expression):
            yield from self.visit(child_node)

    def visit_local_node(self, node: syntax.RacketLocalNode) -> Generator[mutation.Mutant, None, None]:
        definitions = node.definitions.copy()
        for i, definition in enumerate(node.definitions):
            for mut in self._get_mutations(definition):
                node.definitions[i] = cast(syntax.RacketDefinitionNode, mut.replacement)
            node.definitions = definitions

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.expression = expression

        for child_node in [*node.definitions, node.expression]:
            yield from self.visit(child_node)

    def visit_procedure_application_node(
        self, node: syntax.RacketProcedureApplicationNode
    ) -> Generator[mutation.Mutant, None, None]:
        expressions = node.expressions.copy()
        for i, expression in enumerate(node.expressions):
            for mut in self._get_mutations(expression):
                node.expressions[i] = cast(syntax.RacketExpressionNode, mut.replacement)
                yield mutation.Mutant(mut, self.stringifier.visit(self.program))
            node.expressions = expressions

        for child_node in node.expressions:
            yield from self.visit(child_node)

    def visit_test_case_node(self, node: syntax.RacketTestCaseNode) -> Generator[mutation.Mutant, None, None]:
        expressions = node.expressions.copy()
        for i, expression in enumerate(node.expressions):
            for mut in self._get_mutations(expression):
                node.expressions[i] = cast(syntax.RacketExpressionNode, mut.replacement)
                yield mutation.Mutant(mut, self.stringifier.visit(self.program))
            node.expressions = expressions

        for child_node in node.expressions:
            yield from self.visit(child_node)

    def visit_library_require_node(
        self, node: syntax.RacketLibraryRequireNode
    ) -> Generator[mutation.Mutant, None, None]:
        library = node.library
        for mut in self._get_mutations(node.library):
            node.library = cast(syntax.RacketNameNode, mut.replacement)
            yield mutation.Mutant(mut, self.stringifier.visit(self.program))
        node.library = library

        yield from self.visit(library)

    def _get_mutations(self, node: syntax.RacketASTNode) -> Generator[mutation.Mutation, None, None]:
        for mut in self.mutations:
            if node is mut.original:
                yield mut
