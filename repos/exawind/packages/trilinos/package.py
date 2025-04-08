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
    depends_on("kokkos~cuda", when="+kokkos~cuda")
    depends_on("kokkos~rocm", when="+kokkos~rocm")
    patch("16-1-0-stk-fpe-exceptions.patch", when="@=16.1.0 +stk platform=darwin")
    patch("16-1-0-stk-size_t.patch", when="@=16.1.0 +stk %oneapi")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)

        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "verbosity=1:log_threads=1:suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
