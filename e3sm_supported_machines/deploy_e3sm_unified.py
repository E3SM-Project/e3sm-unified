#!/usr/bin/env python

from __future__ import print_function

import os
import warnings
import sys

try:
    from configparser import ConfigParser
except ImportError:
    from six.moves import configparser
    import six

    if six.PY2:
        ConfigParser = configparser.SafeConfigParser
    else:
        ConfigParser = configparser.ConfigParser

from shared import parse_args, check_call, install_miniconda


def get_config(config_file):
    here = os.path.abspath(os.path.dirname(__file__))
    default_config = os.path.join(here, 'default.cfg')
    config = ConfigParser()
    config.read(default_config)

    if config_file is not None:
        config.read(config_file)

    return config


def get_conda_base(conda_base, config):
    if conda_base is None:
        if config.has_option('e3sm_unified', 'base_path'):
            conda_base = os.path.abspath(os.path.join(
                config.get('e3sm_unified', 'base_path'), 'base'))
        elif 'CONDA_EXE' in os.environ:
            # if this is a test, assume we're the same base as the
            # environment currently active
            conda_exe = os.environ['CONDA_EXE']
            conda_base = os.path.abspath(
                os.path.join(conda_exe, '..', '..'))
            warnings.warn(
                '--conda path not supplied.  Using conda installed at '
                '{}'.format(conda_base))
        else:
            raise ValueError('No conda base provided with --conda and '
                             'none could be inferred.')
    # handle "~" in the path
    conda_base = os.path.abspath(os.path.expanduser(conda_base))
    return conda_base


def bootstrap(activate_install_env, source_path):

    print('Creating the e3sm_unified conda environment')
    bootstrap_command = '{}/bootstrap.py'.format(source_path)
    command = '{}; ' \
              '{} {}'.format(activate_install_env, bootstrap_command,
                             ' '.join(sys.argv[1:]))
    check_call(command)
    sys.exit(0)


def setup_install_env(activate_base, config):
    print('Setting up a conda environment for installing E3SM-Unified')
    mache_version = config.get('e3sm_unified', 'mache')
    commands = '{}; ' \
               'mamba create -y -n temp_e3sm_unified_install ' \
               'progressbar2 jinja2 mache={}'.format(activate_base,
                                                     mache_version)

    check_call(commands)


def remove_install_env(activate_base):
    print('Removing conda environment for installing  E3SM-Unified')
    commands = '{}; ' \
               'conda remove -y --all -n ' \
               'temp_e3sm_unified_install'.format(activate_base)

    check_call(commands)


def main():
    args = parse_args()
    source_path = os.getcwd()

    config = get_config(args.config_file)

    conda_base = get_conda_base(args.conda_base, config)

    base_activation_script = os.path.abspath(
        '{}/etc/profile.d/conda.sh'.format(conda_base))

    activate_base = 'source {}; conda activate'.format(base_activation_script)

    activate_install_env = \
        'source {}; ' \
        'conda activate temp_e3sm_unified_install'.format(
            base_activation_script)

    # install miniconda if needed
    install_miniconda(conda_base, activate_base)

    setup_install_env(activate_base, config)

    bootstrap(activate_install_env, source_path)

    remove_install_env(activate_base)


if __name__ == '__main__':
    main()
