# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.package import *
from spack.pkg.builtin.tioga import Tioga as bTioga
from spack.pkg.exawind.ctest_package import *

class Tioga(bTioga, CtestPackage):
    variant("asan", default=False, description="Turn on address sanitizer")

    def cmake_args(self):
        spec = self.spec
        options = super(Tioga, self).cmake_args()

        if spec.satisfies("dev_path=*"):
            options.append(self.define("CMAKE_EXPORT_COMPILE_COMMANDS",True))

        return options

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer -fsanitize-blacklist={0}".format(join_path(self.package_dir, "sup.asan")))
