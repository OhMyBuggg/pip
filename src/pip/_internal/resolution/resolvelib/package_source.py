
from pip._internal.resolution.resolvelib.provider import PipProvider

from pip._vendor.mixology.package_source import PackageSource as BasePackageSource
from pip._vendor.mixology.constraint import Constraint
from pip._vendor.mixology.union import Union
from pip._vendor.mixology.range import Range

class PackageSource(BasePackageSource):
    def __init__(self, provider):
        self.provider = provider
        self.package = {} # store candidate



    @property
    def root_version(self):  # type: () -> Any
        raise NotImplementedError()

    # input is 'term.package'(package) and 'term.constraint.constraint'(union)
    # to get candidate
    # import!!!! use 'Contraint' to find match 'candidate' (difficult)
    # one way is change 'Constraint' back to 'requirement' and use find_match find candidate
    # the other way is we use packagefinder to find candidate  
    def _versions_for(
        self, package, constraint=None
    ):  # type: (Hashable, Any) -> List[Hashable]
        raise NotImplementedError()
    
    # use 'package' and 'version' to find 'dependency'
    # use package.name and version find candidate in self.package
    # then use self.provider._get_dependencies to get requirement
    # important!!!! turn ewquirement to dependency (difficult)
    def dependencies_for(self, package, version):  # type: (Hashable, Any) -> List[Any]
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
