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

    version("16.0.1", commit="76e401dbc71e6dcb612f9b16584e0ec67dc9e645")
    version("13.4.1.2023.02.28", commit="8b3e2e1db4c7e07db13225c73057230c4814706f")
    version("13.4.0.2022.10.27", commit="da54d929ea62e78ba8e19c7d5aa83dc1e1f767c1")
    version("13.2.0.2022.06.05", commit="7498bcb9b0392c830b83787f3fb0c17079431f06")

    variant("asan", default=False, description="Turn on address sanitizer")

    patch("kokkos_zero_length_team.patch", when="@:13.3.0")
    patch("kokkos-kernels-remove-sort_option.patch", when="@15.1.1")
    patch("stk_mesh_ngpfield_template.patch", when="@16.0.1")

    # External Kokkos
    with when("@14.4: +kokkos"):
        depends_on("kokkos+wrapper", when="+wrapper")
        depends_on("kokkos~wrapper", when="~wrapper")
        depends_on("kokkos~complex_align")
        depends_on("kokkos@4.4.01", when="@16:")
        depends_on("kokkos@4.2.01", when="@15.1:15")
        depends_on("kokkos@4.1.00", when="@14.4:15.0")
        depends_on("kokkos-kernels@4.4.01", when="@16:")
        depends_on("kokkos-kernels@4.2.01", when="@15.1:15")
        depends_on("kokkos-kernels@4.1.00", when="@15.0")

        for a in CudaPackage.cuda_arch_values:
            arch_str = f"+cuda cuda_arch={a}"
            depends_on(f"kokkos{arch_str}", when=arch_str)
        for a in ROCmPackage.amdgpu_targets:
            arch_str = f"+rocm amdgpu_target={a}"
            depends_on(f"kokkos{arch_str}", when=arch_str)

    conflicts("^kokkos+cuda", when="~cuda")
    conflicts("^kokkos+rocm", when="~rocm")

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)

        if spec.satisfies("+asan"):
            env.append_flags("CXXFLAGS", "-fsanitize=address -fno-omit-frame-pointer")
            env.set("LSAN_OPTIONS", "verbosity=1:log_threads=1:suppressions={0}".format(join_path(self.package_dir, "sup.asan")))
