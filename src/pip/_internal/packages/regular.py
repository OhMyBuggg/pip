import re
"""
Regular expresion about version from poetry
need to be modified when pip use.
"""

MODIFIERS = (
    "[._-]?" # means . or _ or - or nothing
    r"((?!post)(?:beta|b|c|pre|RC|alpha|a|patch|pl|p|dev)(?:(?:[.-]?\d+)*)?)?"
    r"([+-]?([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?"
)

_COMPLETE_VERSION = r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?{}(?:\+[^\s]+)?".format(
    MODIFIERS
)

COMPLETE_VERSION = re.compile("(?i)" + _COMPLETE_VERSION)

text = "1.0.0"
match = COMPLETE_VERSION.match(text)

text = text.rstrip(".")

major = int(match.group(1))
minor = int(match.group(2)) if match.group(2) else None
patch = int(match.group(3)) if match.group(3) else None

print("Version is: {}.{}.{}".format(major, minor, patch))