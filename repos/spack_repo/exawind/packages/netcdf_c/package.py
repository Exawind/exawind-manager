from spack.package import *
from spack_repo.builtin.packages.netcdf_c.package import NetcdfC as bNetcdfC

class NetcdfC(bNetcdfC):
    depends_on("cxx", type="build")
