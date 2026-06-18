from __future__ import annotations

import logging
from pathlib import Path

import pytest

from sevaht_utility.log_utility import LogFileOptions, log_exceptions


def test_log_file_options_are_keyword_only_after_path() -> None:
    # Everything after `path` is keyword-only; passing positionally must fail.
    with pytest.raises(TypeError):
        LogFileOptions(Path("x"), 512, 1)  # type: ignore[misc]
    options = LogFileOptions(Path("x"), max_kb=512, backup_count=1)
    assert options.max_kb == 512
    assert options.backup_count == 1


def test_log_exceptions_logs_and_reraises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    test_logger = logging.getLogger("tests.log_exceptions")

    @log_exceptions(logger=test_logger)
    def raises() -> None:
        message = "boom"
        raise ValueError(message)

    with (
        caplog.at_level(logging.ERROR, logger=test_logger.name),
        pytest.raises(ValueError, match="boom"),
    ):
        raises()

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "ERROR"
    assert record.message == "uncaught exception"
    assert getattr(record, "file_only", False) is True


def test_log_exceptions_returns_normal_result() -> None:
    @log_exceptions()
    def returns_value(value: int) -> int:
        return value + 1

    assert returns_value(4) == 5
