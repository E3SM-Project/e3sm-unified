#!/bin/bash

export PATH="${GOPATH}/bin:${PATH}"

mkdir -p "${GOPATH}/src/github.com/sylabs"
cd "${GOPATH}/src/github.com/sylabs"

git clone https://github.com/sylabs/singularity
cd singularity
git checkout tags/v3.4.2
./mconfig -v -p /usr/local
make -j `nproc 2>/dev/null || echo 1` -C ./builddir all
sudo make -C ./builddir install

echo "Singularity version"
singularity --version
echo
