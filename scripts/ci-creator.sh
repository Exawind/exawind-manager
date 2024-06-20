#!/bin/bash

source ${EXAWIND_MANAGER}/start.sh
spack-start
deploy.py --name e4s-build --ranks=${NRANKS:-4} --depfile
spack clean -a
