import re
"""
Regular expresion about version from poetry
need to be modified when pip use.
"""

MODIFIERS = (
    "[._-]?"
    r"((?!post)(?:beta|b|c|pre|RC|alpha|a|patch|pl|p|dev)(?:(?:[.-]?\d+)*)?)?"
    r"([+-]?([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?"
)

_COMPLETE_VERSION = r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?{}(?:\+[^\s]+)?".format(
    MODIFIERS
)

COMPLETE_VERSION = re.compile("(?i)" + _COMPLETE_VERSION)