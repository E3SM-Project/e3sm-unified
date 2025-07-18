# Updating `mache`

`mache` is the configuration library used by E3SM-Unified (and related
projects like Polaris and Compass) to determine machine-specific settings,
including module environments and Spack configurations.

During each E3SM-Unified release, it is often necessary to:

* Add support for new machines
* Update Spack environment templates for existing systems
* Create release candidates and final versions of `mache`

This page outlines the steps for maintaining and updating `mache` during the
release process.

---

## Repo Location

🔗 [https://github.com/E3SM-Project/mache](https://github.com/E3SM-Project/mache)

---

## When to Update `mache`

You should update `mache` when:

* A supported machine has changed modules or compilers
* New machines are being targeted for deployment
* Spack YAML templates fall out of sync with system configurations
* You need to test new combinations of compiler + MPI + module environments

Each change should be tested by deploying a release candidate of E3SM-Unified.

---

## Key Tasks

### 1. Update config options

Each HPC machine supported by E3SM-Unified has a
[config file in `mache`](https://github.com/E3SM-Project/mache/tree/main/mache/machines).

The config file has a section `[e3sm_unified]`, e.g.:

```cfg
# Options related to deploying an e3sm-unified conda environment on supported
# machines
[e3sm_unified]

# the unix group for permissions for the e3sm-unified conda environment
group = cels

# the compiler set to use for system libraries
compiler = gnu

# the system MPI library
mpi = openmpi

# the path to the directory where activation scripts, the base environment, and
# system libraries will be deployed
base_path = /lcrc/soft/climate/e3sm-unified

# whether to use E3SM modules for hdf5, netcdf-c, netcdf-fortran and pnetcdf
# (spack modules are used otherwise)
use_e3sm_hdf5_netcdf = False
```

These config options control the default deployment behavior, including the
Unix `group` that the E3SM-Unified environment will belong to, the
`compiler` and `mpi` library used to build E3SM-Unified Spack packages by
default, The `base_path` under which the conda and spack environments as well
as the activation scripts will be installed, and whether that machine will
use E3SM's version of `hdf5`, `netcdf-c`, `netcdf-fortran`, `parallel-netcdf`,
etc. or install them from Spack.

### 2. Edit Spack Templates

Spack environment templates live in:

```
mache/spack/templates/<machine>_<compiler>_<mpi>.yaml
```

Edit these files to reflect updated system modules or new toolchains.
If adding a new machine, copy an existing `yaml` file to use as a template.

Use the utility script to assist:
🔗 [utils/update_cime_machine_config.py README](https://github.com/E3SM-Project/mache/blob/main/utils/README.md)

This script can be used to download the latest version of the
`config_machines.xml` file from E3SM's master branch, then compare it to the
previous version stored in `mache`, showing changes related to supported
machines.

You should make the changes associated with the differences that this utility
displays in the appropriate `mache/spack/templates` files. You should then copy `new_config_machines.xml` into `mache/cime_machine_config/config_machines.xml`
as the new reference set of machine configurations that `mache` is in sync
with.

---

### 3. Create a Release Candidate

Use the typical GitHub flow:

```bash
git checkout -b update-to-1.32.0
# Make changes
# Push branch and open PR
```

Once the PR is reviewed and merged:

* Tag a release candidate (e.g., `1.32.0rc1`)
* Publish it to conda-forge under `mache_dev` (by merging a PR that targets
  the `dev` branch)

This RC will be referenced in the E3SM-Unified build process.

**Note:** As we will discuss later, it is also possible to test E3SM-Unified
with a development branch of `mache` available on GitHub.  However, it is
always cleaner to use a release candidate.

---

### 4. Finalize the Release

Once testing across all platforms is complete:

* Create a final version tag (e.g., `1.32.0`)
* Always use [semantic versioning](https://semver.org/)
* Submit a PR to `mache-feedstock` to update the recipe (this time targeting
  the `main` branch)
* Merge once CI passes

Afterward, update any references to the RC version in the E3SM-Unified repo to
point to the final release.

---

## Best Practices

* Be liberal in what system tools (`tar`, `CMake`, etc.) are defined as
  `buildable: false` in Spack environments.  Anything Spack doesn't have to
  build saves time and avoids potential build errors due to inconsistent
  toolchain assumptions.
* Regularly sync templates with actual E3SM production configurations
* Validate changes via test deployments of E3SM-Unified (or Polaris or Compass)
  before tagging final versions.
* New mache releases will need to be made as needed by any of the
  **downstream** repos — currently E3SM-Unified, Polaris, and Compass.

---

➡ Next: [Deploying on HPCs](deploying-on-hpcs.md)
