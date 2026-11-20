# Troubleshooting & FAQs

This page collects common problems users encounter when working with
E3SM-Unified and how to resolve them. If you encounter an issue not listed
here, please reach out via Slack or GitHub.

---

## Common Issues

### "Permission Denied" When Installing E3SM-Unified

**Symptom:**

```
OSError(13, 'Permission denied')
```

**Cause:** You're likely trying to install E3SM-Unified into a system-wide
Python or Conda environment you don't have write access to.

**Solution:**
Install Miniforge3 in your home directory and create an environment locally,
see [Quickstart Guide](quickstart.md).

---

### "Module Not Found" When Importing Packages

**Symptom:**

```python
ModuleNotFoundError: No module named 'e3sm_diags'
```

**Cause:** E3SM-Unified may not be activated correctly, or you're in a
different shell/session.

**Solution:**
Re-source the appropriate `load_latest_e3sm_unified_<machine>.sh` script and
retry.

If you installed E3SM-Unified locally, confirm that your active environment
contains the package:

```bash
conda list e3sm-unified
```

---

### MPI-based Tools Fail on Login Nodes

**Symptom:** Tools like `mpas_analysis` or `nco` crash with MPI errors.

**Cause:** These tools may require the `hpc` package variant or another
MPI-enabled stack that is intended for compute nodes.

**Solution:** Launch a batch job or an interactive compute session with
`srun`, `salloc` or `qsub`, depending on your machine.

If you are on an HPC machine, confirm the active deployment mode:

```bash
echo "$E3SMU_MPI"
```

If this prints `NOMPI` on a compute node, the load script may have selected
the login environment instead of the compute-node environment.

---

### Local Install Solves to the Wrong Package Variant

**Symptom:** You expected MPI-enabled tools but installed the default package,
or a command like
`conda create ... "e3sm-unified=*=mpi_mpich_*"` fails to solve or installs an
old version.

**Cause:** Conda-forge MPI variants (`mpich` and `openmpi`) were last published
for E3SM-Unified 1.12.0. Starting with 1.13.0, only the `nompi` and `hpc`
variants are built, because `e3sm_diags` requires the `nompi` build of `esmf`
([e3sm_diags#1051](https://github.com/E3SM-Project/e3sm_diags/issues/1051)).

**Solution:** For local installs, use the default `nompi` variant:

```bash
conda create -n e3sm-unified -c conda-forge python=3.13 e3sm-unified
```

For MPI-enabled tools on an HPC machine, use the shared E3SM-Unified deployment
on a compute node, where the `hpc` variant uses the system MPI.

---

## Tips & Best Practices

* Always check you're in the correct conda environment.
* On HPC systems, prefer running MPI-enabled tools on compute nodes.
* If installing locally, make sure have create a clean environment with the
  latest version of E3SM-Unified.
* Refer to the [Quickstart Guide](quickstart.md) for environment setup
  instructions.

---

## Still Need Help?

```{admonition} Support
- Slack: #e3sm-help-postproc
- GitHub Issues: [E3SM-Unified on GitHub](https://github.com/E3SM-Project/e3sm-unified/issues)
- Email: xylar@lanl.gov
```
