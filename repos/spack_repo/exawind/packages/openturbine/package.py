from spack.package import *
from spack_repo.builtin.packages.openturbine.package import Openturbine as bOpenturbine
from spack_repo.exawind.packages.ctest_package.package import *


class Openturbine(bOpenturbine, CtestPackage):
    variant("asan", default=False, description="Turn on address sanitizer")

    depends_on("suite-sparse@7.4:", when="+klu")
    depends_on("netcdf-c@4.9:")
    depends_on("yaml-cpp@0.6:")

    requires("+tests", when="+cdash_submit")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))

    def cmake_args(self):
        spec = self.spec
        cmake_options = super(Openturbine, self).cmake_args()

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))

        return cmake_options
