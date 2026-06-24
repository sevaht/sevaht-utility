"""General-purpose utilities.

Submodules:

* :mod:`sevaht_utility.naming` -- identifier case detection and conversion.
* :mod:`sevaht_utility.parsing` -- text, CSV, and JSON parsing helpers.
* :mod:`sevaht_utility.hinting` -- runtime type-hint inspection.
* :mod:`sevaht_utility.log_utility` -- opinionated logging setup.
* :mod:`sevaht_utility.notifications` -- best-effort desktop notifications
  (notify-send/dbus-send, falling back to the console) with no dependencies.

Attributes:
    __version__: The installed distribution version.
"""

import importlib.metadata

__version__ = importlib.metadata.version(__package__)
