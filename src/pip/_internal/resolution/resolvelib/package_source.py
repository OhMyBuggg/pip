
from pip._internal.resolution.resolvelib.provider import PipProvider

from pip._vendor.mixology.package_source import PackageSource as BasePackageSource
from pip._vendor.mixology.constraint import Constraint
from pip._vendor.mixology.union import Union
from pip._vendor.mixology.range import Range

class Dependency:
    pass

class Version:
    def __init__(self, version):  # type: (str) -> None
        self._version = version
    
    @property
    def version(self):  # type: () -> str
        return self._version
    
    def __str__(self):  # type: () -> str
        return self._version

class Package(object):
    """
    A project's package.
    """
    def __init__(self, name):  # type: (str) -> None
        self._name = name

    @classmethod
    def root(cls):  # type: () -> Package
        return Package("_root_")

    @property
    def name(self):  # type: () -> str
        return self._name

    def __eq__(self, other):  # type: () -> bool
        return str(other) == self.name

    def __str__(self):  # type: () -> str
        return self._name

    def __repr__(self):  # type: () -> str
        return 'Package("{}")'.format(self.name)

    def __hash__(self):
        return hash(self.name)



class PackageSource(BasePackageSource):
    def __init__(self, provider):
        self.provider = provider
        self.package = {} # store candidate



    @property
    def root_version(self):  # type: () -> Any
        raise NotImplementedError()

    # input is 'term.package'(package) and 'term.constraint.constraint'(union)
    # to get candidate
    # import!!!! use 'Contraint' to find match 'candidate(version)' (difficult)
    # one way is change 'Constraint' back to 'requirement' and use find_match find candidate
    # the other way is we use packagefinder to find candidate
    def _versions_for(
        self, package, constraint=None
    ):  # type: (Hashable, Any) -> List[Hashable]
        # turn constraint to string
        # 'a>1.0.0,>=2.0.0'
        self.provider._factory.make_requirement_from_spec()
        raise NotImplementedError()
    
    # use 'package' and 'version' to find 'dependency'
    # use package.name and version find 'candidate' in self.package
    # then use self.provider._get_dependencies to get requirement
    # important!!!! turn 'requirement' to 'dependency' (difficult)
    # 'dependency' is just a type and it finally will be changed to 'constraint'
    def dependencies_for(self, package, version):  # type: (Hashable, Any) -> List[dependency]
        
        candidate = self.package[package.name][version.version]
        requirements = self.provider._get_dependencies(candidate)
        # change requirement to dependency

        raise NotImplementedError()
    
    # turn 'dependency' to 'Constraint' 
    def convert_dependency(
        self, dependency
    ):  # type: (Any) -> _Union[Constraint, Range, Union]
        """
        Converts a user-defined dependency (returned by dependencies_for())
        into a format Mixology understands.
        """
        raise NotImplementedError()   
