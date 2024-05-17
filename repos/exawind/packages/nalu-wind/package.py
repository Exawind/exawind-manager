# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.pkg.builtin.nalu_wind import NaluWind as bNaluWind
from spack.pkg.exawind.ctest_package import *


class NaluWind(CtestPackage, bNaluWind):
    version("master", branch="master", submodules=True, preferred=True)
    version("multiphase", branch="multiphase_dev", submodules=True)

    variant("asan", default=False, description="Turn on address sanitizer")
    variant("tests", default=True, description="Activate regression tests")
    variant("unit-tests", default=True, description="Activate unit tests")

    depends_on("openfast@develop", when="+fsi")
    depends_on("trilinos+rocm_rdc", when="+rocm")

    def setup_dependent_run_environment(self, env, dependent_spec):
        spec = self.spec
        super().setup_dependent_run_environment(env, dependent_spec)

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer -fsanitize-blacklist={0}".format(join_path(self.package_dir, "blacklist.asan")))
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
            env.set("ASAN_OPTIONS", "detect_container_overflow=0")

    def cmake_args(self):
        spec = self.spec

        cmake_options = super(CtestPackage, self).cmake_args()
        cmake_options.extend(super(NaluWind, self).cmake_args())

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS",True))
            cmake_options.append(self.define("ENABLE_TESTS", True))

        cmake_options.append(self.define_from_variant("ENABLE_OPENFAST_FSI", "fsi"))
        if spec.satisfies("+fsi"):
            cmake_options.append(self.define("OpenFAST_DIR", spec["openfast"].prefix))
            cmake_options.append(self.define("ENABLE_OPENFAST", True))

        if spec.satisfies("+tests") or self.run_tests or spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("ENABLE_TESTS", True))
            cmake_options.append(self.define("NALU_WIND_SAVE_GOLDS", True))
            cmake_options.append(self.define("NALU_WIND_SAVED_GOLDS_DIR", super().saved_golds_dir))
            cmake_options.append(self.define("NALU_WIND_REFERENCE_GOLDS_DIR", super().reference_golds_dir))

        return cmake_options
