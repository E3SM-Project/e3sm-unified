# Overview of the Workflow

The release process typically follows this progression:

1. **[How Conda and Spack Work Together in E3SM-Unified](conda-vs-spack.md)**
2. **[Planning Package Updates](planning-updates.md)**
3. **[Creating Release Candidates](creating-rcs/overview.md)**
4. **[Deployment and Testing](testing/overview.md)**
5. **[Adding a New Machine](adding-new-machines.md)**
6. **[Finalizing the Release](finalizing-release.md)**
7. **[Maintaining Past Versionse](maintaining-past-versions.md)**

Each of these steps is detailed in its own page. See below for a high-level
summary.

---

## 1. How Conda and Spack Work Together in E3SM-Unified

Why does E3SM-Unified use both Conda and Spack? What roles do they each serve?
Before you start, it's critical to understand how these two systems work
together.

🔗 [Read more](conda-vs-spack.md)

---

## 2. Planning Package Updates

Updates are driven by the needs of the E3SM community, typically discussed via
Confluence or GitHub. This step documents how to propose new packages or
changes to existing ones.

🔗 [Read more](planning-updates.md)

---

## 3. Creating Release Candidates

This step covers:

* Making RCs for core tools (e.g., E3SM Diags, MPAS-Analysis, zppy)
* Building an `e3sm-unified` RC

🔗 [Read more](creating-rcs/overview.md)

---

## 4. Deploying and Testing on HPCs

Before full deployment, release candidates are installed on a subset of HPC
platforms for iterative testing and validation. This stage often requires
extensive coordination and may involve debugging and extending the Spack build
workflow, updating the E3SM Spack fork, and modifying `mache` to support new
systems or changes in machine configurations.

Testing includes everything from basic imports to full `zppy` workflows. This
is a collaborative effort, with the full iterative process often spanning
several weeks to a few months.

🔗 [Read more](testing/overview.md)

---

## 5. Adding a New Machine

Most of the work for adding a new machine takes place in `mache`. Here we
provide notes on adding new HPCs that are specific to E3SM-Unified.

🔗 [Read more](adding-new-machines.md)

---

## 6. Finalizing the Release

Once all RCs pass testing:

* Make final releases of all dependencies
* Publish the final E3SM-Unified conda package
* Deploy across all supported HPC machines
* Announce the release to the community

🔗 [Read more](finalizing-release.md)

---

## 7. Maintaining Past Versions

Older versions of E3SM-Unified sometimes require maintenance (repairs or
deletion).

🔗 [Read more](maintaining-past-versions.md)
