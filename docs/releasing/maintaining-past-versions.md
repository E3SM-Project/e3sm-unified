# Maintaining Past Versions

After a new version of E3SM-Unified is released, older versions may still be
in use for months or years by analysis workflows, diagnostic pipelines, or
collaborators working on older datasets. This page outlines best practices for
keeping past versions available and usable.

---

## 🎯 Goals

* Ensure long-term reproducibility
* Avoid breaking existing workflows
* Minimize overhead for maintainers
* Free up limited disk space when required

---

## 🔒 Avoid Breaking Changes

### Don’t Delete Spack or Conda Environments

E3SM-Unified installs are isolated by version. Do not delete directories like:

```bash
/lcrc/soft/climate/e3sm-unified/base/envs/e3sm_unified_1.11.0/
/lcrc/soft/climate/e3sm-unified/spack/e3sm_unified_1.11.0_chrysalis_gnu_mpich/
```

These environments may be used by others via scripts, batch jobs, or notebooks.

**Exception**: If the environment is broken beyond repair and cannot be
recreated, it should be removed. If there is no more disk space for software,
the oldest environments must be deleted to make room for new ones. Use your
best judgment and document removals on Confluence.

### Don’t Remove Activation Scripts

Keep activation scripts for previous versions (e.g.,
`load_e3sm_unified_1.11.0_chrysalis.sh`) in place.

**Exception**: If the environment has been removed, it is safe to remove the
associated activation scripts.

---

## 🧹 What Can Be Removed

### Test Environments

You can safely delete environments or activation scripts for
**release candidates**:

* `test_e3sm_unified_1.11.0rc3_*.sh`
* Conda environments like `test_e3sm_unified_install`

These were used only during internal testing and should be removed when they
are no longer needed to free up disk space.

### Intermediate Build Artifacts

Temporary logs or caches (e.g., from failed deployments) can be removed to
save space.

---

## 🔁 Rebuilding Past Versions

If a past version breaks due to:

* OS upgrades
* Module stack changes
* File system reorganizations

...you may need to rebuild that version. Follow these steps:

1. Checkout the appropriate tag in the `e3sm-unified` repo (e.g., `1.11.0`)
3. Use `deploy_e3sm_unified.py` with the `--version` flag (as a precaution):

```bash
./deploy_e3sm_unified.py --conda ~/miniforge3 --version 1.11.0 --release --recreate
```

You may run into difficulty solving for older conda environments e.g. because
of packages that have been marked as broken in the interim.  At some point, it
may simply not be possible to recreate older E3SM-Unified conda environments
because of this.

---

## 💬 Communication

* Coordinate cleanup of old versions via Slack (`#e3sm-help-postproc`)
* Use Confluence notes to document version removals or rebuilds

---

Back to: [Publishing the Final Release](publishing-final-release.md)
