#!/bin/bash

source ${EXAWIND_MANAGER}/start.sh
spack-start
deploy.py --ranks=${NRANKS:-4} --depfile
spack clean -a
