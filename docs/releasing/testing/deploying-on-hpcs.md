# Deploying on HPCs

Once a release candidate of E3SM-Unified is ready, it must be deployed and
tested on HPC systems using a combination of Spack and Conda-based tools.
Deployment scripts and configurations live within the `e3sm_supported_machines`
directory of the E3SM-Unified repo.

This document explains the deployment workflow, what needs to be updated, and
how to test and validate the install.

---

## Deployment Components

Deployment happens via the following components:

### 🔧 `deploy_e3sm_unified.py`

* The main entry point for deploying E3SM-Unified
* Installs the combined Conda + Spack environment on supported systems
* Reads deployment config from `default.cfg` and shared logic in `shared.py`

You can find the full list of command-line flags with:

```bash
./deploy_e3sm_unified.py --help
```

You must supply `--conda` at a minimum. This is the path to a conda
installation (typically in your home directory) where the deployment tool
can create a conda environment (`temp_e3sm_unified_install`) used to install
E3SM-Unified. This environment includes the `mache` package, which can
automatically recognize the machine you are on and configure accordingly.

For release builds (but not release candidates), you should supply
`--release`. If this flag is **not** supplied, the activation scripts
created during deployment will start with `test_e3sm_unified_...` whereas
the release versions will be called `load_latest_e3sm_unified_...` and
`load_e3sm_unified_<version>...`.

Other flags are optional and will be discussed below.

### 📁 `default.cfg`

* Specifies which packages and versions to install via Spack as well as the
  versions of some conda packages required in the installation environment
  (notably `mache`)
* Version numbers here should match `meta.yaml` unless diverging for a reason
* A special case is `esmpy = None`, required so ESMPy comes from conda-forge,
  not Spack.

### ⚙️ `shared.py`

* Contains logic shared between `deploy_e3sm_unified.py` and `bootstrap.py`
* Defines the version of E3SM-Unified to deploy (hard-coded)

### 🧰 `bootstrap.py`

* Used by `deploy_e3sm_unified.py` to build and configure environments once
  the `temp_e3sm_unified_install` conda environment has been created.

### 🧪 Templates

The `e3sm_supported_machines/templates` subdirectory contains jinja2 templates
used during deployment.

* Build script template:

  * `build.template`: Used during deployment to build and install versions of
    the following packages using system compilers and MPI (if requested):

    ```bash
    mpi4py
    ilamb
    esmpy
    xesmf
    ```

  * Maintainers may need to add new packages to the template over time.
    Typically, the dependencies here are python-based but use system compilers
    and/or MPI. Spack must not install Python itself, as this would conflict
    with the Conda-managed Python environment. All Python packages need to be
    installed into the Conda environment.

* Activation script templates:

  * `load_e3sm_unified.sh.template`
  * `load_e3sm_unified.csh.template`
  * Since E3SM itself cannot be built when E3SM-Unified is active, these
    scripts set:

    ```bash
    CIME_MODEL="ENVIRONMENT_RUNNING_E3SM_UNIFIED_USE_ANOTHER_TERMINAL"
    ```

    This is supposed to tell users that they cannot build E3SM with this
    terminal window (because E3SM-Unified is loaded) and they should open
    a new one. Some users have not found this very intuitive but we don't
    currently have a better way for E3SM to detect that E3SM-Unified is active.
  * These scripts also detect whether the user is on a compute or login node
    via `$SLURM_JOB_ID` or `$COBALT_JOBID` environment variables (which should
    only be set on compute nodes).
  * Maintainers will need to edit these scripts to support new queuing systems
    (e.g. PBS).

---

## Typical Deployment Steps

1. **Update config files**:

   * Set the target version in `shared.py`
   * Update `default.cfg` with package versions (Spack + Conda)
   * Update `mache` config files (see [Updating `mache`](mache-updates.md))

2. **Test the build** on one or more HPC machines:

   ```bash
   cd e3sm_supported_machines
   ./deploy_e3sm_unified.py --conda ~/miniforge3
   ```

   **Note:** This can take a lot of time. If the connection to the HPC machine
   is not stable, you should use `screen` or similar to preserve your
   connection and you should pipe the output to a log file, e.g.:

   ```bash
   ./deploy_e3sm_unified.py --conda ~/miniforge3 | tee deploy.log
   ```

   **Note:** It is not recommended that you try to deploy E3SM-Unified
   simultaneously on two different machines that share the same base conda
   environment (e.g. Anvil and Chrysalis). The two deployments will step on
   each other's toes.

3. **Check terminal output** and validate that:

   * Spack built the expected packages
   * Conda environment was created and activated
   * Activation scripts were generated and symlinked correctly
   * Permissions have been updated successfully (read only for everyone
     except the E3SM-Unified maintainer)

4. **Manually test** tools in the installed environment

   * Load via: `source test_e3sm_unified_<version>_<machine>.sh`
   * Run tools like `zppy`, `e3sm_diags`, `mpas_analysis`

5. **Deploy more broadly** once core systems pass testing

---

## Optional flags to `deploy_e3sm_unified.py`

Here, we start with the flags that a mainainer is most likely to need, with
less useful flags at the bottom.

* `--recreate`: Rebuilds the Conda environment if it already exists. This will
  also recreate the installation environment `temp_e3sm_unified_install`.

  Note: This will **not** rebuild Spack packages from scratch. To do that,
  manually delete the corresponding Spack directory before running the
  deployment script again. These directories are typically located under:

  ```
  spack/e3sm_unified_<version>_<machine>_<compiler>_<mpi>
  ```

* `--mache_fork` and `--mache_branch`: It is common to need to co-develop
  E3SM-Unified and `mache`, and it is impractical to tag a release candidate
  and build the associated conda-forge package every time. Instead, use these
  flags to point to your fork and branch of `mache` to install into both
  the installation and testing `conda` environments. **Do not use this
  for release deployments.**

* `--tmpdir`: Set the `$TMPDIR` environment variable for Spack to use in case
  `/tmp` is full or not a desirable place to install.

* `--version`: Typically you want to deploy the latest release candidate or
  release, which should be the hard-coded default. You can set this to
  a different value to perform a deployment of an earlier version if needed.

* `--python`: Deploy with a different version of python than specified in
  `default.cfg`

* `-m` or `--machine`: Specify the machine if `mache` did not detect it
  correctly for some reason.

* `-c` or `--compiler`: Specify a different compiler than the default. To
  determine the default compiler, find the machine under
  [mache's machine config files](https://github.com/E3SM-Project/mache/tree/main/mache/machines).
  To determine which other compilers are supported, look at the list of
  [mache spack templates](https://github.com/E3SM-Project/mache/tree/main/mache/spack/templates)
  (`yaml` files).

* `-i` or `--mpi`: Similar to compilers, use this flag to specify an MPI
  variant other than the default. As above, you can determine the defaults
  and supported alternatives by looking in the configs and templates in
  `mache`.

* `-f` or `--config_file`: You can provide a config file to override defaults
  from `default.cfg` or the config file for the specific machine from `mache`.
  Use this with caution because this approach will be hard for other
  maintainers to reproduce in the future.

* `--use_local`: Typically not useful but can be used in a pinch if you have
  built conda package locally in the installation you pointed to with `--conda`
  and want to use them in the deployment.

---

## Notes for Maintainers

* A partial deployment is expected during RC testing; not all systems must be
  built initially. Chrysalis and Perlmutter are good places to start.
* Always ensure that the E3SM spack fork has a `spack_for_mache_<version>`
  branch (e.g. `spack_for_mache_1.32.0`) for the version of `mache` you are
  testing (e.g. `mache` 1.32.0rc1).
* Be aware of potential permission or filesystem issues when writing to
  shared software locations.

---

➡ Next: [Troubleshooting Deployment](troubleshooting-deploy.md)
