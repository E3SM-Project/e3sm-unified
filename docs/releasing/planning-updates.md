# Planning Package Updates

Before each release of E3SM-Unified, the Infrastructure Team works with the
broader E3SM community to decide which packages and versions should be
included. This planning stage helps ensure compatibility across tools and
supports evolving analysis and diagnostic workflows.

*Note: Access to Confluence and Slack is limited to E3SM/BER collaborators.*

---

## Where Planning Happens

* **Confluence Discussion Page**: Most planning takes place on the "Next
  Version" page in the internal E3SM Documentation space. For those with
  access, use [this link](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/129732419/Packages+in+the+E3SM+Unified+conda+environment#Next-versions)
* **GitHub Issues/PRs**: Occasionally, suggestions or discussions take place
  in issues or pull requests on the
  [E3SM-Unified GitHub repository](https://github.com/E3SM-Project/e3sm-unified).
  This is the main avenue for community members without access to E3SM's
  Confluence pages.
* **Slack (`#e3sm-help-postproc`)**: For quick suggestions or discussion
  prompts for those with access to E3SM's or BER's Slack spaces.

---

## Types of Updates

### ✅ New Packages

* Tools that have become important to E3SM workflows
* Visualization, diagnostics, or file conversion utilities

### ⬆️ Version Updates

* Upgrading packages already in the environment to more recent releases
* Ensuring compatibility with latest E3SM output formats or Python versions

### ❌ Package Removal

* Rare, but sometimes necessary for deprecated tools or packages no longer
  maintained

---

## Making Suggestions

The best way to suggest a package or version change:

1. Edit the Confluence table for the upcoming version (if you have access)
2. If not, open an issue on GitHub with your suggestion and rationale
3. Optional: Tag maintainers or post on Slack to coordinate

When requesting a new package, please include:

* Package name and version
* Maintainer or expert point of contact (if known)
* Why it's useful for E3SM workflows

---

## Final Selection

The final list of packages is curated by the Infrastructure Team based on:

* Compatibility
* Stability of upstream packages
* Success in testing
* Community need and usage patterns

Once the list is mostly settled, the team begins creating release candidates
using the [Creating Release Candidates](creating-rcs.md) workflow.

---

## 📦 Managing Version Pins During Conda-Forge Migrations

E3SM-Unified often needs to coordinate with conda-forge's centralized version
pinning. Many packages used by E3SM-Unified are governed by
[global pins](https://conda-forge.org/docs/maintainer/pinning_deps/) (exact
required versions) in:

* [`conda_build_config.yaml`](https://github.com/conda-forge/conda-forge-pinning-feedstock/blob/main/recipe/conda_build_config.yaml)

### 🔀 What Happens During a Migration?

Conda-forge frequently upgrades pinned versions of core libraries (e.g.,
`hdf5`, `libnetcdf`, `proj`) via version migrations. These are tracked under:

* [`migrations/`](https://github.com/conda-forge/conda-forge-pinning-feedstock/tree/main/recipe/migrations/)

For example, the migration to `hdf5` 1.14.6 is described here:

* [`hdf51146.yaml`](https://github.com/conda-forge/conda-forge-pinning-feedstock/blob/c78051a2495698e9e612860efe058eb7e39fc528/recipe/migrations/hdf51146.yaml)

### ⚠ Why This Matters

If your dependencies are built against different versions of a migrating
library, you can end up with **incompatible binary builds** that silently fail
or break at runtime — especially with low-level C/C++ or Fortran dependencies.

### 🧠 How to Handle It

During planning, for any core dependency that is pinned:

1. Check if it's listed in a migration YAML file.
2. Determine how far the migration has progressed on the
   [conda-forge status page](https://conda-forge.org/status/):

   * If **all** of E3SM-Unified’s dependencies have adopted the new version,
     use it.
   * If **none** have, stick with the current version in
     `conda_build_config.yaml`.
   * If **some** have and some haven’t:
     ➔ You must *freeze to the old version* and *manually rebuild* any
     migrated packages against that version (typically merging to a branch
     on the conda-forge feedstock other than `main`).

### 🌀 Multiple Migrations

When multiple overlapping migrations are in progress (e.g., `hdf5`,
`libnetcdf`), assess each separately but prioritize compatibility. This is
often one of the trickiest parts of managing an E3SM-Unified release candidate.

### 📦 E3SM-Unified Dependencies Affected by Conda-Forge Pins

The ones in **bold** are those where we provide pins of our own and special care
must be taken. The rest either are unconstrained in E3SM-Unified or use version
constraints without strict pins (i.e., `>=` or `<` rather than an exact version),
so less care is required.

* ffmpeg
* **hdf5**
* **libnetcdf**
* numpy
* **proj**
* **python**
* scipy

This list may evolve from release to release as new packages are added or
pinned more strictly.
