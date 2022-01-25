#!/usr/bin/env python

from __future__ import print_function

import os
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

from shared import parse_args, check_call, install_miniconda, get_conda_base


def get_config(config_file):
    here = os.path.abspath(os.path.dirname(__file__))
    default_config = os.path.join(here, 'default.cfg')
    config = ConfigParser()
    config.read(default_config)

    if config_file is not None:
        config.read(config_file)

    return config


def bootstrap(activate_install_env, source_path, local_conda_build):

    print('Creating the e3sm_unified conda environment')
    bootstrap_command = '{}/bootstrap.py'.format(source_path)
    command = '{}; ' \
              '{} {}'.format(activate_install_env, bootstrap_command,
                             ' '.join(sys.argv[1:]))
    if local_conda_build is not None:
        command = '{} --local_conda_build {}'.format(command,
                                                     local_conda_build)
    check_call(command)
    sys.exit(0)


def setup_install_env(activate_base, config, use_local):
    print('Setting up a conda environment for installing E3SM-Unified')
    mache_version = config.get('e3sm_unified', 'mache')
    channels = []
    if use_local:
        channels.append('--use-local')
    if 'rc' in mache_version:
        channels.append('-c conda-forge/label/e3sm_dev')
    channels = ' '.join(channels)
    commands = '{}; ' \
               'mamba create -y -n temp_e3sm_unified_install ' \
               '{} progressbar2 jinja2 mache={}'.format(activate_base,
                                                        channels,
                                                        mache_version)

    check_call(commands)


def remove_install_env(activate_base):
    print('Removing conda environment for installing  E3SM-Unified')
    commands = '{}; ' \
               'conda remove -y --all -n ' \
               'temp_e3sm_unified_install'.format(activate_base)

    check_call(commands)


def main():
    args = parse_args(bootstrap=False)
    source_path = os.getcwd()

    config = get_config(args.config_file)

    conda_base = get_conda_base(args.conda_base, config, shared=False)

    base_activation_script = os.path.abspath(
        '{}/etc/profile.d/conda.sh'.format(conda_base))

    activate_base = 'source {}; conda activate'.format(base_activation_script)

    activate_install_env = \
        'source {}; ' \
        'conda activate temp_e3sm_unified_install'.format(
            base_activation_script)

    # install miniconda if needed
    install_miniconda(conda_base, activate_base)

    setup_install_env(activate_base, config, args.use_local)

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('e3sm_unified', 'release')

    if is_test and args.use_local:
        local_conda_build = os.path.abspath('{}/conda-bld'.format(conda_base))
    else:
        local_conda_build = None

    bootstrap(activate_install_env, source_path, local_conda_build)

    remove_install_env(activate_base)


if __name__ == '__main__':
    main()
