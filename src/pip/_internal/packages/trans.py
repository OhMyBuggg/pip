import re

from pip._vendor.packaging.specifiers import SpecifierSet
# from pip._vendor.resolvelib.mix.range import Range

specifier1 = SpecifierSet('> 1.0.0')
specifier2 = SpecifierSet('< 1.0.0')
specifier3 = SpecifierSet('>= 1.0.0')
specifier4 = SpecifierSet('<= 1.0.0')
specifier5 = SpecifierSet('!= 1.0.0')
specifier6 = SpecifierSet('== 1.0.0')

# _COMPLETE_CONSTRAINT = (S)
# COMPLETE_CONSTRAINT = re.compile(_COMPLETE_CONSTRAINT)

MODIFIERS = (
    r"(?:>|<|>=|<=|!=|==) ([0-9]+(\.[0-9]+)*)"
)

#_COMPLETE_VERSION = r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?{}(?:\+[^\s]+)?".format(
#    MODIFIERS
#)

COMPLETE_VERSION = re.compile(MODIFIERS)
# COMPLETE_VERSION = re.compile("(?i)" + _COMPLETE_VERSION)

def trans(specifier):
    match = COMPLETE_VERSION.match(specifier)
    op = match.group(0)
    version = match.group(1)

    print("Cons: {} {}".format(op, version))

trans('>= 12.10 ')