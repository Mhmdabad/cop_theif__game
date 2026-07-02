"""Shared exceptions for domain services."""

from __future__ import annotations


class IllegalMoveError(ValueError):
    """Raised when a proposed action violates the game rules."""
