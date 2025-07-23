# Creating RCs for Dependency Packages

This page describes how to create release candidates (RCs) for packages that
are included in the E3SM-Unified environment, such as `e3sm_diags`,
`mpas-analysis`, `zppy`, and `zstash`.

We use `e3sm_diags` as a concrete example, but the process is similar for all
E3SM-developed dependencies.

---

## Step-by-Step: Creating an RC for `e3sm_diags`

### 1. Tag a Release Candidate or Make a GitHub Release

#### 1.1 Tag a Release Candidate in the Source Repo

In some repos like MPAS-Analysis, it is desirable to tag a release candidate
without making a GitHub release page.  This avoids clutter and confusion.

We will use E3SM Diags in this example even though this is not the preferred
workflow for that repository.

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

#### 1.2 Perform at GitHub Release

In other repositories like E3SM Diags and zppy, developers prefer that you
create release pages for release candidates.  These pages provide clarity and
provenance for the release candidate just like for a normal release.

Follow these steps to create a release candidate via GitHub:

- **Pull the latest changes on `main`:**
  ```bash
  git checkout main
  git pull origin main
  ```

- **Create a new branch from `main`:**
  ```bash
  git checkout -b bump/0.1.0rc1
  ```

- **Push the branch to your fork or upstream:**
  ```bash
  git push --set-upstream origin bump/0.1.0rc1
  ```

- **Bump the version in the Python files:**
  - You can use the `tbump` tool (available in the conda development
    environments for `e3sm_diags` and `e3sm_to_cmip`):
    ```bash
    tbump 0.1.0rc1 --no-tag
    ```
    This will automatically update version strings, add, commit, and push
    changes to remote.
  - Alternatively, manually update version strings in files such as
    `pyproject.toml`, `setup.py`, and `<python_package>/__init__.py`. Then
    add, commit, and push these changes.

- **Open a pull request:**
  - Use your `bump/0.1.0rc1` branch as the source and merge into `main`.
  - Example: [Compare · E3SM-Project/e3sm_to_cmip](https://github.com/E3SM-Project/e3sm_to_cmip/compare)

- **Publish a new GitHub Release:**
  - Go to the [GitHub Releases page](https://github.com/E3SM-Project/e3sm_to_cmip/releases/new).
  - Click "Choose a tag" and enter `0.1.0rc1` (ideally without a `v`, but
    follow the repo’s conventions).
  - For "Release title", use `v0.1.0rc1` (with a `v`).
  - Click "Generate release notes" and organize the changelog as needed.
  - Check the box "Set as a pre-release".
  - Click "Publish release".

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

1. Tagging a Release Candidate or making a GitHub release
2. Opening a PR on the feedstock targeting the `dev` branch
3. Waiting for CI to pass, then merging

This process enables E3SM-Unified maintainers to incorporate the RC version of
your package into a unified test build.

➡ Next: [Creating an RC for E3SM-Unified](rc-e3sm-unified.md)
