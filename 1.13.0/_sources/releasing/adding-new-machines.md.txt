# Adding a New Machine

Support for a new HPC machine in E3SM-Unified requires coordinated updates
across multiple tools — primarily in
[`mache`](https://github.com/E3SM-Project/mache), but also in the E3SM Spack
fork and the repository's `deploy/` configuration.

This page provides guidance for E3SM-Unified maintainers and infrastructure
developers integrating new machines into the release and deployment workflow.

---

## 🔗 Main Mache Documentation

Most of the process is already documented in the official `mache` developer
guide:

* [Adding a New Machine](https://docs.e3sm.org/mache/main/developers_guide/adding_new_machine.html)
* [Adding Spack Support](https://docs.e3sm.org/mache/main/developers_guide/spack.html)

Start in `mache` to:

* Add a machine-specific config file (e.g., `pm-cpu.cfg`)
* Add hostname detection logic in `discover.py`
* Create Spack templates for supported compiler/MPI stacks
* Optionally add shell script templates for environment setup

> ⚠️ Machines not listed in the E3SM
  [`config_machines.xml`](https://github.com/E3SM-Project/E3SM/blob/master/cime_config/machines/config_machines.xml) must first be added upstream before `mache`
  can support them.

---

## 🧩 Integration with E3SM-Unified Deployment

After updating `mache`, you'll need to:

1. **Reference your `mache` branch in E3SM-Unified Deployment**

   * Use the `--mache-fork` and `--mache-branch` flags to deploy using the
     updated branch
   * Confirm the new machine is recognized and templates are applied correctly

2. **Update Spack if needed**

   * If new versions of external tools are required, update the
     [`spack_for_mache_<version>`](testing/spack-updates.md) branch of the
     [E3SM Spack fork](https://github.com/E3SM-Project/spack)

---

## ✅ Testing Your Changes

Use the standard test deployment approach from
[Deploying on HPCs](testing/deploying-on-hpcs.md):

```bash
./deploy.py --mache-fork <your_fork> \
    --mache-branch <your_branch>
```
You can also supply these flags:
```
--machine <new_machine>
--compiler <compiler>
--mpi <mpi>
```
but they should not be needed if you have set things up in `mache` correctly.

During testing, focus on:

* Spack external package detection and successful builds
* Shell script generation and activation behavior
* Module compatibility and performance of tools like `zppy` and `e3sm_diags`

---

## 💡 Tips and Best Practices

* Reuse YAML templates from similar machines to minimize effort
* Add common system tools as `buildable: false` in the Spack environment
* Avoid identifying machines using environment variables unless absolutely
  necessary.  Instead use the hostnames for login and compute nodes if
  possible
* Use `utils/update_cime_machine_config.py` to verify `mache` remains in sync
  with E3SM

---

➡ Next: [Publishing the Final Release](finalizing-release.md)
