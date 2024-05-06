from spack import *
from spack.pkg.builtin.hypre import Hypre as bHypre
import glob
import os
import shutil

import spack.util

class Hypre(bHypre):

    variant("rocblas", default=False, description="use rocblas")
    variant("cublas", default=False, description="use cublas")

    depends_on("umpire+rocm", when="+umpire+rocm")
    depends_on("umpire+cuda", when="+umpire+cuda")
    depends_on("rocprim", when="+rocm")

    conflicts("+cublas", when="~cuda", msg="cublas requires cuda to be enabled")
    conflicts("+rocblas", when="~rocm", msg="rocblas requires rocm to be enabled")

    def configure_args(self):
        spec = self.spec
        options = super(Hypre, self).configure_args()

        if "+rocblas" in spec:
            options.append("--enable-rocblas")

        if "+cublas" in spec:
            options.append("--enable-cublas")

        if "+umpire" in spec:
            if  (("+cuda" in spec or "+rocm" in spec) and "--enable-device-memory-pool" in options):
                options.remove("--enable-device-memory-pool")

        return options
