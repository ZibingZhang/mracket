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

    def __init__(self) -> None:
        self._token_stream: list[lexer.Token] = []
        self._current_token = lexer.EOF_TOKEN
        self._lparen_stack: list[lexer.Token] = []

    def parse(self, tokens: list[lexer.Token]) -> syntax.RacketProgramNode:
        """Convert the tokens into an abstract syntax tree."""
        self._token_stream = tokens.copy()
        self._current_token = self._token_stream.pop(0)
        self._lparen_stack = []

        statements = []
        reader_directive = None
        while self._current_token.type is not lexer.TokenType.EOF:
            if self._current_token.type is lexer.TokenType.READER_DIRECTIVE:
                reader_directive = self._reader_directive()
            else:
                statements.append(self._statement())

        if reader_directive is None:
            raise errors.ExpectedReaderDirective(lexer.EOF_TOKEN)

        return syntax.RacketProgramNode(token=tokens[0], reader_directive=reader_directive, statements=statements)

    def _reader_directive(self) -> syntax.RacketReaderDirectiveNode:
        node = syntax.RacketReaderDirectiveNode(token=self._current_token)
        self._eat(lexer.TokenType.READER_DIRECTIVE)
        return node

    def _statement(self) -> syntax.RacketStatementNode:
        if self._current_token.type is lexer.TokenType.EOF:
            raise errors.UnexpectedEOFTokenError(self._current_token)
        if self._current_token.type is lexer.TokenType.RPAREN:
            raise errors.UnexpectedRightParenthesisError(self._current_token)

        if self._is_defintion_statement():
            return self._definition()
        if self._is_test_case_statement():
            return self._test_case()
        if self._is_library_require_statement():
            return self._library_require()
        return self._expression()

    def _definition(self) -> syntax.RacketDefinitionNode:
        if self._is_name_definition():
            return self._name_definition()
        elif self._is_structure_definition():
            return self._structure_definition()
        else:
            raise errors.IllegalStateError()

    def _name_definition(self) -> syntax.RacketNameDefinitionNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        if self._current_token.type is lexer.TokenType.LPAREN:
            return self._desugar_function_definition(lparen)
        elif self._current_token.type is lexer.TokenType.SYMBOL:
            name = self._name()
            expression = self._expression()
            rparen = self._eat(lexer.TokenType.RPAREN)
            return syntax.RacketNameDefinitionNode(lparen=lparen, rparen=rparen, name=name, expression=expression)
        else:
            raise errors.IllegalStateError()

    def _desugar_function_definition(self, lparen: lexer.Token) -> syntax.RacketNameDefinitionNode:
        # desugar (define (name variable ...) expr) to (define name (lambda (variable ...) expr)
        self._eat(lexer.TokenType.LPAREN)
        name = self._name()
        variables = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            variables.append(self._name())
        self._eat(lexer.TokenType.RPAREN)
        expression = self._expression()
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketNameDefinitionNode(
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

    def _structure_definition(self) -> syntax.RacketStructureDefinitionNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        name = self._name()
        self._eat(lexer.TokenType.LPAREN)
        fields = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            fields.append(self._name())
        self._eat(lexer.TokenType.RPAREN)
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketStructureDefinitionNode(lparen=lparen, rparen=rparen, name=name, fields=fields)

    def _expression(self) -> syntax.RacketExpressionNode:
        token_type = self._current_token.type
        if token_type in LITERAL_TOKEN_TYPES:
            return syntax.RacketLiteralNode(token=self._eat(token_type))
        elif token_type is lexer.TokenType.SYMBOL:
            return self._name()

        # TODO: handle other cases, such as quotes

        if token_type is not lexer.TokenType.LPAREN:
            raise errors.IllegalStateError(str(self._current_token))

        if self._is_cond_expression():
            return self._cond()
        if self._is_lambda_expression():
            return self._lambda()
        if self._is_let_expression():
            return self._let()
        if self._is_local_expression():
            return self._local()

        return self._procedure_application()

    def _name(self) -> syntax.RacketNameNode:
        return syntax.RacketNameNode(token=self._eat(lexer.TokenType.SYMBOL))

    def _cond(self) -> syntax.RacketCondNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        branches = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            self._eat(lexer.TokenType.LPAREN)
            branch = (self._expression(), self._expression())
            self._eat(lexer.TokenType.RPAREN)
            branches.append(branch)
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketCondNode(lparen=lparen, rparen=rparen, branches=branches)

    def _lambda(self) -> syntax.RacketLambdaNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        self._eat(lexer.TokenType.LPAREN)
        variables = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            variables.append(self._name())
        self._eat(lexer.TokenType.RPAREN)
        expression = self._expression()
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketLambdaNode(lparen=lparen, rparen=rparen, variables=variables, expression=expression)

    def _let(self) -> syntax.RacketLetNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        name = self._eat(lexer.TokenType.SYMBOL)
        self._eat(lexer.TokenType.LPAREN)
        local_definitions = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            self._eat(lexer.TokenType.LPAREN)
            local_definition = (self._name(), self._expression())
            self._eat(lexer.TokenType.RPAREN)
            local_definitions.append(local_definition)
        self._eat(lexer.TokenType.RPAREN)
        expression = self._expression()
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketLetNode(
            lparen=lparen,
            rparen=rparen,
            typ=syntax.RacketLetNode.Type(name.source),
            local_definitions=local_definitions,
            expression=expression,
        )

    def _local(self) -> syntax.RacketLocalNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        self._eat(lexer.TokenType.LPAREN)
        definitions = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            definitions.append(self._definition())
        self._eat(lexer.TokenType.RPAREN)
        expression = self._expression()
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketLocalNode(lparen=lparen, rparen=rparen, definitions=definitions, expression=expression)

    def _procedure_application(self) -> syntax.RacketProcedureApplicationNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        expressions = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            expressions.append(self._expression())
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketProcedureApplicationNode(lparen=lparen, rparen=rparen, expressions=expressions)

    def _test_case(self) -> syntax.RacketTestCaseNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        name = self._eat(lexer.TokenType.SYMBOL)
        expressions = []
        while self._current_token.type is not lexer.TokenType.RPAREN:
            expressions.append(self._expression())
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketTestCaseNode(
            lparen=lparen, rparen=rparen, typ=syntax.RacketTestCaseNode.Type(name.source), expressions=expressions
        )

    def _library_require(self) -> syntax.RacketLibraryRequireNode:
        lparen = self._eat(lexer.TokenType.LPAREN)
        self._eat(lexer.TokenType.SYMBOL)
        library = self._name()
        rparen = self._eat(lexer.TokenType.RPAREN)
        return syntax.RacketLibraryRequireNode(lparen=lparen, rparen=rparen, library=library)

    def _eat(self, token_type: lexer.TokenType) -> lexer.Token:
        if self._current_token.type != token_type:
            raise errors.ParserError(self._current_token)

        if token_type is lexer.TokenType.LPAREN:
            self._lparen_stack.append(self._current_token)
        elif token_type is lexer.TokenType.RPAREN:
            lparen = self._lparen_stack.pop()
            if self._current_token.source != MATCHING_PARENS[lparen.source]:
                raise errors.MismatchedParenthesesError(lparen, self._current_token)

        previous_token = self._current_token
        self._current_token = self._token_stream.pop(0)
        return previous_token

    def _is_defintion_statement(self) -> str | Literal[False]:
        return self._is_special_statement(DEFINITION)

    def _is_test_case_statement(self) -> str | Literal[False]:
        return self._is_special_statement(TEST_CASE)

    def _is_library_require_statement(self) -> str | Literal[False]:
        return self._is_special_statement(LIBRARY_REQUIRE)

    def _is_special_statement(self, pattern: re.Pattern) -> str | Literal[False]:
        if not (self._current_token.type is lexer.TokenType.LPAREN and len(self._token_stream) > 0):
            return False
        next_token = self._token_stream[0]
        if next_token.type is lexer.TokenType.SYMBOL and re.match(pattern, next_token.source):
            return next_token.source
        return False

    def _is_name_definition(self) -> bool:
        return self._token_stream[0].source == "define"

    def _is_structure_definition(self) -> bool:
        return self._token_stream[0].source == "define-struct"

    def _is_cond_expression(self) -> bool:
        return self._is_special_expression("cond")

    def _is_lambda_expression(self) -> bool:
        return self._is_special_expression("\u03bb", "lambda")

    def _is_let_expression(self) -> bool:
        return self._is_special_expression("letrec", "let", "let*")

    def _is_local_expression(self) -> bool:
        return self._is_special_expression("local")

    def _is_special_expression(self, *names: str) -> bool:
        next_token = self._token_stream[0]
        return next_token.type is lexer.TokenType.SYMBOL and next_token.source in names
