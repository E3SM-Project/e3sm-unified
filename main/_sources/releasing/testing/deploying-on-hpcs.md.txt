# Deploying on HPCs

Once a release candidate of E3SM-Unified is ready, it must be deployed and
tested on HPC systems using the deployment configuration in this repository's
`deploy/` directory together with `mache deploy`. Pixi manages the deployed
conda environments, and Spack is used only when the selected package variant
requires machine-specific system libraries.

This document explains the deployment workflow, what needs to be updated, and
how to test and validate the install.

---

## Deployment Components

Deployment happens via the following components:

### 🔧 `./deploy.py`

* The main entry point for deploying E3SM-Unified from this repository
* Reads `deploy/pins.cfg`, `deploy/cli_spec.json`, and
  `deploy/custom_cli_spec.json`
* Creates a bootstrap Pixi environment and then invokes `mache deploy run`
  internally

The workflow should start from the repository root with `./deploy.py`.
The CLI exposed by `./deploy.py` is assembled from `deploy/cli_spec.json`
plus `deploy/custom_cli_spec.json`.

You can inspect the routed arguments in:

```bash
./deploy.py --help
cat deploy/cli_spec.json
cat deploy/custom_cli_spec.json
```

The wrapper also supports repository-specific flags such as `--release`,
`--package-source`, `--package-mpi`, `--env-layout`, and
`--load-script-dir`.

When `mache` itself changes, refresh the mache-owned deployment assets with
`mache deploy update` before testing deployments. See
[Updating `mache`](mache-updates.md) for the exact sequence and for the list of
files that still must be edited manually afterward.

### 📁 `deploy/pins.cfg`

* Pins the bootstrap Python version, deployed Python version, and `mache`
  version
* Pins versions for Spack-managed packages and optional post-install packages
* Is **not** updated by `mache deploy update`; maintainers must edit it
  manually after refreshing mache-owned assets
* Should stay aligned with
  `recipes/e3sm-unified/e3sm-unified-feedstock/recipe/recipe.yaml` unless
  there is an intentional reason to diverge

### ⚙️ `deploy/config.yaml.j2`

* Defines the generic `mache deploy` project configuration
* Delegates machine-specific and E3SM-Unified-specific decisions to hooks
* Controls Pixi prefixes, permissions, runtime version checks, and Spack
  behavior

### 🧰 `deploy/hooks.py`

* Resolves the deployed E3SM-Unified version from the feedstock recipe unless
  overridden
* Selects channels, package source, package MPI, and environment layout
* Enables or disables Spack dynamically based on the chosen package variant
* Adds E3SM-Unified-specific environment variables through `deploy/load.sh`

### 🧪 Templates

The key templates live in the `deploy/` directory:

* `deploy/pixi.toml.j2`
* `deploy/spack.yaml.j2`
* `deploy/config.yaml.j2`

`mache` contributes the higher-level deployment templates and generated wrapper
scripts. E3SM-Unified supplies the repository-specific pieces above.

When you run `mache deploy update`, the mache-owned wrapper and template files
in `deploy/` are refreshed automatically. The maintainer-owned version pins in
`deploy/pins.cfg` and the CI dependency pin in `pixi.toml` still need manual
updates.

### 🧪 `ci/render_pixi_manifest.py`

* Used only in CI to validate that locally built packages can be installed with
  Pixi from the generated local channel

---

## Typical Deployment Steps

1. **Update config files**:

   * If you updated `mache`, first run `mache deploy update` as described in
     [Updating `mache`](mache-updates.md)
   * Update the version and dependency pins in
     `recipes/e3sm-unified/e3sm-unified-feedstock/recipe/recipe.yaml`
   * Update `deploy/pins.cfg` with bootstrap, `mache`, Spack, and post-install
     pins
   * Update `pixi.toml` so the CI/test environment uses the intended `mache`
     version
   * Review `deploy/hooks.py` if package-variant or channel behavior changed
   * Update `mache` config files (see [Updating `mache`](mache-updates.md))

2. **Test the build** on one or more HPC machines:

   ```bash
   ./deploy.py --machine <machine>
   ```

   **Note:** This can take a lot of time. If the connection to the HPC machine
   is not stable, you should use `screen` or similar to preserve your
   connection and you should pipe the output to a log file, e.g.:

   ```bash
   ./deploy.py --machine <machine> 2>&1 | tee deploy.log
   ```

   **Note:** It is not recommended that you try to deploy E3SM-Unified
   simultaneously on two different machines that share the same deployment
   prefix. The runs will step on each other's state.

3. **Check terminal output** and validate that:

   * The expected Pixi environment or environments were created
   * Spack built the expected packages when `--package-mpi hpc` was used
   * Activation scripts were generated and symlinked correctly
   * Permissions have been updated successfully (read only for everyone
     except the E3SM-Unified maintainer)

4. **Verify compute-node activation**

   When `--env-layout dual` is used, the load scripts are designed to load a
   login-friendly environment on login nodes and the compute-node environment
   when scheduler variables indicate that you are inside an allocation.
   Before manual testing, confirm that sourcing the script on a compute node
   loads the expected package variant.

   Steps:

   * Start an interactive job on a compute node, for example:

     - Slurm:

       ```bash
       salloc -N 1 -t 10:00
       ```

     - Cobalt:

       ```bash
       qsub -I -n 1 -t 10
       ```

     - PBS (example):

       ```bash
       qsub -I -l select=1:ncpus=1:mpiprocs=1,walltime=00:10:00
       ```

   * On the compute node, source the activation script:

     - Bash/zsh:

       ```bash
       source test_e3sm_unified_<version>_<machine>.sh
       ```

     - csh/tcsh:

       ```bash
       source test_e3sm_unified_<version>_<machine>.csh
       ```

     For release builds, use the corresponding `load_e3sm_unified_<version>_<machine>.*`
     or `load_latest_e3sm_unified_<machine>.*` script names.

   * Verify that the MPI environment is active (not the no-MPI one):

     ```bash
     echo "$E3SMU_MPI"   # should reflect the compute-node variant
     which python        # should point to the active Pixi env
     python -c "import mpi4py, xarray; print('mpi4py:', mpi4py.__version__)"
     ```

     Optional quick MPI sanity check (if mpirun/srun is available on the node):

     ```bash
     mpirun -n 2 python -c "from mpi4py import MPI; print(MPI.COMM_WORLD.Get_size())"
     # or, for Slurm
     srun -n 2 python -c "from mpi4py import MPI; print(MPI.COMM_WORLD.Get_size())"
     ```

   If the script loads the login environment on a compute node, check that the
   scheduler environment variables are present on compute nodes for this
   machine and update the relevant `mache` deployment logic if needed.

5. **Manually test** tools in the installed environment

   * Load via: `source test_e3sm_unified_<version>_<machine>.sh`
   * Run tools like `zppy`, `e3sm_diags`, `mpas_analysis`

6. **Deploy more broadly** once core systems pass testing

---

## Common flags

These are the repository-specific flags maintainers are most likely to use.

* `--recreate`: Rebuilds the Pixi environment if it already exists.

  This will **not** necessarily rebuild Spack packages from scratch. To do
  that, manually delete the corresponding Spack environment before rerunning.

* `--release`: Performs a shared release deployment. This forbids local package
  builds and forked `mache` sources.

* `--package-source`: Choose between `conda-forge` and `local-build`.

  `local-build` is useful while validating a release candidate before the
  package has been published.

* `--package-mpi`: Choose `nompi`, `mpich`, `openmpi`, or `hpc`.

  On supported HPC systems, `hpc` is typically the target release variant.

* `--env-layout`: Choose `single` or `dual`.

  `dual` is typically used for shared HPC deployments so login and compute
  nodes can use different runtime environments through one load script.

* `--e3sm-unified-version`: Override the version resolved from the feedstock
  recipe.

* `--mache-fork` and `--mache-branch`: Test against a development branch of
  `mache` instead of a tagged release. Do not use these for release
  deployments.

* `--spack-path`: Point to a specific Spack checkout.

* `--spack-tmpdir`: Set a temporary directory for Spack builds.

* `--python`: Override the Python version pinned in `deploy/pins.cfg`.

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

* `--load-script-dir`: Write a copy of the generated load script to a specific
  directory.

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
