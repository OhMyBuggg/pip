# represent package class to save <package name, version>
# need to find the code to represent in that format in pip
from .version import Version

class Package(object):
    def __init__(self, name, version):
        self._name = name
        if not isinstance(version, Version):
            self._version = Version.parse(version)
        else:
          self._version = version     
           
    @classmethod
    def root(cls):  # type: () -> Package
        return Package("_root_", "0.0.0")

    @property
    def __str__(self):
        return self._name

    @property
    def version(self):
        return self._version

    
    def __eq__(self, other):
        return str(other == self._name)
    
    def __hash__(self):
        return hash((self._name, self._version))

    def __repr__(self):
        return "<Package {}>".format(self._name)