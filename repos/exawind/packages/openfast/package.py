# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

from spack import *
from spack.package import *
from spack.pkg.builtin.openfast import Openfast as bOpenfast

class Openfast(bOpenfast):
    version("develop", commit="024dbc1816ca8caeefcc720b1099397730b1ec0a")
    version("4.0.0", tag="v4.0.0")
    version("3.5.5", tag="v3.5.5")
    patch("openmp.patch", when="@3.5.3:3.5.4")
