"""Integration tests for mracket.reader."""
from __future__ import annotations

import subprocess
import tempfile

import pytest

from mracket import test
from mracket.reader.lexer import Lexer
from mracket.reader.parser import Parser
from mracket.reader.stringify import Stringifier


def test_read_program_succeeds() -> None:
    for source in test.inputs.read_contents():
        tokens = Lexer().tokenize(source)
        Parser().parse(tokens)


@pytest.mark.parametrize(
    "source",
    [
        "1",
        "(define x 1)",
        "(define-struct posn (x y))",
        "(cond (#t 1) (else 2))",
        "(lambda (x) 1)",
    ],
)
def test_stringify(source: str) -> None:
    source = f"#lang racket\n{source}"
    program = Parser().parse(Lexer().tokenize(source))
    assert Stringifier().visit(program) == source


@pytest.mark.parametrize(
    "source,desugared_source",
    [
        ["(define (x) 1)", "(define x (lambda () 1))"],
        ["'a", "(quote a)"],
        ["`,a", "(quasiquote (unquote a))"],
        ["`(,@'(1 2 3))", "(quasiquote ((unquote-splicing (quote (1 2 3)))))"],
        ["(if #t 1 2)", "(cond (#t 1) (else 2))"],
    ],
)
def test_desugar(source: str, desugared_source: str) -> None:
    program = Parser().parse(Lexer().tokenize(f"#lang racket\n{source}"))
    assert Stringifier().visit(program) == f"#lang racket\n{desugared_source}"


def test_stringify_idempotent() -> None:
    lexer = Lexer()
    parser = Parser()
    for source in test.inputs.read_contents():
        tokens_0 = lexer.tokenize(source)
        program_0 = parser.parse(tokens_0)
        stringified_program_0 = Stringifier().visit(program_0)

        tokens_1 = lexer.tokenize(stringified_program_0)
        program_1 = parser.parse(tokens_1)
        stringified_program_1 = Stringifier().visit(program_1)

        assert stringified_program_0 == stringified_program_1


@pytest.mark.slow
def test_racket_output_unchanged() -> None:
    for file_name in test.inputs.file_paths(r"^(?!test-case).+"):
        original_process = subprocess.Popen(["racket", file_name], stdout=subprocess.PIPE)

        with open(file_name) as f:
            source = f.read()
        tokens = Lexer().tokenize(source)
        program = Parser().parse(tokens)
        stringified_program = Stringifier().visit(program)

        with tempfile.NamedTemporaryFile(mode="w") as tf:
            tf.write(stringified_program)
            tf.seek(0)

            transformed_process = subprocess.Popen(["racket", tf.name], stdout=subprocess.PIPE)

            (original_output, original_error) = original_process.communicate()
            (transformed_output, transformed_error) = transformed_process.communicate()

        assert original_process.returncode == transformed_process.returncode
        if original_error is None:
            assert original_output == transformed_output
