from pip._vendor.resolvelib.mix.package_source import PackageSource as BasePackageSource
from pip._vendor.resolvelib.mix.range import Range

# TODO change candidate 
# TODO 

class PackageSource(BasePackageSource):
    def __init__(self):
        # Add root 0.0.0
        self._root_dependencies = []
        self._packages = {}

        super(PackageSource, self).__init__()


    def convert_requirements(self, requirements):
        # change requirement -> criterion -> candidate -> _package
        