"""Identifier case detection and conversion.

This module breaks identifiers into their component words regardless of the
casing convention used (``snake_case``, ``kebab-case``, ``camelCase``,
``PascalCase``, or whitespace separated) and rebuilds them in a chosen
:class:`NameStyle`.

The splitter recognizes a single *medial acronym* using a pure heuristic, so
``"HTTPServer"`` becomes ``["http", "server"]`` and ``"getHTTPResponseCode"``
becomes ``["get", "http", "response", "code"]``. It deliberately does **not**
split *consecutive* acronyms (``"XMLHTTPRequest"`` stays ``"xmlhttp"`` +
``"request"``), since separating them unambiguously would require a dictionary.

Example:
    >>> from sevaht_utility.naming import convert_name, NameStyle
    >>> convert_name("getHTTPResponseCode", style=NameStyle.SNAKE_CASE)
    'get_http_response_code'
    >>> convert_name("get_http_response_code", style=NameStyle.PASCAL_CASE)
    'GetHttpResponseCode'
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto, unique
from itertools import chain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class NameStyleConfig:
    """How a list of lowercase words is recombined into a single name.

    Attributes:
        separator: String placed between words (``"_"``, ``"-"``, or ``""``).
        capitalize_first: Whether the first word is capitalized.
        capitalize_rest: Whether words after the first are capitalized.
    """

    separator: str
    capitalize_first: bool
    capitalize_rest: bool


@unique
class NameStyle(Enum):
    """A supported identifier casing convention.

    Each member carries the :class:`NameStyleConfig` describing how to render a
    name in that style, available via :attr:`config`.

    Attributes:
        SNAKE_CASE: ``words_joined_like_this``.
        KEBAB_CASE: ``words-joined-like-this``.
        CAMEL_CASE: ``wordsJoinedLikeThis``.
        PASCAL_CASE: ``WordsJoinedLikeThis``.
    """

    _config: NameStyleConfig

    SNAKE_CASE = auto(), NameStyleConfig("_", False, False)
    KEBAB_CASE = auto(), NameStyleConfig("-", False, False)
    CAMEL_CASE = auto(), NameStyleConfig("", False, True)
    PASCAL_CASE = auto(), NameStyleConfig("", True, True)

    def __new__(cls, value: int, config: NameStyleConfig) -> NameStyle:
        obj = object.__new__(cls)
        obj._value_ = value
        obj._config = config
        return obj

    @property
    def config(self) -> NameStyleConfig:
        """The :class:`NameStyleConfig` describing this style."""
        return self._config


def split_into_words(name: str) -> list[str]:
    """Split an identifier into its lowercase component words.

    Word boundaries are detected from delimiters (``-``, ``_``, whitespace) and
    from case transitions, so a single function handles every common style.
    The returned words are always lowercase.

    Acronym handling is heuristic and intentionally limited:

    * A *medial* acronym is split from the word that follows it, e.g.
      ``"HTTPServer"`` -> ``["http", "server"]`` and ``"userIDName"`` ->
      ``["user", "id", "name"]``.
    * *Consecutive* acronyms are left merged, e.g. ``"XMLHTTPRequest"`` ->
      ``["xmlhttp", "request"]``. Splitting them apart would require a known
      acronym dictionary; when a specific identifier matters, map it
      explicitly (see :func:`sevaht_utility.parsing.csv_load` and
      :class:`sevaht_utility.parsing.DataMapping`).

    Args:
        name: The identifier to split. May use any supported style; empty or
            delimiter-only input yields an empty list.

    Returns:
        The component words, lowercased, in order.

    Example:
        >>> split_into_words("someSampleName")
        ['some', 'sample', 'name']
        >>> split_into_words("some-sample-name")
        ['some', 'sample', 'name']
        >>> split_into_words("getHTTPResponseCode")
        ['get', 'http', 'response', 'code']
    """
    words: list[str] = []
    word = ""  # the current word, built up character by character
    # Upper-ness of the previous two characters, oldest first. Seeded False (no
    # preceding characters); each step pushes the current value and the FIFO
    # drops the oldest, so `all(recent_upper)` means we are in an acronym run.
    recent_upper = deque([False, False], maxlen=2)
    for current in chain(name, "-"):
        upper = current.isupper()
        if current in ("-", "_") or current.isspace():
            if word:
                words.append(word.lower())
                word = ""
        elif upper and not recent_upper[-1]:
            if word:  # lower-to-upper: a new word starts at `current`
                words.append(word.lower())
            word = current
        elif current.islower() and all(recent_upper):
            # An acronym run flowing into a lowercase word: its final capital
            # actually begins that word (e.g. "HTTPServer" -> http, server).
            # Close the word without that capital and start the next with it.
            words.append(word[:-1].lower())
            word = word[-1] + current
        else:
            word += current
        recent_upper.append(upper)
    return words


def join_words(words: Sequence[str], style: NameStyle) -> str:
    """Join words into a single identifier rendered in ``style``.

    Words are lowercased and empty entries dropped before they are capitalized
    and joined according to ``style``.

    Args:
        words: The component words to join.
        style: The target :class:`NameStyle`.

    Returns:
        The joined identifier, or ``""`` if no non-empty words were given.

    Example:
        >>> join_words(["http", "server"], NameStyle.PASCAL_CASE)
        'HttpServer'
        >>> join_words(["http", "server"], NameStyle.SNAKE_CASE)
        'http_server'
    """
    normalized_words = [word.lower() for word in words if word]
    if not normalized_words:
        return ""
    cfg = style.config
    transformed = [
        (
            w.capitalize()
            if (i == 0 and cfg.capitalize_first)
            or (i > 0 and cfg.capitalize_rest)
            else w
        )
        for i, w in enumerate(normalized_words)
    ]
    return cfg.separator.join(transformed)


def convert_name(name: str, *, style: NameStyle) -> str:
    """Convert a name from any supported style into ``style``.

    This is :func:`split_into_words` followed by :func:`join_words`. Because
    splitting normalizes to lowercase words, conversion is idempotent: applying
    it twice yields the same result as applying it once.

    Args:
        name: The identifier to convert. May use any supported style.
        style: The target :class:`NameStyle`.

    Returns:
        ``name`` rendered in ``style``.

    Example:
        >>> convert_name("someSampleName", style=NameStyle.SNAKE_CASE)
        'some_sample_name'
        >>> convert_name("user-id", style=NameStyle.PASCAL_CASE)
        'UserId'
    """
    words = split_into_words(name)
    return join_words(words, style)
