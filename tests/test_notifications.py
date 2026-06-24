from __future__ import annotations

from typing import TYPE_CHECKING

from sevaht_utility.notifications import notify

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest


class _Result:
    returncode = 0


def test_notify_send_used_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Sequence[str]] = []

    def fake_which(name: str) -> str | None:
        return "/usr/bin/notify-send" if name == "notify-send" else None

    def fake_run(command: Sequence[str], **_kwargs: object) -> _Result:
        calls.append(command)
        return _Result()

    monkeypatch.setattr(
        "sevaht_utility.notifications.shutil.which", fake_which
    )
    monkeypatch.setattr(
        "sevaht_utility.notifications.subprocess.run", fake_run
    )

    notify("Hi", "There", app_name="app", icon="battery-full")

    assert len(calls) == 1
    command = list(calls[0])
    assert command[0] == "/usr/bin/notify-send"
    assert command[command.index("--app-name") + 1] == "app"
    assert command[command.index("--icon") + 1] == "battery-full"
    assert command[-2:] == ["Hi", "There"]


def test_notify_falls_back_to_console(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sevaht_utility.notifications.shutil.which", lambda _name: None
    )

    notify("Title", "Body", app_name="app")

    captured = capsys.readouterr()
    assert "[app] Title: Body" in captured.err
