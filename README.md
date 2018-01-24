# e3sm-unified

A metapackage for a unified anaconda environment for analysis of results from
the Energy Exascale Earth System Model (E3SM).

To install the metapackage with x-windows support under UV-CDAT, use:
```
conda install -c conda-forge -c e3sm -c acme -c uvcdat e3sm-unified
```
To install without x-windows, use:
```
conda install -c conda-forge -c e3sm -c acme -c uvcdat e3sm-unified mesalib
```

Note: UV-CDAT's version of VTK automatically installs an older version of `six`
that overwrites the newer version required by many other packages.  Similarly,
the `gcc` package downgrades `libstdcxx`, in conflict with several related
packages.  To overcome these issues, it is currently necessary to force a
reinstall of 4 packages once e3sm-unified has been installed:
```
conda install -y --force -c conda-forge six libgcc libgcc-ng libstdcxx-ng
```
