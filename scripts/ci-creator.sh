#!/bin/bash

. ../shortcut.sh
deploy.py --name ci-env --ranks=${NRANKS:-4} --depfile
spack clean -a
