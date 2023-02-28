"""A procedure application replacement mutator."""
from __future__ import annotations

from collections.abc import Generator, Mapping

from mracket import mutation
from mracket.mutation.generator import base
from mracket.reader import lexer, parser, stringify, syntax


class ProcedureApplicationReplacement(base.BaseMutationGenerator):
    """Replaces procedure applications with expressions."""

    stringifier = stringify.Stringifier()

    def __init__(self, replacements: Mapping[str, list[str]]) -> None:
        lexer_ = lexer.Lexer()
        parser_ = parser.Parser()
        processed_replacements = {}
        for procedure_name in replacements:
            processed_sources = []
            for source in replacements[procedure_name]:
                processed_sources.append(parser_.parse_expression(lexer_.tokenize(source)))
            processed_replacements[procedure_name] = processed_sources
        self.replacements = processed_replacements

    def visit_procedure_application_node(
        self, node: syntax.RacketProcedureApplicationNode
    ) -> Generator[mutation.Mutation, None, None]:
        if len(node.expressions) == 0:
            return
        procedure = node.expressions[0]
        if procedure.token.type is not lexer.TokenType.SYMBOL:
            return
        procedure_name = procedure.token.source
        if procedure_name not in self.replacements:
            return

        for new_node in self.replacements[procedure_name]:
            explanation = (
                f"Replace procedure application of {procedure_name}"
                f" at line {procedure.token.lineno}, column {procedure.token.colno}"
                f" with {self.stringifier.visit(new_node)}"
            )
            yield mutation.Mutation(
                original=node,
                replacement=new_node,
                explanation=explanation,
            )
