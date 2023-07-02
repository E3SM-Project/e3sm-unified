#!/usr/bin/env python3

from __future__ import print_function

import os
import sys

from configparser import ConfigParser

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
    bootstrap_command = f'{source_path}/bootstrap.py'
    joined_args = ' '.join(sys.argv[1:])
    command = f'{activate_install_env} && ' \
              f'{bootstrap_command} {joined_args}'
    if local_conda_build is not None:
        command = f'{command} --local_conda_build {local_conda_build}'
    check_call(command)
    sys.exit(0)


def setup_install_env(activate_base, config, use_local):
    print('Setting up a conda environment for installing E3SM-Unified')
    mache_version = config.get('e3sm_unified', 'mache')
    channels = []
    if use_local:
        channels.append('--use-local')
    if 'rc' in mache_version:
        channels.append('-c conda-forge/label/mache_dev')
    channels = ' '.join(channels)
    commands = f'{activate_base} && ' \
               f'mamba create -y -n temp_e3sm_unified_install ' \
               f'{channels} progressbar2 jinja2 mache={mache_version}'

    check_call(commands)


def remove_install_env(activate_base):
    print('Removing conda environment for installing  E3SM-Unified')
    commands = f'{activate_base} && ' \
               f'conda remove -y --all -n ' \
               f'temp_e3sm_unified_install'

    check_call(commands)


def main():
    args = parse_args(bootstrap=False)
    source_path = os.getcwd()

    config = get_config(args.config_file)

    conda_base = get_conda_base(args.conda_base, config, shared=False)
    conda_base = os.path.abspath(conda_base)

    source_activation_scripts = \
        f'source {conda_base}/etc/profile.d/conda.sh && ' \
        f'source {conda_base}/etc/profile.d/mamba.sh'

    activate_base = f'{source_activation_scripts} && conda activate'

    activate_install_env = \
        f'{source_activation_scripts} && ' \
        f'conda activate temp_e3sm_unified_install'

    # install miniconda if needed
    install_miniconda(conda_base, activate_base)

    setup_install_env(activate_base, config, args.use_local)

    if args.release:
        is_test = False
    else:
        is_test = not config.getboolean('e3sm_unified', 'release')

    if is_test and args.use_local:
        local_conda_build = os.path.abspath(f'{conda_base}/conda-bld')
    else:
        local_conda_build = None

    bootstrap(activate_install_env, source_path, local_conda_build)

    remove_install_env(activate_base)


if __name__ == '__main__':
    main()
