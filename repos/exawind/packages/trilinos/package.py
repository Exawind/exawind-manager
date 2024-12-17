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
    # Our custom release versions should be the latest release tag found on
    # the trilinos github page appended with the date of the commit.
    # this preserves the Trilinos versioning scheme and will allow for valid
    # version comparisons in spack's internals.

    version("develop", commit="436ce065b6e3c37acc3f5db6807a9cdf9807c78f")
    version("13.4.1.2023.02.28", commit="8b3e2e1db4c7e07db13225c73057230c4814706f")
    version("13.4.0.2022.10.27", commit="da54d929ea62e78ba8e19c7d5aa83dc1e1f767c1")
    version("13.2.0.2022.06.05", commit="7498bcb9b0392c830b83787f3fb0c17079431f06")

    variant("asan", default=False, description="Turn on address sanitizer")

    patch("kokkos_zero_length_team.patch", when="@:13.3.0")
    patch("kokkos-kernels-remove-sort_option.patch", when="@15.1.1")

    depends_on("kokkos+cuda_relocatable_device_code~shared", when="+cuda_rdc")
    depends_on("kokkos-kernels~shared", when="+cuda_rdc")

    conflicts("^kokkos+cuda", when="~cuda")
    conflicts("^kokkos+rocm", when="~rocm")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)

        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "verbosity=1:log_threads=1:suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
