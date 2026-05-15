# Updating the E3SM Spack Fork

E3SM-Unified relies on a custom fork of Spack to build performance-critical
software components that are not managed by Conda. This fork includes
specialized packages (e.g., `moab`, `tempestremap`, `esmf`) and system-aware
configurations to support a wide range of HPC environments.

This page outlines the steps for updating and managing the E3SM Spack fork
during an E3SM-Unified release cycle.

---

## Repo Location

The E3SM Spack fork lives at:
🔗 [https://github.com/E3SM-Project/spack](https://github.com/E3SM-Project/spack)

---

## Key Tasks

### 1. Add or Update Package Versions

You may need to:

* Add new versions of packages like `nco`, `moab`, `esmf`, `tempestremap`, etc.
* Update build configurations, variants, or patches
* rebase onto new releases of the main [spack repo](https://github.com/spack/spack)

Follow Spack’s standard packaging conventions. Builds will typically be tested
as part of E3SM-Unified deployment (or deployment of Polaris or Compass), so
no other testing is typically necessary or practical.

After changes are validated, push them to the appropriate branch or branches
(see next section).

---

### 2. Create `spack_for_mache_<version>` Branches

The main development branch on E3SM's spack for is `develop`.  Each release of
`mache` also references a specific Spack branch named:

```
spack_for_mache_<version>
```

Example:

```
spack_for_mache_1.32.0
```

To create one from a local clone of the E3SM spack repo:

```bash
git checkout develop
git checkout -b spack_for_mache_1.32.0
git push origin spack_for_mache_1.32.0
```
This ensures that the version of `mache` used for deployment has a stable and
reproducible Spack reference.  During development of a `mache` version, this
also let you make potentially breaking changes to `spack_for_mache_<version>`
for testing without breaking the `develop` branch.  (Make sure to always push
your changes to `origin` so they are available during E3SM-Unified deployment.)

**Note**: Your `spack_for_mache_<version>` branch name should not include
`rc<n>` even if you are testing a release candidate of `mache` as part of your
E3SM-Unified deployment.  The deployment scripts automatically strip off the
`rc<n>` part when determining the name of the appropriate spack branch.

Once you have a relatively stable `spack_for_mache_<version>` branch, you can
push the changes you have made to `develop` so they are available for future
`mache` versions and other users of E3SM's spack fork.

```bash
git checkout develop
git reset --hard spack_for_mache_1.32.0
git push origin develop
```
Please be careful not to use `git push --force` here.  You should only be
adding new commits, not changing the history of `develop`.

### 3. Rebasing `develop` onto Spack Releases

One important maintenance task for the E3SM Spack fork is to keep it up-to-date
with the [main Spack repo](https://github.com/spack/spack).  This requires
interactively rebasing the `develop` branch onto the release, interactively
selecting only commits authored within the E3SM Spack fork (i.e., excluding
upstream Spack commits), and troubleshooting any merge conflicts that arise.

Because this will involve a force-push, it is important to coordinate with
other users of the fork. Make an issue similar to
[this exampe](https://github.com/E3SM-Project/spack/issues/36) and ping
relevant developers to arrange a good time for the update.

```bash
git checkout develop
git remote add spack/spack git@github.com:spack/spack.git
git fetch --all -p
git rebase -i spack/spack/v0.23.1
# edit the list of commits so the first is "Add v2.1.0 to v2.1.6 to TempestRemap"
git push --force origin develop
```

You may wish to perform the rebase using a new branch (e.g.,
`rebase-onto-v0.23.1`) that you can point to in the issue you post to
coordinate with other developers.  This way, you can ask for guidance if you
are unsure about the way you resolved any merge conflicts that arose.

---

## Best Practices

* Keep `develop` clean and stable — avoid experimental changes
* Use branches to track specific `mache` releases
* Coordinate with other E3SM package maintainers when rebasing the `develop`
  branch or updating shared packages

---

➡ Next: [Updating `mache`](mache-updates.md)
