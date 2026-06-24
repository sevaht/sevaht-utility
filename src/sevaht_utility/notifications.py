"""Best-effort desktop notifications with no third-party dependencies.

:func:`notify` tries, in order:

#. ``notify-send`` (libnotify),
#. ``dbus-send`` to the freedesktop Notifications service,
#. printing to the console.

So it works in a desktop session, degrades to the terminal for CLI tools or
headless environments, and needs no GUI toolkit or D-Bus library -- making it
usable from plain command-line apps as well as GUI ones.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)

_NOTIFICATIONS_SERVICE = "org.freedesktop.Notifications"
_NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"
# Let the notification server pick its default timeout.
_DEFAULT_EXPIRE_TIMEOUT = -1


def notify(
    title: str,
    message: str,
    *,
    app_name: str | None = None,
    icon: str | None = None,
) -> None:
    """Show a desktop notification, falling back to the console.

    ``icon`` is a freedesktop icon name, used by the desktop backends. This
    never raises: an unavailable backend is skipped.
    """
    if _notify_send(title, message, app_name=app_name, icon=icon):
        return
    if _dbus_send(title, message, app_name=app_name, icon=icon):
        return
    _console(title, message, app_name=app_name)


def _run(command: list[str]) -> bool:
    try:
        result = subprocess.run(  # noqa: S603
            command, check=False, capture_output=True
        )
    except OSError:
        logger.debug("notification command failed", exc_info=True)
        return False
    return result.returncode == 0


def _notify_send(
    title: str, message: str, *, app_name: str | None, icon: str | None
) -> bool:
    executable = shutil.which("notify-send")
    if executable is None:
        return False
    command = [executable]
    if app_name is not None:
        command += ["--app-name", app_name]
    if icon is not None:
        command += ["--icon", icon]
    command += [title, message]
    return _run(command)


def _dbus_send(
    title: str, message: str, *, app_name: str | None, icon: str | None
) -> bool:
    executable = shutil.which("dbus-send")
    if executable is None:
        return False
    # Notify(app_name, replaces_id, app_icon, summary, body, actions, hints,
    # expire_timeout). Empty actions/hints arrays serialise identically
    # regardless of their declared element type, so dbus-send's a{ss} is
    # accepted for the a{sv} hints argument.
    command = [
        executable,
        "--session",
        "--type=method_call",
        f"--dest={_NOTIFICATIONS_SERVICE}",
        _NOTIFICATIONS_PATH,
        f"{_NOTIFICATIONS_SERVICE}.Notify",
        f"string:{app_name or ''}",
        "uint32:0",
        f"string:{icon or ''}",
        f"string:{title}",
        f"string:{message}",
        "array:string:",
        "dict:string:string:",
        f"int32:{_DEFAULT_EXPIRE_TIMEOUT}",
    ]
    return _run(command)


def _console(title: str, message: str, *, app_name: str | None) -> None:
    prefix = f"[{app_name}] " if app_name else ""
    print(f"{prefix}{title}: {message}", file=sys.stderr)
