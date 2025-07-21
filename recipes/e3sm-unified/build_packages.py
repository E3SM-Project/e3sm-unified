#!/usr/bin/env python3
import os
import shutil
import subprocess
import argparse
from jinja2 import Template
import yaml

LABELS = {
     "chemdyg": "chemdyg_dev",
     "e3sm_diags": "e3sm_diags_dev",
     "e3sm_to_cmip": "e3sm_to_cmip_dev",
     "mache": "mache_dev",
     "mpas-analysis": "mpas_analysis_dev",
     "mpas_tools": "mpas_tools_dev",
     "xcdat": "xcdat_dev",
     "zppy": "zppy_dev",
     "zstash": "zstash_dev",
}

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


def get_rc_dev_labels(meta_yaml_path, labels_dict):
    """Parse meta.yaml and return a list of dev labels for RC dependencies."""
    # Render the jinja template with dummy/default values
    with open(meta_yaml_path) as f:
        template_text = f.read()
    # Provide dummy/default values for all jinja variables used in meta.yaml
    template = Template(template_text)
    rendered = template.render(
        mpi='mpich',  # or any valid value
        py='310',     # or any valid value
        CONDA_PY='310',  # used in build string
    )
    meta = yaml.safe_load(rendered)
    dev_labels = []
    run_reqs = meta.get("requirements", {}).get("run", [])
    for req in run_reqs:
        # req can be a string like "pkgname version" or just "pkgname"
        if isinstance(req, str):
            parts = req.split()
            pkg = parts[0]
            version = " ".join(parts[1:]) if len(parts) > 1 else ""
            # Only match 'rc' in version, not in pkg name
            if "rc" in version and pkg in labels_dict:
                label = labels_dict[pkg]
                if label not in dev_labels:
                    dev_labels.append(label)
    return dev_labels


def get_version_from_meta(meta_yaml_path):
    """Parse the version from the {% set version = ... %} line in meta.yaml."""
    with open(meta_yaml_path) as f:
        for line in f:
            if line.strip().startswith("{% set version"):
                # e.g., {% set version = "1.11.1rc1" %}
                parts = line.split("=")
                if len(parts) >= 2:
                    version = (
                        parts[1].strip().strip('%}').strip().strip(
                            '"').strip("'")
                    )
                    return version
    raise ValueError("Could not find version in meta.yaml")


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
        dev_labels = get_rc_dev_labels(meta_yaml_path, LABELS)

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
