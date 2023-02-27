"""A procedure replacement mutator."""
from __future__ import annotations

from collections.abc import Generator, Mapping

from mracket import mutation
from mracket.mutation.generator import base
from mracket.reader import lexer, syntax


class ProcedureReplacement(base.BaseMutationGenerator):
    def __init__(self, replacements: Mapping[str, set[str]]) -> None:
        self.replacements = replacements

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
        for replacement in self.replacements[procedure_name]:
            new_node = syntax.RacketProcedureApplicationNode(
                lparen=lexer.DUMMY_TOKEN,
                rparen=lexer.DUMMY_TOKEN,
                expressions=[syntax.RacketNameNode(token=lexer.Token.from_source(lexer.TokenType.SYMBOL, replacement))]
                + node.expressions[1:],
            )
            explanation = (
                f"Replace procedure {procedure_name}"
                f" at line {procedure.token.lineno}, column {procedure.token.colno}"
                f" with {replacement}"
            )
            yield mutation.Mutation(
                original=node,
                replacement=new_node,
                explanation=explanation,
            )
