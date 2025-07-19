# Publishing the Final Release

Once all dependencies have been tested and validated, and the E3SM-Unified
release candidate (RC) has passed testing across the relevant HPC systems, the
final release can be published. This page outlines the process of finalizing
and distributing an official E3SM-Unified release.

---

## ✅ Pre-Release Checklist

Before publishing:

* [ ] All RC versions of dependencies (e.g., `e3sm_diags`, `zppy`, `mache`)
  have been released with final version tags and conda-forge packages
* [ ] Final version of `e3sm-unified` has been created and built on conda-forge
* [ ] Final deployments have been completed on all target HPC machines
* [ ] Smoke testing and key workflows (e.g., `zppy`, `mpas_analysis`) have
  been validated

---

## Step-by-Step Finalization

### 1. Remove RC Labels

Edit `recipes/e3sm-unified/meta.yaml` and:

* Replace RC versions of dependencies (e.g., `3.0.0rc2`) with final versions
  (e.g., `3.0.0`) in both `meta.yaml` and `default.cfg`
* Bump the `e3sm-unified` version accordingly (e.g., from `1.12.0rc3` to
  `1.12.0`) in `meta.yaml` and `e3sm_supported_machines/shared.py`

Commit the changes to your `update-to-<version>` branch.

### 2. Tag Final Release in Source Repo

If you followed the suggested workflow under
[Creating an RC for E3SM-Unified](creating-rcs/rc-e3sm-unified.md), you should
have a draft PR from your `update-to-<version>` branch that documents the
changes. Merge this PR into `main` so the release history and testing context
are preserved.

Then, go to `Releases` on the right on the
[main page](https://github.com/E3SM-Project/e3sm-unified) of the repo and
click `Draft a new release` at the top.

Document the changes in this version (hopefully just copy-paste from the
description of your recently merged PR), similar to
[this example](https://github.com/E3SM-Project/e3sm-unified/releases/tag/1.11.0).

### 3. Submit Final Feedstock PR

Go to the [e3sm-unified-feedstock](https://github.com/conda-forge/e3sm-unified-feedstock):

* Open a pull request from your fork
* Update the version number and `sha256` hash.
* Target the `main` branch (not `dev`)
* Ensure final versions of all dependencies are listed

Once CI passes, merge the PR.

This will trigger CI to publish the new release to the standard conda-forge
channel.  You typically need to wait as long as an hour after packages have
built for them to become available for installation.  You can watch
[this page](https://anaconda.org/conda-forge/e3sm-unified/files)
to see when files appear and how many downloads they have.  Once all files have
been built and show 2 or more downloads, you should be good to proceed with
final deployment.

### 4. Deploy Final Release on HPC Systems

Use the same process as during RC testing, but now with the `--release` flag:

```bash
./deploy_e3sm_unified.py --conda ~/miniforge3 --release
```

This creates new activation scripts like:

* `load_e3sm_unified_<version>_<machine>.sh`

Also generates symlinks like:

* `load_latest_e3sm_unified_<machine>.sh`

### 5. Announce the Release

Share the release:

* 📝 **Confluence** [Like this example](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/4908515329/E3SM-Unified+1.11.0+release+notes)
* **Email** to [E3SM All-hands](https://e3sm.atlassian.net/wiki/spaces/ED/pages/818381294/Email+Lists) list (same contents as Confluence page)
* 📣 **Slack** (`#e3sm-help-postproc`) with release highlights

Be sure to include:

* Final versions of core E3SM-developed packages (e.g., `mpas_analysis`,
  `zppy`)
* List of supported HPC machines and activation instructions
* Summary of major changes, fixes, and new features

---

## 🔁 Post-Release Maintenance

On each supported machine:

* Clean up outdated `test_...` activation scripts
* Remove conda and spack environments for E3SM-Unified RCs
* Delete the `update-to-<version>` branch
* Move the contents on Confluence describing the
  [current version](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/129732419/Packages+in+the+E3SM+Unified+conda+environment#Current-Version)
  to the top of the
  [previous versions](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/3236233332/Packages+in+previous+versions+E3SM+Unified+conda+environment) page
* Copy the contents of the next version to be the new current version
* Update the the version under "next version" and remove all bold (to indicate
  that, as a starting point, no updates have been made to any packages in the
  next version)
* Move any release notes for older E3SM-Unified versions into the Confluence
  subdirectory for [previous versions](https://e3sm.atlassian.net/wiki/spaces/DOC/pages/3236233332/Packages+in+previous+versions+E3SM+Unified+conda+environment).

---

➡ Next: [Maintaining Past Versions](maintaining-past-versions.md)
