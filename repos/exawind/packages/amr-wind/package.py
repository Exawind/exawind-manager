# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.pkg.builtin.amr_wind import AmrWind as bAmrWind
import os
from spack.pkg.exawind.ctest_package import *

class AmrWind(CtestPackage, bAmrWind):
    version("multiphase", branch="multiphase_dev", submodules=True)
    
    variant("asan", default=False,
            description="Turn on address sanitizer")
    variant("clangtidy", default=False,
            description="Turn on clang-tidy")

    requires("+tests", when="+cdash_submit")

    def setup_build_environment(self, env):
        super().setup_build_environment(env)
        if "+asan" in self.spec:
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))

    def cmake_args(self):
        spec = self.spec
        cmake_options = super(CtestPackage, self).cmake_args()
        cmake_options.extend(super(AmrWind, self).cmake_args())

        if spec.satisfies("dev_path=*"):
            cmake_options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS", True))

        if "+clangtidy" in spec:
            cmake_options.append(self.define("AMR_WIND_ENABLE_CLANG_TIDY", True))

        if "+tests" in spec:
            cmake_options.append(self.define("AMR_WIND_TEST_WITH_FCOMPARE", True))
            cmake_options.append(self.define("AMR_WIND_SAVE_GOLDS", True))
            cmake_options.append(self.define("AMR_WIND_SAVED_GOLDS_DIRECTORY", super().saved_golds_dir))
            cmake_options.append(self.define("AMR_WIND_REFERENCE_GOLDS_DIRECTORY", super().reference_golds_dir))

        return cmake_options
