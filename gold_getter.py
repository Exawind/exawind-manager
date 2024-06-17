import os
import spack.util.spack_yaml as spack_yaml

from spack.spec import Spec

def get_golds_yaml():
    path = os.path.join(os.environ["EXAWIND_MANAGER"], "golds.yaml")
    assert os.path.isfile(path)
    with open(path, "r") as f:
        yaml = spack_yaml.load(f)
    return yaml

def get_golds_path(spec, machine):
    """
    Look for a specific gold match using spec comparisons
    """
    gyaml = get_golds_yaml()

    if machine not in gyaml:
        return None

    myaml = gyaml[machine]

    for spec_pair in myaml:
       gold_spec_str, gold_path = spec_pair 
       gold_spec = Spec(gold_spec_str)

       if gold_spec.satisfies(spec):
            return gold_path

    return None
