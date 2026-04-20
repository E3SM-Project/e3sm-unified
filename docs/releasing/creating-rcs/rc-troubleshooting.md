# Troubleshooting Pixi Solve Failures

When building a release candidate (RC) of E3SM-Unified, it's common to
encounter solver or build failures due to dependency conflicts, pinning
mismatches, or version incompatibilities.

This page outlines common issues and how to debug them effectively.

---

## Common Failure: Pixi Solver Errors

The most frequent issue occurs during environment solving:

```bash
Error: failed to solve environment
```

Or more subtly, a solve may fail only for a particular Python or MPI
combination in the generated manifest.

These often stem from:

* Conflicting dependencies across packages
* Incompatible versions due to partially-completed conda-forge migrations
* A mismatch between recipe selectors, variant expansion, and the final solve

---

## Strategy: Use `pixi_first_failure.py`

To help identify the root cause, E3SM-Unified provides:

```
recipes/e3sm-unified/pixi_first_failure.py
```

This utility performs a Pixi-based solve using a list of dependencies, then
uses bisection to find the first package that causes solver failure.

### Usage

1. Copy the list of dependencies from `recipe.yaml` into a
   text file (e.g., `specs.txt`)

2. Constrain the python version to a single minor version, e.g.:

   ``` yaml
     - python ==3.13
   ```

3. Remove or replace any jinja templating or conflicting selector logic,
   for example:

   * replace `\${{ mpi_prefix }}` with `mpi_mpich` or `nompi`
   * replace `\${{ mpi }}` with a concrete value when needed
   * depending on the python version and variant you are testing, pick only
     the applicable conditional requirements

4. Run the script:

```bash
python3 recipes/e3sm-unified/pixi_first_failure.py specs.txt
```

5. The script will print the **first package** that causes a conflict.

### Interpreting Results

* The failing package might not be the root issue — it may simply conflict
  with another dependency in the list.
* To explore this, move the failing package to the **top** of the list and
  re-run the script. The new failure likely points to a **conflicting pair**.
* Examine the dependencies (via the respective conda-forge feedstocks) of
  the conflicting pair of packages to see if you can understand the conflict.

---

## Advanced Debugging Tips

* Add transitive dependencies to the `specs.txt` file (e.g., if the problem
  might involve `hdf5`, add `libnetcdf`, `netcdf4`, etc.)
* Compare dependency trees using:

```bash
pixi add --manifest-path /tmp/test-pixi.toml <packages>
```

* Inspect the generated Pixi manifest or chosen constraints to make sure they
  match the recipe branch you are testing

---

## When You’re Stuck

As the E3SM-Unified maintainer, you're likely the most experienced person on
the team when it comes to conda-forge packaging and solver behavior.

If the conflict is particularly subtle or deep within upstream packages:

* Dig into transitive dependencies (e.g., `conda-tree` can be useful)
* Inspect recent changes to pinned versions in conda-forge
* Examine dependency metadata from feedstocks

When further help is needed, reach out directly to:

* Other E3SM tool maintainers (e.g., for `e3sm_diags`, `mpas_analysis`, etc.)
* Colleagues with Spack or Conda-forge packaging experience

Ultimately, it’s up to the release engineer to resolve these issues through
investigation, collaboration, or temporary workarounds until a proper fix is
found.
