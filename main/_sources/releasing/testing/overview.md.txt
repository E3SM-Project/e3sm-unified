# Deployment and Testing Overview

Once a release candidate (RC) of E3SM-Unified has been successfully built, it
must be thoroughly tested across supported HPC systems before a full release
can occur. This phase ensures compatibility with system modules,
performance-critical tools, and real-world analysis workflows.

This section documents the full testing and deployment process, including how
to:

* Update the E3SM Spack fork to support new versions
* Maintain and release new versions of `mache` for system-specific Spack
  configurations
* Deploy RCs and full releases of E3SM-Unified on supported HPC platforms
* Identify and resolve deployment issues

---

## Phased Deployment Strategy

Testing typically begins with a **partial deployment** of an E3SM-Unified RC
to a few key HPC systems. Once core functionality and package compatibility
are verified, a **full deployment** to all supported machines is performed.

Each iteration involves collaboration between the Infrastructure Team and tool
maintainers to:

* Validate that tools like `zppy`, `e3sm_diags`, and `mpas-analysis` run
  correctly
* Confirm compatibility with system MPI, compilers, and Python versions
* Identify mismatches or conflicts in environment resolution

---

## Key Components of the Deployment Process

The following steps and infrastructure are used when testing and deploying a
new release:

### 🛠️ [Updating the E3SM Spack Fork](spack-updates.md)

* Add new versions of performance-critical tools (e.g., NCO, ESMF, MOAB)
* Create `spack_for_mache_<version>` branches for use in `mache`

### 🧩 [Updating `mache`](mache-updates.md)

* Keep system-specific Spack environment templates in sync with E3SM module
  stacks
* Create RC and final releases of `mache`
* Use `utils/update_cime_machine_config.py` to streamline updates

### 🚀 [Deploying on HPCs](deploying-on-hpcs.md)

* Use the `deploy_e3sm_unified.py` script and template infrastructure in
  `e3sm_supported_machines`
* Build environments and activation scripts tailored to each system

### 🧪 [Troubleshooting Deployment Issues](troubleshooting-deploy.md)

* Resolve Spack build failures and MPI/compiler mismatches
* Address problems with activation, modules, or symbolic links
* Common pitfalls in `default.cfg` or `shared.py` configuration

---

## Audience

This section is primarily intended for E3SM-Unified maintainers and release
engineers. Familiarity with Spack, Conda, and HPC system environments is
assumed.

➡ Start with: [Updating the E3SM Spack Fork](spack-updates.md)
