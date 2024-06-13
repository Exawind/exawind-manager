#!/bin/bash

. ../shortcut.sh
deploy.py --ranks=${NRANKS:-4} --depfile
spack clean -a
