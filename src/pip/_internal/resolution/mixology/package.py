class Package(object):
    def __init__(self, name):
        self._name = name

    @classmethod
    def root(cls):  # type: () -> Package
        return Package("_root_")

    def __str__(self):
        return self._name 

    def __eq__(self, other):
        return str(other) == self._name

    def __repr__(self):
        return "<Package {}>".format(self._name)

    def __hash__(self):
        return hash(self._name)