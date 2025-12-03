# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack.package import *
from spack_repo.builtin.packages.trilinos.package import Trilinos as bTrilinos

class Trilinos(bTrilinos):
    url = "https://github.com/trilinos/Trilinos/archive/refs/tags/16.2.0.tar.gz"
    version("16.2.0", sha256="a5dd61e7752b6c0c53e89495aa68e099a5f68b6b775fff49e324c3b177174488")
    variant("asan", default=False, description="Turn on address sanitizer")

    depends_on("kokkos@=4.7.01", when="@16.2 +kokkos")
    depends_on("kokkos-kernels@=4.7.01", when="@16.2 +kokkos")

    def flag_handler(self, name, flags):
        super().flag_handler(name, flags)
        if name == "cxxflags":
            if "+stk" in self.spec:
                flags.append("-DUSE_STK_SIMD_NONE")
        return (flags, None, None)

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)

        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
