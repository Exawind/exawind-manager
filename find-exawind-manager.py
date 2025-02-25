# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.

import os
import socket
import sys

from gold_getter import get_golds_path


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
    "kestrel-cpu": MachineData(
        lambda: (os.environ["NREL_CLUSTER"] == "kestrel" and os.environ["CRAY_CPU_TARGET"] == "x86-spr"), "kestrel-cpu.hpc.nrel.gov"
    ),
    "kestrel-gpu": MachineData(
        lambda: (os.environ["NREL_CLUSTER"] == "kestrel" and os.environ["CRAY_CPU_TARGET"] == "x86-genoa"), "kestrel-gpu.hpc.nrel.gov"
    ),
    "mi250": MachineData(lambda: (os.environ["NREL_CLUSTER"] == "mi250"), "mi250-test.hpc.nrel.gov"),
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

def get_current_machine():
    for name, machine in machine_list.items():
        # wasteful look up but adds error checking
        if detector(name):
            return name, machine
    return None, None


def cdash_host_name():
    """get consistent hostnames for cdash"""
    # if we get here we need to error
    _ , machine = get_current_machine()
    if machine:
        return machine.full_machine_name
    else:
        raise Exception("Unsupported machines can't upload to cdash")


def cdash_build_name(spec):
    #return f"'{spec.short_spec}'".replace(" ", "_")
    filtered=spec.format("{variants}").replace("\\", "")
    filtered=spec.format("{variants}").replace("'", "")
    return spec.format("{@version}%{compiler}")+filtered


def reference_golds_default(spec):
    """
    This can eventually provide check on the machine
    and spec to give predetermined golds directories
    """
    name, _ = get_current_machine()
    if name:
        # gives data if it exists so check output
        specific_path = get_golds_path(spec, name)
        if specific_path:
            return specific_path
    # secondary path
    gold_dir = os.path.join(os.environ["EXAWIND_MANAGER"], "golds", "current", spec.name)
    os.makedirs(gold_dir, exist_ok=True)
    return gold_dir
