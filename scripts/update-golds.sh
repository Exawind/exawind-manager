#!/bin/bash -l

set -e

MYHOME=/data/ssd1/home/${USER}
MYEW=${MYHOME}/exawind
MYEWM=${MYEW}/exawind-manager
MYGOLDS=${MYEW}/golds/current
DATE=$(date -I)

cmd() {
  echo "+ $@"
  eval "$@"
}

copy() {
  SPEC=${1}
  GOLD_SPEC_DIR=${2}
  GOLD_DIR=${3}

  SPEC_DIR=$(spack location -i ${SPEC})
  echo ""
  echo "Copying ${SPEC} golds..."
  echo "rm -r ${GOLD_DIR}/${GOLD_SPEC_DIR}/*"
  echo "cp -R ${SPEC_DIR}/golds/Linux ${GOLD_DIR}/${GOLD_SPEC_DIR}/"
}

cmd "cd ${MYEWM}"
cmd "source shortcut.sh"
cmd "spack env activate ${DATE}"

for APP in exawind amr-wind nalu-wind
do
  GOLD_DIR=${MYGOLDS}/${APP}

  #~asan%clang
  SPEC=${APP}~asan%clang
  GOLD_SPEC_DIR=clang-cpu
  copy ${SPEC} ${GOLD_SPEC_DIR} ${GOLD_DIR}

  #+asan%clang
  SPEC=${APP}+asan%clang
  GOLD_SPEC_DIR=clang-cpu-asan
  copy ${SPEC} ${GOLD_SPEC_DIR} ${GOLD_DIR}

  #~cuda%gcc
  SPEC=${APP}~cuda%gcc
  GOLD_SPEC_DIR=gcc-cpu
  copy ${SPEC} ${GOLD_SPEC_DIR} ${GOLD_DIR}

  #+cuda%gcc
  SPEC=${APP}+cuda%gcc
  GOLD_SPEC_DIR=gcc-gpu
  copy ${SPEC} ${GOLD_SPEC_DIR} ${GOLD_DIR}
done
