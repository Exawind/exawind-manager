from spack.package import *
from spack_repo.builtin.packages.netcdf_c.package import NetcdfC as bNetcdfC

class NetcdfC(bNetcdfC):
    depends_on("c", type="build")
    depends_on("cxx", type="build")

    def cmake_args(self):
        spec = self.spec
        cmake_options = super(NetcdfC, self).cmake_args()
        
        return cmake_options
