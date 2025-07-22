#!/usr/bin/env python3
import os
import shutil
import subprocess
import argparse

from jinja2 import Template

from shared import get_rc_dev_labels, get_version_from_meta

DEV_PYTHON_VERSIONS = ["3.10"]
DEV_MPI_VERSIONS = ["nompi", "hpc"]

RELEASE_PYTHON_VERSIONS = ["3.9", "3.10"]
RELEASE_MPI_VERSIONS = ["nompi", "mpich", "openmpi", "hpc"]


def generate_matrix_files(dev):
    with open("configs/template.yaml") as f:
        template_text = f.read()
    template = Template(template_text)
    if dev:
        python_versions = DEV_PYTHON_VERSIONS
        mpi_versions = DEV_MPI_VERSIONS
    else:
        python_versions = RELEASE_PYTHON_VERSIONS
        mpi_versions = RELEASE_MPI_VERSIONS
    matrix_files = []
    for python in python_versions:
        for mpi in mpi_versions:
            script = template.render(python=python, mpi=mpi)
            filename = f"configs/mpi_{mpi}_python{python}.yaml"
            with open(filename, "w") as handle:
                handle.write(script)
            matrix_files.append(filename)
    return matrix_files


def main():
    parser = argparse.ArgumentParser(
        description="Build E3SM-Unified conda packages."
    )
    parser.add_argument(
        "--conda",
        type=str,
        default=os.path.expanduser("~/miniforge3"),
        help="Path to the conda base directory (default: ~/miniforge3)."
    )
    args = parser.parse_args()

    conda_dir = os.path.expanduser(args.conda)
    meta_yaml_path = os.path.join(os.path.dirname(__file__), "meta.yaml")
    version = get_version_from_meta(meta_yaml_path)
    dev = "rc" in version

    # Remove conda-bld directory if it exists
    bld_dir = os.path.join(conda_dir, "conda-bld")
    if os.path.exists(bld_dir):
        shutil.rmtree(bld_dir)

    # Generate matrix files on the fly
    matrix_files = generate_matrix_files(dev)

    dev_labels = []
    if dev:
        dev_labels = get_rc_dev_labels(meta_yaml_path)

    channels = []
    for label in dev_labels:
        channels.extend(["-c", f"conda-forge/label/{label}"])
    channels += [
        "-c", "conda-forge"
    ]

    for file in matrix_files:
        cmd = [
            "conda", "build", "-m", file, "--override-channels"
        ] + channels + ["."]
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
