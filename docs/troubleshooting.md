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

---

### MPI-based Tools Fail on Login Nodes

**Symptom:** Tools like `mpas_analysis` or `nco` crash with MPI errors.

**Cause:** These tools are compiled with system MPI (or launch other tools
that use system MPI) and require execution on compute nodes.

**Solution:** Launch a batch job or an interactive compute session with
`srun`, `salloc` or `qsub`, depending on your machine.

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
