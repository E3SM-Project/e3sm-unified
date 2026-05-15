# How Conda and Spack Work Together in E3SM-Unified

E3SM-Unified uses a hybrid approach that combines Conda and Spack to build
and deploy a comprehensive software environment for E3SM analysis and
diagnostics. This page explains the motivation for this strategy, how the
components interact, and the shared infrastructure that supports both
E3SM-Unified and related projects.

---

## Why Combine Conda and Spack?

Each tool solves a different part of the problem:

### ✅ Conda

* Excellent for managing Python packages and their dependencies
* Supports rapid installation and reproducibility
* Compatible with conda-forge and custom channels (e.g., `e3sm`)
* User-friendly interface, especially for scientists and developers

### ✅ Spack

* Designed for building performance-sensitive HPC software
* Allows fine-grained control over compilers, MPI implementations, and system
  libraries
* Better suited for tools written in Fortran/C/C++ with MPI dependencies
  (e.g., NCO, MOAB, TempestRemap)

### ❗ The Challenge

Neither system alone is sufficient:

* Conda cannot reliably build or run MPI-based binaries across multiple nodes
  on HPC systems. In our experience, Conda's MPI implementations often fail
  even for multi-task jobs on a single node, making them unsuitable for
  high-performance parallel workflows
* Spack lacks strong support for modern Python environments and is generally
  harder to use for scientists accustomed to Conda-based workflows. While
  conda-forge provides access to tens of thousands of Python packages, Spack
  offers far fewer, meaning many familiar scientific tools are not readily
  available through Spack alone

---

## Architecture: How They Work Together

E3SM-Unified environments:

1. Use **Conda** to install the core Python tools and lightweight dependencies
2. Rely on **Spack** to build performance-critical tools outside Conda
3. Are bundled into a single workflow that ensures compatibility across both

System-specific setup scripts (e.g., `load_latest_e3sm_unified_<machine>.sh`)
ensure both components are activated correctly.

For MPI-based tools:

* The tools are built with Spack using system compilers and MPI
* Users automatically access these builds when running on compute nodes

---

## Shared Infrastructure

E3SM-Unified, Polaris, and Compass all rely on the same key components:

* [`mache`](https://github.com/E3SM-Project/mache): A configuration library
  for detecting machine-specific settings (modules, compilers, paths)
* [E3SM's Spack fork](https://github.com/E3SM-Project/spack): Centralized
  control over package versions and build settings
* Conda: Used consistently to install `mache`, lightweight tools, and Python
  dependencies

This shared foundation ensures reproducibility and consistency across
workflows, testbeds, and developer tools in the E3SM ecosystem.

---

## Future Alternatives

As complexity grows, other strategies may be worth evaluating:

### Option: **E4S (Extreme-scale Scientific Software Stack)**

* Spack-based stack of curated HPC tools
* E4S environments aim to replace the need for manual Spack+Conda integration
* May offer better long-term sustainability, but lacks Python focus today

🔗 [Explore E4S](https://e4s.io)

### Other Approaches (less suitable currently):

* Pure Spack builds (harder for Python workflows)
* Pure Conda builds (harder for HPC performance tools)
* Containers (portability gains, but complex for HPC integration)

---

## Summary

The hybrid Conda + Spack model in E3SM-Unified balances ease of use with HPC
performance. While more complex to maintain, it provides flexibility,
compatibility, and performance across diverse systems. Shared infrastructure
(like `mache` and E3SM's Spack fork) reduces duplication across projects and
streamlines the release process.
