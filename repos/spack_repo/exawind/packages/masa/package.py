# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack_repo.builtin.packages.masa.package import Masa as bMasa
from spack.package import *

class Masa(bMasa):
    def configure_args(self):
        options = super(Masa, self).configure_args()
        return options

    def setup_build_environment(self, env: EnvironmentModifications) -> None:
        super().setup_build_environment(env)
        # Unfortunately can't use this because MASA overwrites it
        # env.set('CXXFLAGS', self.compiler.cxx11_flag)
        env.set("CXX", "{0} {1}".format(self.compiler.cxx, self.compiler.cxx11_flag))
        if self.spec.satisfies("%apple-clang"):
            env.set("CXX", "{0} {1} {2}".format(self.compiler.cxx, self.compiler.cxx11_flag, "-lstdc++"))
            env.set("CFLAGS", "-Wno-implicit-function-declaration")
