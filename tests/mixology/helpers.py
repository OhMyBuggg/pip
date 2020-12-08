from src.pip._vendor.mixology.failure import SolverFailure
from src.pip._vendor.mixology.package import Package
from src.pip._vendor.mixology.version_solver import VersionSolver


def check_solver_result(source, result=None, error=None, tries=None):
    solver = VersionSolver(source)

    try:
        solution = solver.solve()

    except SolverFailure as e:
        if error:
            # print("error message result\n", str(e))
            # print("error\n", error)
            assert str(e) == error
            if tries is not None:
                assert solver.solution.attempted_solutions == tries

            return

        raise

    packages = {}
    for package, version in solution.decisions.items():
        if package == Package.root():
            continue

        packages[package] = str(version)

    print("\nexpect", result)
    print("result", packages)
    assert result == packages
    if tries is not None:
        assert solution.attempted_solutions == tries
