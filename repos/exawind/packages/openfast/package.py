from spack import *
from spack.package import *
from spack.pkg.builtin.openfast import Openfast as bOpenfast

class Openfast(bOpenfast):
    version("4.0.4", tag="v4.0.4", commit="d28a823169e75029d73362b07a2942d0a454f03b")
    with default_args(deprecated=True):
        version("4.0.3", tag="v4.0.3", commit="20632d7728da024478956b545876eb24a48dadbe")
        version("4.0.2", tag="v4.0.2", commit="fc1110183bcc87b16d93129edabdce6d30e3a497")
        version("4.0.1", tag="v4.0.1", commit="89358f1843b62071ee1a8ca943c1b5277bcbd45a")
        version("4.0.0", tag="v4.0.0", commit="da685d4997fd17ea845812c785325efa72edcf47")
