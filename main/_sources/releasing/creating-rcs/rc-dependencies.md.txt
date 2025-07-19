# Creating RCs for Dependency Packages

This page describes how to create release candidates (RCs) for packages that
are included in the E3SM-Unified environment, such as `e3sm_diags`,
`mpas-analysis`, `zppy`, and `zstash`.

We use `e3sm_diags` as a concrete example, but the process is similar for all
E3SM-developed dependencies.

---

## Step-by-Step: Creating an RC for `e3sm_diags`

### 1. Tag a Release Candidate in the Source Repo

Go to the source repository:
[E3SM Diags GitHub](https://github.com/E3SM-Project/e3sm_diags)

Create a release tag:

```bash
git checkout main
git fetch --all -p
git reset --hard origin/main
git tag v3.0.0rc1
git push origin v3.0.0rc1
```

**Note:**

* `e3sm_diags` uses a `v` prefix in version tags (e.g., `v3.0.0rc1`) as part
  of its established convention.
* For new packages, it’s recommended to follow
  [Semantic Versioning](https://semver.org/) and omit the `v` prefix (i.e.,
  tag as `3.0.0rc1`).

---

### 2. Prepare the Feedstock PR

Go to the conda-forge feedstock for `e3sm_diags`:
[E3SM Diags Feedstock](https://github.com/conda-forge/e3sm_diags-feedstock)

If a `dev` branch does not already exist:

* Clone the feedstock repo locally
* Create a new branch off `main` called `dev`
* Push it to the origin

  **Note:** By making no changes from the `main` branch, you ensure that no
  new packages will be created when you push the `dev` branch to the origin

### 3. Fork the Feedstock and Create a PR

1. Fork the feedstock repo to your GitHub account.
2. In your fork, create a new branch (e.g., `update-v3.0.0rc1`).

   **Important:** Do **not** create branches directly on the main conda-forge
   feedstock. All changes should go through a pull request from your personal
   fork. Creating a branch on the main feedstock can trigger package builds
   before your updates have been properly tested or reviewed. (e.g.,
   `update-v3.0.0rc1`).

3. Edit `recipe/meta.yaml`:

* Update the `version` field to match your RC tag (e.g., `v3.0.0rc1`)
* Set the `sha256` hash.  To determine the hash, you need to download the
  source file on a Linux (e.g. HPC) machine and run `sha256sum` on it.  For
  some reason, Macs seem to produce an incorrect hash.
* Update dependencies if needed (e.g., pin to RC versions of other tools)

4. If you created the `dev` branch above and no previous release candidates
   have been added, you will need to add `recipe/conda_build_config.yaml` with
   contents like:

   ``` yaml
   channel_targets:
     - conda-forge e3sm_diags_dev
   ```

   The label is the name of the package with any `-` replaced by `_`, followed
   by `_dev`.

5. Commit the changes and push them to the branch on your fork (unless editing
   on GitHub directly).

6. Open a pull request:

   * **Source:** your RC branch on your fork (head repository)
   * **Target:** the `dev` branch on the conda-forge feedstock (base
     repository)

---

### 4. Merge the PR Once CI Passes

After CI completes successfully:

* Review the logs if needed
* Merge the PR into the `dev` branch

The RC build will now be published to:

```
conda-forge/label/e3sm_diags_dev
```

You can test the RC by installing it like so:

```bash
conda install -c conda-forge/label/e3sm_diags_dev e3sm_diags
```

---

## Summary

Creating an RC for a dependency involves:

1. Tagging the source repository
2. Opening a PR on the feedstock targeting the `dev` branch
3. Waiting for CI to pass, then merging

This process enables E3SM-Unified maintainers to incorporate the RC version of
your package into a unified test build.

➡ Next: [Creating an RC for E3SM-Unified](rc-e3sm-unified.md)
