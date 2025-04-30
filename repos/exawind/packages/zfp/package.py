from spack import *
from spack.package import *
from spack.pkg.builtin.zfp import Zfp as bZfp

class Zfp(bZfp):
    version("1.0.1", sha256="ca0f7b4ae88044ffdda12faead30723fe83dd8f5bb0db74125df84589e60e52b")
