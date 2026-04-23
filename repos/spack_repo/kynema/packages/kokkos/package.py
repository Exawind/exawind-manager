from spack.package import *
from spack_repo.builtin.packages.kokkos.package import Kokkos as bKokkos

class Kokkos(bKokkos):
    patch("sycl_printf.patch", when="@=4.5.01")
    def cmake_args(self):
        spec = self.spec
        options = super(Kokkos, self).cmake_args()
        return options

    def setup_build_environment(self, env):
        spec = self.spec
        super().setup_build_environment(env)
