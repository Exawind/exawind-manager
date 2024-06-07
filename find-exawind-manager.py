# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

import os
import socket
import sys


class MachineData:
    def __init__(self, test, full_machine_name):
        self.i_am_this_machine = test
        self.full_machine_name = full_machine_name


def is_cee(hostname):
    site = False
    system = False
    if "SNLSITE" in os.environ:
        site = os.environ["SNLSITE"] == "cee"
    if "SNLSYSTEM" in os.environ:
        system = os.environ["SNLSYSTEM"] == "cee"
    detected = site or system
    return detected


def is_cts_1(hostname):
    known_hosts = ("skybridge", "ghost", "attaway", "chama")
    for k in known_hosts:
        if k in hostname:
            return True
    return False


def is_azure():
    if "CYCLECLOUD_HOME" in os.environ:
        return True
    else:
        return False


def is_e4s():
    if "E4S_MACHINE" in os.environ:
        return True
    else:
        return False


"""
Set up a dictionary with a key for machine name and checker function
for value - the checker function should return true for the machine
match
"""
machine_list = {
    # SNL
    "cee": MachineData(lambda: is_cee(socket.gethostname()), "cee.snl.gov"),
    "cts-1": MachineData(lambda: is_cts_1(socket.gethostname()), "cts-1.snl.gov"),
    # NREL
    "kestrel": MachineData(
        lambda: os.environ["NREL_CLUSTER"] == "kestrel", "kestrel.hpc.nrel.gov"
    ),
    "eagle": MachineData(lambda: os.environ["NREL_CLUSTER"] == "eagle", "eagle.hpc.nrel.gov"),
    "rhodes": MachineData(lambda: os.environ["NREL_CLUSTER"] == "rhodes", "rhodes.hpc.nrel.gov"),
    "ellis": MachineData(lambda: os.environ["NREL_CLUSTER"] == "ellis", "ellis.hpc.nrel.gov"),
    # OLCF
    "summit": MachineData(
        lambda: os.environ["LMOD_SYSTEM_NAME"] == "summit", "summit.olcf.ornl.gov"
    ),
    "frontier": MachineData(
        lambda: os.environ["LMOD_SYSTEM_NAME"] == "frontier", "frontier.olcf.ornl.gov"
    ),
    # ALCF
    "aurora": MachineData(lambda: "aurora" in socket.getfqdn(), "aurora.alcf.anl.gov"),
    "sunspot": MachineData(lambda: "americas.sgi.com" in socket.getfqdn(), "sunspot.alcf.anl.gov"),
    # E4S
    "e4s": MachineData(lambda: is_e4s(), "e4s.nodomain.gov"),
    # Azure
    "azure": MachineData(lambda: is_azure(), "azure.nodomain.com"),
    # NERSC
    "perlmutter": MachineData(
        lambda: os.environ["NERSC_HOST"] == "perlmutter", "perlmutter-p1.nersc.gov"
    ),
    # General
    "darwin": MachineData(lambda: sys.platform == "darwin", "darwin.nodomain.gov"),
}


def detector(name):
    for machine_name, data in machine_list.items():
        """
        Since we don't expect uniform environments on all machines
        we bury our checks in a try/except
        """
        if name == machine_name:
            try:
                return data.i_am_this_machine()
            except KeyError:
                """
                expect key errors when an environment variable is not defined
                so these are skipped
                """
                pass
            except Exception:
                """
                all other errors will be raised and kill the program
                we can add more excpetions to the pass list as needed
                in the future
                """
                raise
    return False


def cdash_host_name():
    """get consistent hostnames for cdash"""
    for name, machine in machine_list.items():
        # wasteful look up but adds error checking
        if detector(name):
            return machine.full_machine_name
    # if we get here we need to error
    raise Exception("Unsupported machines can't upload to cdash")


def cdash_build_name(spec):
    return spec.format("{name}{@version}%{compiler}")


def reference_golds_default(spec):
    """
    This can eventually provide check on the machine
    and spec to give predetermined golds directories
    """
    gold_dir = os.path.join(os.environ["EXAWIND_MANAGER"], "golds", "current", spec.name)
    os.makedirs(gold_dir, exist_ok=True)
    return gold_dir
