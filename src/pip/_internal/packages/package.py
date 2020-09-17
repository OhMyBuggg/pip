# represent package class to save <package name, version>
# need to find the code to represent in that format in pip
class Package(object):
    def __init__(self, name):
        self._name = name

    @property
    def __str__(self):
        return self._name
    
    def __eq__(self, other):
        return str(other == self._name)
    
    def __hash__(self):
        return hash(self._name)