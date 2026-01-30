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

Edit the feedstock recipe in the submodule at
`recipes/e3sm-unified/e3sm-unified-feedstock/recipe/recipe.yaml`:

* Update the `version` field to match the RC version (e.g., `1.12.0rc1`)
* Update the list of dependencies and versions, including RCs
* Be sure to include the correct version for each core tool (e.g.,
  `e3sm_diags`, `mpas-analysis`, etc.)

After a successful local test build, push these updates to a branch on your
fork of the `e3sm-unified-feedstock` and open a pull request against either
the `main` or `dev` branch, depending on whether the version is a release or
release candidate.

---
## 3. Run `build_packages.py`

The script builds the full variant matrix defined in
`recipes/e3sm-unified/e3sm-unified-feedstock/.ci_support` for the current
platform. Use the `--python` and `--mpi` flags to filter that matrix.

### Build test packages locally (maintainers)

When maintainers need to produce test packages, use the feedstock submodule
and the rattler-build workflow. From the root of the repo:

```bash
cd e3sm-unified/recipes/e3sm-unified
git submodule update --init
conda install rattler-build
./build_packages.py --python 3.13 --mpi hpc mpich nompi
```

This will produce a set of packages in:
```
outputs/linux-64/e3sm-unified-1.12.0-hpc_py313hade9021_1.conda
outputs/linux-64/e3sm-unified-1.12.0-nompi_py313h296f607_1.conda
```

---

## 4. Troubleshoot

If builds fail, consult the
[Troubleshooting Conda Build Failures](rc-troubleshooting.md) guide.
This includes how to use `conda_first_failure.py` to debug dependency
resolution issues.

---

## 5. Make a draft PR

Push the branch to your fork of `e3sm-unified` and make a draft PR to the
main `e3sm-unified` repo.  Use that PR to document progress and highlight
important version updates in this release for the public (those without
acces to E3SM's Confluence pages). See
[this example](https://github.com/E3SM-Project/e3sm-unified/pull/125).

---

## 6. Keeping updated on Confluence

As deployment and testing progresses, you needs to make sure that the packages
in your `update-to-<version>` branch match the
[agreed-upon versions on Confluence](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/129732419/Packages+in+the+E3SM+Unified+conda+environment#Next-versions).
Maintainers of dependencies will need to inform you as new release candidates
or final releases become available, preferably by updating Confluence and also
sending a Slack message or email.

As testing nears completion, it is also time to draft a release note, similar
to [this example](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/4908515329/E3SM-Unified+1.11.0+release+notes).
Ask maintainers of any of the main E3SM-Unified packages that have been
updated since the last release to describe (**briefly and with minimal
jargon**) what is new in their package that would be of interest to users.

---

## 7. Tag and Publish the RC

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
