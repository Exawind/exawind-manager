#!/bin/bash

source ${EXAWIND_MANAGER}/start.sh
spack-start
spack clean -a
./deploy.py --name e4s-build --ranks=${NRANKS:-4} --depfile
