# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.package import *
from spack.pkg.builtin.trilinos import Trilinos as bTrilinos

class Trilinos(bTrilinos):
    variant("asan", default=False, description="Turn on address sanitizer")

    #patch("stk_mesh_ngpfield_template.patch", when="@develop")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)

        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "verbosity=1:log_threads=1:suppressions={0}".format(join_path(self.package_dir, "sup.asan")))

    def cmake_args(self):
        spec = self.spec
        cmake_options = super().cmake_args()
        if spec.satisfies("+stk platform=darwin"):
            cmake_options.append(self.define("STK_HAVE_FP_EXCEPT", False))
            cmake_options.append(self.define("STK_HAVE_FP_ERRNO", False))

        return cmake_options
