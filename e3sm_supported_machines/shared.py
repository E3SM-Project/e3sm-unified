import sys
import argparse
import subprocess
import os
import platform
import warnings

try:
    from urllib.request import urlopen, Request
except ImportError:
    # For Python 2 compatibility
    from urllib2 import urlopen, Request

LABELS = {
     "chemdyg": "chemdyg_dev",
     "e3sm_diags": "e3sm_diags_dev",
     "e3sm_to_cmip": "e3sm_to_cmip_dev",
     "mache": "mache_dev",
     "moab": "moab_dev",
     "mpas-analysis": "mpas_analysis_dev",
     "mpas_tools": "mpas_tools_dev",
     "nco": "nco_dev",
     "xcdat": "xcdat_dev",
     "zppy": "zppy_dev",
     "zppy-interfaces": "zppy_interfaces_dev",
     "zstash": "zstash_dev",
}


def parse_args(bootstrap):
    parser = argparse.ArgumentParser(
        description='Deploy E3SM-Unified')
    parser.add_argument("--version", dest="version",
                        help="The version of E3SM-Unified to deploy")
    parser.add_argument("--conda", dest="conda_base",
                        help="Path for the  conda base")
    parser.add_argument("-m", "--machine", dest="machine",
                        help="The name of the machine for loading machine-"
                             "related config options")
    parser.add_argument("-p", "--python", dest="python", type=str,
                        help="The python version to deploy")
    parser.add_argument("-i", "--mpi", dest="mpi", type=str,
                        help="The MPI library (nompi, mpich, openmpi or a "
                             "system flavor) to deploy")
    parser.add_argument("-c", "--compiler", dest="compiler", type=str,
                        help="The name of the compiler")
    parser.add_argument("--recreate", dest="recreate", action='store_true',
                        help="Recreate the environment if it exists")
    parser.add_argument("-f", "--config_file", dest="config_file",
                        help="Config file to override deployment config "
                             "options")
    parser.add_argument("--release", dest="release", action='store_true',
                        help="Indicates that this is a release, not a test, "
                             "build")
    parser.add_argument("--use_local", dest="use_local", action='store_true',
                        help="Use locally built conda packages (for testing).")
    parser.add_argument("--tmpdir", dest="tmpdir",
                        help="A temporary directory for building spack "
                             "packages")
    if bootstrap:
        parser.add_argument("--local_conda_build", dest="local_conda_build",
                            type=str,
                            help="A path for conda packages (for testing).")
    parser.add_argument("--mache_fork", dest="mache_fork",
                        help="Point to a mache fork (and branch) for testing")
    parser.add_argument("--mache_branch", dest="mache_branch",
                        help="Point to a mache branch (and fork) for testing")

    args = parser.parse_args(sys.argv[1:])

    if (args.mache_fork is None) != (args.mache_branch is None):
        raise ValueError('You must supply both or neither of '
                         '--mache_fork and --mache_branch')

    if args.version is None:
        meta_yaml_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "recipes",
            "e3sm-unified",
            "meta.yaml"
        )
        args.version = get_version_from_meta(meta_yaml_path)

    return args


def check_call(commands, env=None):
    print_command = '\n  '.join(commands.split(' && '))
    print(f'\n\nrunning:\n  {print_command}\n\n')
    proc = subprocess.Popen(commands, env=env, executable='/bin/bash',
                            shell=True)
    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, commands)


def install_miniforge3(conda_base, activate_base):
    if not os.path.exists(conda_base):
        print('Installing Miniforge3')
        if platform.system() == 'Linux':
            system = 'Linux'
        elif platform.system() == 'Darwin':
            system = 'MacOSX'
        else:
            system = 'Linux'
        miniforge = f'Miniforge3-{system}-x86_64.sh'
        url = f'https://github.com/conda-forge/miniforge/releases/latest/download/{miniforge}'  # noqa: E501
        print(url)
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        f = urlopen(req)
        html = f.read()
        with open(miniforge, 'wb') as outfile:
            outfile.write(html)
        f.close()

        command = f'/bin/bash {miniforge} -b -p {conda_base}'
        check_call(command)
        os.remove(miniforge)

    print('Doing initial setup\n')
    commands = f'{activate_base} && ' \
               f'conda config --add channels conda-forge && ' \
               f'conda config --set channel_priority strict && ' \
               f'conda update -y --all && ' \
               f'conda init --no-user'

    check_call(commands)


def get_base(config, version):
    """
    Get the base path for E3SM-Unified conda and spack installation
    """
    base_path = config.get('e3sm_unified', 'base_path')
    subdir = f'e3smu_{version}'.replace('.', '_')
    base_path = os.path.join(base_path, subdir)
    return base_path


def get_conda_base(conda_base, config, version, shared, machine=None):
    if shared:
        base_path = get_base(config, version)
        if machine is None:
            raise ValueError(
                "Machine must be specified for shared conda base"
            )
        conda_base = os.path.join(base_path, machine, 'conda')
    elif conda_base is None:
        if 'CONDA_EXE' in os.environ:
            # if this is a test, assume we're the same base as the
            # environment currently active
            conda_exe = os.environ['CONDA_EXE']
            conda_base = os.path.abspath(
                os.path.join(conda_exe, '..', '..'))
            warnings.warn(
                f'--conda path not supplied.  Using conda installed at '
                f'{conda_base}')
        else:
            raise ValueError('No conda base provided with --conda and '
                             'none could be inferred.')
    # handle "~" in the path
    conda_base = os.path.abspath(os.path.expanduser(conda_base))
    return conda_base


def get_rc_dev_labels(meta_yaml_path):
    """Parse meta.yaml and return a list of dev labels for RC dependencies."""

    # a rare case where module-level imports are not a good idea because
    # the deploy_e3sm_unified.py script may be called from an environment
    # where jinja2 and yaml are not installed.
    import yaml
    from jinja2 import Template

    labels_dict = LABELS

    # Render the jinja template with dummy/default values
    with open(meta_yaml_path) as f:
        template_text = f.read()
    # Provide dummy/default values for all jinja variables used in meta.yaml
    template = Template(template_text)
    rendered = template.render(
        mpi='mpich',  # or any valid value
        py='310',     # or any valid value
        CONDA_PY='310',  # used in build string
    )
    meta = yaml.safe_load(rendered)
    dev_labels = []
    run_reqs = meta.get("requirements", {}).get("run", [])
    for req in run_reqs:
        # req can be a string like "pkgname version" or just "pkgname"
        if isinstance(req, str):
            parts = req.split()
            pkg = parts[0]
            version = " ".join(parts[1:]) if len(parts) > 1 else ""

            # NCO is special: it has a dev label for alpha/beta versions
            if pkg == "nco" and ('alpha' in version or 'beta' in version):
                label = labels_dict[pkg]
                if label not in dev_labels:
                    dev_labels.append(label)

            # Only match 'rc' in version, not in pkg name
            if "rc" in version and pkg in labels_dict:
                label = labels_dict[pkg]
                if label not in dev_labels:
                    dev_labels.append(label)
    return dev_labels


def get_version_from_meta(meta_yaml_path):
    """Parse the version from the {% set version = ... %} line in meta.yaml."""
    with open(meta_yaml_path) as f:
        for line in f:
            if line.strip().startswith("{% set version"):
                # e.g., {% set version = "1.11.1rc1" %}
                parts = line.split("=")
                if len(parts) >= 2:
                    version = (
                        parts[1].strip().strip('%}').strip().strip(
                            '"').strip("'")
                    )
                    return version
    raise ValueError("Could not find version in meta.yaml")
