#!/usr/bin/env python3

from jinja2 import Template


with open('template.yaml') as f:
    tempate_test = f.read()

template = Template(tempate_test)
for python in ['3.8', '3.9', '3.10']:
    for mpi in ['mpich', 'openmpi', 'hpc']:
        script = template.render(python=python, mpi=mpi)
        filename = f'mpi_{mpi}_python{python}.yaml'
        with open(filename, 'w') as handle:
            handle.write(script)
