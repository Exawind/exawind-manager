from spack import *
from spack.package import *
from spack.pkg.builtin.openfast import Openfast as bOpenfast

class Openfast(bOpenfast):
    version("4.0.3", tag="v4.0.3", commit="20632d7728da024478956b545876eb24a48dadbe")
