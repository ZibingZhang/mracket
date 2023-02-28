"""Code mutations."""
from __future__ import annotations

import dataclasses

from mracket.reader import syntax


@dataclasses.dataclass(frozen=True)
class Mutation:
    """A code mutation."""

    original: syntax.RacketASTNode
    replacement: syntax.RacketASTNode
    explanation: str
