#!/bin/bash
#
# Copyright (c) 2022, National Technology & Engineering Solutions of Sandia,
# LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# This software is released under the BSD 3-clause license. See LICENSE file
# for more details.
#

cmd() {
  echo "+ $@"
  eval "$@"
}

# convenience function for getting to the spack-manager directory
function cd-sm(){
  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Convenience function for navigating to the spack-manager directory"
    return
  fi
  cd ${KYNEMA_MANAGER}
}

# function to initialize spack-manager's spack instance
function spack-start() {
  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "This function loads spack into your active shell"
    return
  fi
  
  # https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
  # for zsh we follow: https://stackoverflow.com/questions/9901210/bash-source0-equivalent-in-zsh
  export KYNEMA_MANAGER="$( cd -- "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" >/dev/null 2>&1 ; pwd -P )"

  function install_spack_manager(){
    export SPACK_ROOT=${KYNEMA_MANAGER}/spack
    (cd "${KYNEMA_MANAGER}" && git submodule update ${SPACK_ROOT}/../spack-manager)
    spack -E config --scope site add "config:extensions:[${KYNEMA_MANAGER}/spack-manager]"
    spack -E manager add ${KYNEMA_MANAGER}
  }

  if ! $(type '_spack_start_called' 2>/dev/null | grep -q 'function'); then
    # The default python version on Kestrel does not work correctly
    if [[ "${NREL_CLUSTER}" == 'kestrel' ]]; then
      module load cray-python
    fi

    export SPACK_ROOT=${KYNEMA_MANAGER}/spack
    export SPACK_USER_CACHE_PATH=${KYNEMA_MANAGER}/.cache
    export SPACK_USER_CONFIG_PATH=${KYNEMA_MANAGER}/.spack

    if [ -n "$SPACK_ENV" ]; then 
      OLD_SPACK_ENV=${SPACK_ENV}
      unset SPACK_ENV
    fi

    source ${SPACK_ROOT}/share/spack/setup-env.sh

    # Clean Spack misc caches
    # Put this back in if outdated caches directory still causes problems when updating Spack submodule
    #spack clean -m
    
    # move the bootstrap store outside the user config path
    if [[ -z $(spack config blame bootstrap | grep "root: ${KYNEMA_MANAGER}/.bootstrap") ]]; then
      spack -E bootstrap root ${KYNEMA_MANAGER}/.bootstrap
    fi

    if [[ -z $(spack config --scope site blame config | grep "environments_root: ${KYNEMA_MANAGER}/environments") ]]; then
      spack -E config --scope site add config:environments_root:${KYNEMA_MANAGER}/environments
    fi

    if [[ -z $(spack config --scope site blame config | grep spack-manager) ]]; then
      install_spack_manager
    fi

    if [[ -z $(spack config --scope site blame concretizer | grep 'unify:false') ]]; then
      spack -E config --scope site add "concretizer:unify:false"
    fi

    export PATH=${PATH}:${KYNEMA_MANAGER}/scripts
    export PYTHONPATH=${PYTHONPATH}:${KYNEMA_MANAGER}:${KYNEMA_MANAGER}/repos:${KYNEMA_MANAGER}/spack/var/spack/repos:${KYNEMA_MANAGER}/spack/lib/spack

    if [[ -z $(spack repo list | awk '{print $2" "$4}' | grep "kynema $KYNEMA_MANAGER") ]]; then
      spack -E repo add ${KYNEMA_MANAGER}/repos/spack_repo/kynema
      spack -E repo add https://github.com/jrood-nrel/spack-packages.git
    fi

    if [[ -z $(spack config --scope site blame bootstrap | grep spack-bootstrap-store) ]]; then
      if [[ "$(spack manager find-machine | awk '{print $2}')" == "cee" ]]; then
        spack -E bootstrap add --scope site --trust wind-binaries /projects/wind/spack-bootstrap-store/metadata/binaries
      fi
    fi

    if [[ "$(spack manager find-machine | awk '{print $2}')" == "darwin" && ! -f ${SPACK_USER_CONFIG_PATH}/darwin/compilers.yaml ]]; then
      spack -E compiler find
    fi

    source ${KYNEMA_MANAGER}/spack-manager/scripts/quick_commands.sh
    # define a function since environment variables are sometimes preserved in a subshell but functions aren't
    # see https://github.com/psakievich/spack-manager/issues/210
    function _spack_start_called(){
      echo "TRUE"
    }
    if [ -n "${OLD_SPACK_ENV}" ]; then
      export SPACK_ENV=${OLD_SPACK_ENV}
    fi
  fi
}
