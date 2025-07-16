# Creating an RC for E3SM-Unified

Once release candidates (RCs) of core E3SM packages (like `e3sm_diags`,
`mpas-analysis`, etc.) have been published, an RC version of the E3SM-Unified
metapackage can be built and tested.

This guide walks through creating a release candidate of `e3sm-unified` based
on those RC dependencies.

---

## 1. Create a Branch for the New Version

Create a feature branch on your fork of `e3sm-unified`, typically called:

```bash
update-to-<version>
```

Example:

```bash
git checkout -b update-to-1.12.0
```

---

## 2. Update the Conda Recipe

Edit `recipes/e3sm-unified/meta.yaml`:

* Update the `version` field to match the RC version (e.g., `1.12.0rc1`)
* Update the list of dependencies and versions, including RCs
* Be sure to include the correct version for each core tool (e.g.,
  `e3sm_diags`, `mpas-analysis`, etc.)

---

## 3. Regenerate the Build Matrix

Run the matrix generator script to define combinations of Python and MPI:

```bash
cd recipes/e3sm-unified/configs
rm *.yaml
python generate.py
```

This produces matrix files like:

* `mpi_mpich_python3.10.yaml`
* `mpi_hpc_python3.10.yaml`

---

## 4. Edit `build_package.bash`

Update the channel list to include dev labels for any packages still in RC
form. For example:

```bash
channels="-c conda-forge/label/chemdyg_dev \
         -c conda-forge/label/e3sm_diags_dev \
         -c conda-forge/label/mache_dev \
         -c conda-forge/label/mpas_analysis_dev \
         -c conda-forge/label/zppy_dev \
         -c conda-forge/label/zstash_dev \
         -c conda-forge"
```

Then define which matrix files to test. For example:

```bash
for file in configs/mpi_mpich_python3.10.yaml configs/mpi_hpc_python3.10.yaml
do
  conda build -m $file --override-channels $channels .
done
```

Make sure:

* You use `--override-channels` to isolate testing to dev packages
* You only include dev labels for packages with RCs — use stable versions
  otherwise

---

## 5. Build and Troubleshoot

Run the script:

```bash
bash build_package.bash
```

If builds fail, consult the
[Troubleshooting Conda Build Failures](rc-troubleshooting.md) guide.
This includes how to use `conda_first_failure.py` to debug dependency
resolution issues.

---

## 6. Tag and Publish the RC

After test builds are successful:

### Tag a Release Candidate

Tag your `update-to-<version>` branch in the `e3sm-unified` repo:

```bash
git checkout update-to-1.12.0
git tag 1.12.0rc1
git remote add E3SM-Project/e3sm-unified git@github.com:E3SM-Project/e3sm-unified.git
git fetch --all -p
git push E3SM-Project/e3sm-unified 1.12.0rc1
```

### Create a Conda-Forge PR

1. Fork the [`e3sm-unified-feedstock`](https://github.com/conda-forge/e3sm-unified-feedstock)

2. Create a new branch in your fork (e.g., `update-1.12.0rc1`)

3. Edit `recipe/meta.yaml`:

   * Update the `version` field (e.g., `1.12.0rc1`)
   * Update all dependencies to match the versions in your
     `update-to-<version>` branch of `e3sm-unified` repo

   ⚠️ **Reminder:** The feedstock’s `meta.yaml` is the authoritative source
   for the Conda package. The one in the `e3sm-unified` repo is for testing
   and provenance only.

4. Open a PR from your fork → `dev` branch on the feedstock

5. Merge once CI passes

The RC package will now be available under the label:

```
conda-forge/label/e3sm_unified_dev
```

It’s ready to be tested and deployed on HPC systems.

➡ Next: [Deploying on HPCs for Testing](../testing/deploying-on-hpcs.md)
