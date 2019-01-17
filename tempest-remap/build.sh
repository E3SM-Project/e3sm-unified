#!/usr/bin/env bash

set -x
set -e

mkdir -p ${PREFIX}/bin

LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PREFIX}

make -f Makefile.gmake

cp bin/* ${PREFIX}/bin