# Updating Spack Packages

The `hpc` variant of E3SM-Unified builds performance-critical tools (NCO,
ESMF, MOAB, TempestRemap, TempestExtremes and, on some machines, HDF5 and
NetCDF) with Spack against each machine's compilers and MPI. This page
explains where the Spack recipes come from and how to pick up a new package
version during a release cycle without waiting for a new `mache` release.

---

## Where the Recipes Come From

`mache` 5 uses Spack 1.x, which keeps packages in repositories separate from
Spack itself. A deployment checks out three repositories:

| Repository | Spack namespace | Contents |
|------------|-----------------|----------|
| [spack/spack](https://github.com/spack/spack) | — | the Spack tool |
| [E3SM-Project/e3sm-spack-packages](https://github.com/E3SM-Project/e3sm-spack-packages) | `e3sm` | versions and fixes E3SM needs ahead of upstream |
| [spack/spack-packages](https://github.com/spack/spack-packages) | `builtin` | upstream recipes |

The `e3sm` repository is searched ahead of `builtin`, so a recipe there
shadows the upstream one. Each `mache` release pins a tag of each repository
in `mache/spack/pins.yaml`. The old `E3SM-Project/spack` fork and its
`spack_for_mache_<version>` branches are retired.

The Spack checkout for a deployment lives under that version's prefix, and
every deployment hard-resets the package repositories to the pinned refs, so
changing a pin takes effect on the next deployment.

---

## Adding a Package Version

1. Open a pull request against
   [e3sm-spack-packages](https://github.com/E3SM-Project/e3sm-spack-packages)
   adding the version (its README explains how recipes subclass upstream).
   Submit the same version upstream to `spack-packages` so the `e3sm` copy can
   be dropped later.

2. Once it is merged, pin the merge commit in `spack.pins` in
   `deploy/config.yaml.j2`:

   ```yaml
   spack:
     pins:
       repos:
         e3sm:
           # nco 5.4.1 (E3SM-Project/e3sm-spack-packages#2), not yet tagged
           commit: <merge commit hash>
   ```

   An override replaces only the ref of the repository it names; the others
   keep the tags from the `mache` release. `spack` and `builtin` can be
   overridden the same way.

3. Update the version in the `[spack]` section of `deploy/pins.cfg` to match
   the feedstock recipe.

No new tag, `mache` pull request, `mache` release candidate or conda-forge
package is needed to test a release candidate.

### Testing an unmerged recipe

To try a recipe before it is merged, point a single deployment at a branch,
on a fork if needed, with `--spack-pins`, which takes precedence over
`deploy/config.yaml.j2`:

```bash
cat > my_pins.yaml << EOF
repos:
  e3sm:
    git: https://github.com/<user>/e3sm-spack-packages.git
    branch: <branch>
EOF
./deploy.py --machine <machine> --spack-pins my_pins.yaml
```

Prefer a commit in `deploy/config.yaml.j2` over a branch for anything shared
with other maintainers, so every machine builds the same recipes.

---

## Before the Final Release

A `--release` deployment refuses Spack sources that are not tags from
`github.com/spack` or `github.com/E3SM-Project`. Before the final release:

1. Tag `e3sm-spack-packages` following the `vYYYY.MM.N` convention in its
   README.
2. Change the `commit` in `spack.pins` to that `tag`, or remove the
   override if the `mache` release used for E3SM-Unified already pins a tag
   that includes the change.

A new `mache` release is not required: a tag pinned in
`deploy/config.yaml.j2` is enough. The next `mache` release can pick up the
tag through an ordinary pull request that edits `mache/spack/pins.yaml`, after
which the override here can be removed.

---

➡ Next: [Updating `mache`](mache-updates.md)
