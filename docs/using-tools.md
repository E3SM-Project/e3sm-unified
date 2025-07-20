# Using Tools in E3SM-Unified

E3SM-Unified includes a suite of powerful tools for analysis, diagnostics,
file manipulation, and more. This page provides quick summaries and links to
documentation to help you get started with some of the most commonly used
tools.

---

## 📈 E3SM Diags

E3SM Diagnostics (E3SM Diags) enables model-vs-observation and model-vs-model
comparisons using a wide array of climatological diagnostics.

- **Core Use Cases**:
  - Climatology comparisons (e.g., model vs. obs, model vs. model)
  - Time series comparisons
  - Diagnostic sets including ENSO, QBO, streamflow, tropical cyclones, and
    more

- **Quickstart**:
  1. Clone or download an
     [example](https://github.com/E3SM-Project/e3sm_diags/tree/master/examples)
     and modify the parameters file
  2. Activate the E3SM-Unified environment on an HPC machine (e.g.,
     Perlmutter):
     ```bash
     source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
     ```
  3. Run with multiprocessing:
     ```bash
     python ex4.py --multiprocessing --num_workers=32 -d diags.cfg
     ```
  4. View output using the generated HTML viewer

- **CMIP Preprocessing** (for time series obs/model comparisons):
  - Rename files to E3SM format: `<variable>_<start_yr>01_<end_yr>12.nc`
  - Place all relevant files in the same directory

- **Visualization Examples**:
  - Latitude-longitude and polar maps
  - Taylor diagrams
  - Pressure-latitude and pressure-longitude slices
  - Time series and zonal mean plots

🔗 [Documentation Hub](https://docs.e3sm.org/e3sm_diags/_build/html/main/index.html)
🔗 [Run Examples](https://docs.e3sm.org/e3sm_diags/_build/html/main/examples.html)
🔗 [Example Output Viewer](https://portal.nersc.gov/cfs/e3sm/forsyth/examples/ex1-model_ts-vs-model_ts/viewer/)

---

## 📐 MOAB

MOAB provides mesh and geometry tools for analysis workflows using unstructured
grids.

Used for working with unstructured meshes and remapping — useful in
preprocessing, remapping or analyzing EAM and MPAS grids.

🔗 [MOAB Documentation](https://sigma.mcs.anl.gov/moab-library/)

---

## 📊 MPAS-Analysis

MPAS-Analysis is used to evaluate MPAS-Ocean and MPAS-Seaice output.

- **Quickstart**:
  - Copy or create a config file (e.g., `myrun.cfg`)
  - Run:
    ```bash
    mpas_analysis myrun.cfg
    ```
  - Optional: use `--purge` to remove old results, or `--generate` to run a
    subset of tasks
- **Parallel runs**: supported via job scripts for common HPC systems
- **Custom plots**: generate new plots using precomputed climatology and time
  series data

🔗 [MPAS-Analysis: Running the Analysis](https://mpas-dev.github.io/MPAS-Analysis/develop/users_guide/quick_start.html#running-the-analysis)
🔗 [Example config files](https://github.com/MPAS-Dev/MPAS-Analysis/tree/develop/configs)

---

## 🧪 NCO

NCO (NetCDF Operators) provides command-line tools for manipulating NetCDF
files.

Includes tools like `ncreamp`, `ncclimo`, `ncks`, `ncra`, `ncrcat`, and
`ncatted` for computing climatologies and extracting time series as well as
remapping, subsetting, concatenating, and editing NetCDF files.

🔗 [NCO Manual](http://nco.sourceforge.net/nco.html)

---

## ⚙️ zppy

[`zppy`](https://github.com/E3SM-Project/zppy) (pronounced *zippee*) is E3SM’s
main post-processing toolchain. It automates key analysis steps like generating
time series, climatologies, and diagnostic plots using **NCO**, **E3SM Diags**,
and **MPAS-Analysis** — especially helpful for long or high-resolution
simulations.

Users control zppy through a single `.cfg` configuration file, specifying:

- Input/output directories
- Model components and time ranges to post-process
- Which analysis tasks to run (e.g., `e3sm_diags`, `mpas_analysis`, `ts`,
  `climo`, etc.)

zppy uses this config to generate and submit batch jobs (via SLURM) with
automatic dependency management.

### Example usage

Copy or create a `.cfg` file (e.g., `post.mysimulation.cfg`) containing task
and data settings.

```bash
zppy -c post.mysimulation.cfg
```

- Post-processed outputs (NetCDF + plots) go in the `output` and `www`
  directories
- Job logs and submission scripts are written under `<output>/post/scripts`
- Each zppy task can be debugged by editing and resubmitting its `.bash` script

### Configuration Highlights

- Supports custom and campaign-specific settings (e.g.,
  `campaign = water_cycle`)
- Each analysis block is defined using `[section]` and `[[subsection]]` syntax
- Works with native-resolution and RRM simulations

🔗 [View the zppy tutorial and examples](https://docs.e3sm.org/zppy/_build/html/main/tutorial.html)

---

## 📦 zstash

[`zstash`](https://github.com/E3SM-Project/zstash) is the
**long-term HPSS archiving** solution used by E3SM to store simulation output
in an efficient and reproducible way.

It is written in Python and designed to be lightweight, fast, and reliable —
emphasizing portability and long-term stability over complex features.

### Key Features

- Archives files into **tarballs** with user-defined max size
- Uses **MD5 checksums** (computed on-the-fly) for both files and tars
- Stores all metadata (paths, sizes, checksums, offsets) in a
  **SQLite database**
- Allows for **selective extraction** of files from tarballs
- Verifies **file integrity** during extraction

### Basic Usage

```bash
# Archive files to HPSS
zstash create --hpss=HPSS_PATH --keep input_dir

# Extract files from archive
zstash extract --hpss=HPSS_PATH --files=FILELIST

# Check archive integrity
zstash check --hpss=HPSS_PATH
```

> For best performance, run `zstash` on **data transfer nodes** (DTNs) of
  supported machines.

### Installation

`zstash` is included in the E3SM-Unified environment on supported HPC systems:

```bash
source /path/to/load_latest_e3sm_unified_<machine>.sh
```

You can also install the latest release manually:

```bash
mamba create -n zstash_env zstash
conda activate zstash_env
```

### Documentation and Tutorials

- 🔗 [Getting started](https://docs.e3sm.org/zstash/_build/html/main/getting_started.html)
- 🔗 [Install via conda](https://docs.e3sm.org/zstash/_build/html/main/getting_started.html#installation-in-a-conda-environment)
- 🔗 [Best practices](https://docs.e3sm.org/zstash/_build/html/main/best_practices.html)
- 🔗 [zstash command usage](https://docs.e3sm.org/zstash/_build/html/main/usage.html)

---

## 🧰 More Tools

Other included tools (e.g., `e3sm_to_cmip`, `mpas_tools`, `pyremap`, `xcdat`)
have documentation hosted on their respective repos or conda-forge feedstocks.

We welcome suggestions for additional summaries and links!
