class Version(object):
    def __init__(self, major, minor, patch, text):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._text = text

    @property
    def __str__(self):
        return self._text
    def __repr__(self):
        return "<Version {}>".format(str(self))
