"""A parser for Racket programs."""
from __future__ import annotations

import re
from typing import Literal

from mracket.reader import errors, lexer, syntax

MATCHING_PARENS = {
    "(": ")",
    "[": "]",
    "{": "}",
}
LITERAL_TOKEN_TYPES = {
    lexer.TokenType.BOOLEAN,
    lexer.TokenType.CHARACTER,
    lexer.TokenType.NUMBER,
    lexer.TokenType.STRING,
}

DEFINITION = re.compile(r"define(-struct)?")
TEST_CASE = re.compile(r"check-(expect|random|within|member-of|range|satisfied|error)")
LIBRARY_REQUIRE = re.compile(r"require")


class Parser:
    """A parser for Racket programs."""

    def __init__(self, tokens: list[lexer.Token]) -> None:
        self._tokens = self._token_stream = tokens
        self._current_token = lexer.EOF_TOKEN

    def parse(self) -> syntax.RacketProgramNode:
        """Convert the tokens into an AST."""

        # reset stream
        self._token_stream = self._tokens.copy()
        self._current_token = self._token_stream.pop(0)

        statements = []
        reader_directive = None
        while self._current_token.type is not lexer.TokenType.EOF:
            if self._current_token.type is lexer.TokenType.READER_DIRECTIVE:
                reader_directive = self._reader_directive()
            else:
                statements.append(self._statement())

        if reader_directive is None:
            raise errors.ExpectedReaderDirective(self._tokens[-1])

        return syntax.RacketProgramNode(token=self._tokens[0], reader_directive=reader_directive, statements=statements)

    def _reader_directive(self) -> syntax.RacketReaderDirectiveNode:
        node = syntax.RacketReaderDirectiveNode(token=self._current_token)
        self._eat(lexer.TokenType.READER_DIRECTIVE)
        return node

    def _statement(self) -> syntax.RacketStatementNode:
        if self._current_token.type is lexer.TokenType.EOF:
            raise errors.UnexpectedEOFTokenError(self._current_token)
        if self._current_token.type is lexer.TokenType.RPAREN:
            raise errors.UnexpectedRightParenthesisError(self._current_token)

        if definition_type := self._is_defintion():
            return self._definition(definition_type)
        if test_case_type := self._is_test_case():
            return self._test_case(test_case_type)
        if self._is_library_require():
            return self._library_require()
        return self._expression()

    def _definition(self, definition_type: str) -> syntax.RacketDefinitionNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        if definition_type == "define":
            if self._current_token.type is lexer.TokenType.LPAREN:
                # desugar (define (name variable ...) expr) to (define name (lambda (variable ...) expr)
                self._eat(lexer.TokenType.LPAREN)
                name = self._name()
                variables = []
                while self._current_token.type is not lexer.TokenType.RPAREN:
                    variables.append(self._name())
                self._eat(lexer.TokenType.RPAREN)
                expression = self._expression()
                rparen = self._eat(lexer.TokenType.RPAREN)
                return syntax.RacketConstantDefinitionNode(
                    lparen=lparen,
                    rparen=rparen,
                    name=name,
                    expression=syntax.RacketLambdaNode(
                        lparen=lexer.DUMMY_LPAREN_TOKEN,
                        rparen=lexer.DUMMY_RPAREN_TOKEN,
                        variables=variables,
                        expression=expression,
                    ),
                )
            elif self._current_token.type is lexer.TokenType.SYMBOL:
                name = self._name()
                expression = self._expression()
                rparen = self._eat(lexer.TokenType.RPAREN)
                return syntax.RacketConstantDefinitionNode(
                    lparen=lparen, rparen=rparen, name=name, expression=expression
                )
            else:
                raise errors.IllegalStateError()
        elif definition_type == "define-struct":
            name = self._name()
            self._eat(lexer.TokenType.LPAREN)
            fields = []
            while self._current_token.type is not lexer.TokenType.RPAREN:
                fields.append(self._name())
            self._eat(lexer.TokenType.RPAREN)
            rparen = self._eat(lexer.TokenType.RPAREN)
            return syntax.RacketStructureDefinitionNode(lparen=lparen, rparen=rparen, name=name, fields=fields)
        else:
            raise errors.IllegalStateError()

    def _expression(self) -> syntax.RacketExpressionNode:
        token_type = self._current_token.type
        if token_type in LITERAL_TOKEN_TYPES:
            return syntax.RacketLiteralNode(token=self._eat(token_type))
        elif token_type is lexer.TokenType.SYMBOL:
            return self._name()

        if token_type is lexer.TokenType.EOF:
            raise ValueError

        # TODO: handle other cases, such as quotes

        if token_type is not lexer.TokenType.LPAREN:
            raise errors.IllegalStateError(str(self._current_token))

        lparen = self._eat(lexer.TokenType.LPAREN)
        expressions = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            expressions.append(self._expression())
        rparen = self._eat(lexer.TokenType.RPAREN)
        if rparen.source != MATCHING_PARENS[lparen.source]:
            raise errors.MismatchedParenthesesError(lparen, rparen)
        return syntax.RacketProcedureApplicationNode(lparen=lparen, rparen=rparen, expressions=expressions)

    def _name(self) -> syntax.RacketNameNode:
        return syntax.RacketNameNode(token=self._eat(lexer.TokenType.SYMBOL))

    def _test_case(self, test_case_type: str) -> syntax.RacketTestCaseNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        if test_case_type == "check-expect":
            actual = self._expression()
            expected = self._expression()
            rparen = self._eat(lexer.TokenType.RPAREN)
            return syntax.RacketCheckExpectNode(lparen=lparen, rparen=rparen, actual=actual, expected=expected)
        else:
            # TODO: parse other check forms
            raise errors.IllegalStateError()

    def _library_require(self) -> syntax.RacketLibraryRequireNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        library = self._name()
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketLibraryRequireNode(lparen=lparen, rparen=rparen, library=library)

    def _eat(self, token_type: lexer.TokenType) -> lexer.Token:
        if self._current_token.type != token_type:
            raise errors.ParserError(self._current_token)

        previous_token = self._current_token
        self._current_token = self._token_stream.pop(0)
        return previous_token

    def _is_defintion(self) -> str | Literal[False]:
        return self._is_special_statement(DEFINITION)

    def _is_test_case(self) -> str | Literal[False]:
        return self._is_special_statement(TEST_CASE)

    def _is_library_require(self) -> str | Literal[False]:
        return self._is_special_statement(LIBRARY_REQUIRE)

    def _is_special_statement(self, pattern: re.Pattern) -> str | Literal[False]:
        if not (self._current_token.type is lexer.TokenType.LPAREN and len(self._token_stream) > 0):
            return False
        next_token = self._token_stream[0]
        if next_token.type is lexer.TokenType.SYMBOL and re.match(pattern, next_token.source):
            return next_token.source
        return False
