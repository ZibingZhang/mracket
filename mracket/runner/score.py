"""Mutation score."""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class MutationScore:
    """A mutation score."""

    total: int
    killed: int
    execution_error: int
