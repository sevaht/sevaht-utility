"""Runtime inspection of type hints and unions.

Helpers for working with annotations at runtime: flattening unions
(:func:`iterate_types`), checking a value against an expected runtime type
(:func:`verify_type`), and extracting a callable's argument types
(:func:`get_callable_argument_hints`). These back the type-aware conversion in
:func:`sevaht_utility.parsing.csv_load`.
"""

from __future__ import annotations

from collections import deque
from dataclasses import InitVar
from inspect import signature
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


T = TypeVar("T")


class InvalidTypeError(TypeError):
    """Raised when a value's type does not match the expected type."""

    def __init__(
        self, value: object, *, expected_type: type[T] | UnionType
    ) -> None:
        super().__init__(
            f"Expected: {expected_type}, "
            f"Actual: {type(value)}, "
            f"Value: {value}"
        )
        self.expected_type = expected_type
        self.value = value


class ParameterizedTypeNotSupportedError(TypeError):
    """Raised when verify_type receives a parameterized generic."""

    def __init__(self, expected_type: object) -> None:
        super().__init__(
            "Parameterized generics are not supported by verify_type: "
            f"{expected_type}. Use an unparameterized runtime type instead."
        )
        self.expected_type = expected_type


def iterate_types(*source_types: type | UnionType) -> Iterator[type]:
    """Yield the distinct member types of one or more (possibly union) types.

    Unions are flattened recursively (both ``X | Y`` and ``typing.Union``), and
    duplicates are skipped, preserving first-seen order.

    Args:
        *source_types: Types or unions to flatten.

    Yields:
        Each distinct constituent type, in order.

    Example:
        >>> list(iterate_types(int | str))
        [<class 'int'>, <class 'str'>]
    """
    stack = deque(source_types)
    seen: set[type] = set()
    while stack:
        current = stack.popleft()
        if isinstance(current, UnionType) or get_origin(current) is Union:
            stack.extendleft(reversed(get_args(current)))
        elif current not in seen:
            seen.add(current)
            yield current


def verify_type[T](expected_type: type | UnionType, value: T) -> T:
    """Return ``value`` if it matches ``expected_type``, else raise.

    ``expected_type`` may be a single type or a union of types; ``value``
    matches if it is an instance of any member (``Any`` and ``object`` always
    match). Parameterized generics such as ``list[int]`` cannot be checked at
    runtime and are rejected.

    Args:
        expected_type: The required type or union of types.
        value: The value to check.

    Returns:
        ``value`` unchanged, for convenient inline use.

    Raises:
        InvalidTypeError: ``value`` matches no member of ``expected_type``.
        ParameterizedTypeNotSupportedError: ``expected_type`` contains a
            parameterized generic.
    """
    matched = False
    for candidate_type in iterate_types(expected_type):
        if get_origin(candidate_type) is not None:
            raise ParameterizedTypeNotSupportedError(candidate_type)
        if candidate_type in (Any, object) or isinstance(
            value, candidate_type
        ):
            matched = True
    if matched:
        return value
    raise InvalidTypeError(value, expected_type=expected_type)


def get_callable_argument_hints(
    function: Callable[..., Any],
) -> dict[str, type]:
    """Return a callable's parameters mapped to their annotated types.

    The ``return`` annotation is excluded, dataclass ``InitVar`` wrappers are
    unwrapped to their inner type, and unannotated parameters map to ``Any``.

    Args:
        function: Any callable (function, dataclass type, etc.).

    Returns:
        A mapping of parameter name to its type.
    """
    type_hints = {
        member: (
            member_type
            if not isinstance(member_type, InitVar)
            else member_type.type
        )
        for member, member_type in get_type_hints(function).items()
    }
    return {
        member: type_hints.get(member, Any)
        for member in signature(function).parameters
        if member != "return"
    }
