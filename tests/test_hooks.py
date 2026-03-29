import argparse
import configparser
import importlib.util
import logging
from pathlib import Path
import sys

import pytest
from mache.deploy.hooks import DeployContext


def _load_deploy_hooks():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    hooks_path = repo_root / 'deploy' / 'hooks.py'
    spec = importlib.util.spec_from_file_location('e3sm_unified_deploy_hooks', hooks_path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Could not load deploy hooks from {hooks_path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deploy_hooks = _load_deploy_hooks()


def _write_machine_cfg(
    tmp_path: Path,
    *,
    group: str = 'users',
    base_path: str = '/tmp/e3sm-unified',
    compiler: str | None = None,
    mpi: str | None = None,
    use_e3sm_hdf5_netcdf: bool | None = None,
) -> Path:
    lines = [
        '[e3sm_unified]',
        f'group = {group}',
        f'base_path = {base_path}',
    ]
    if compiler is not None:
        lines.append(f'compiler = {compiler}')
    if mpi is not None:
        lines.append(f'mpi = {mpi}')
    if use_e3sm_hdf5_netcdf is not None:
        lines.append(
            'use_e3sm_hdf5_netcdf = '
            f'{"True" if use_e3sm_hdf5_netcdf else "False"}'
        )
    cfg_path = tmp_path / 'machine.cfg'
    cfg_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return cfg_path


def _ctx(
    tmp_path: Path, machine: str | None, machine_cfg_path: Path
) -> DeployContext:
    machine_config = configparser.ConfigParser()
    machine_config.read(machine_cfg_path)
    return DeployContext(
        software='e3sm-unified',
        machine=machine,
        repo_root=str(tmp_path),
        deploy_dir=str(tmp_path / 'deploy'),
        work_dir=str(tmp_path / 'deploy_tmp'),
        config={},
        pins={},
        machine_config=machine_config,
        args=argparse.Namespace(
            e3sm_unified_version='1.2.3',
            package_source='conda-forge',
            package_mpi=None,
            env_layout=None,
            release=False,
            no_spack=False,
            prefix=None,
            spack_path=None,
            spack_tmpdir=None,
            load_script_dir=None,
            quiet=True,
            mache_fork=None,
            mache_branch=None,
        ),
        logger=logging.getLogger(f'test-{machine}'),
    )


def test_pre_pixi_defaults_to_nompi_single_for_pixi_only_machine(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path, group='E3SMinput', base_path='/lus/grand/projects/E3SMinput/soft/e3sm-unified'
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='polaris',
        machine_cfg_path=machine_cfg_path,
    )

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert updates['pixi']['mpi'] == 'nompi'
    assert updates['pixi']['login_prefix'] is None
    assert updates['pixi']['login_mpi'] is None
    assert updates['toolchain'] == {}


def test_pre_spack_skips_when_pixi_only_machine_defaults_to_nompi(
    tmp_path: Path,
):
    machine_cfg_path = _write_machine_cfg(
        tmp_path, group='climate', base_path='/usr/projects/e3sm/e3sm-unified'
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='chicoma-cpu',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})

    updates = deploy_hooks.pre_spack(ctx)

    assert updates == {
        'spack': {
            'deploy': False,
            'supported': False,
            'software': {'supported': False},
        }
    }


def test_pre_pixi_local_build_rc_adds_local_and_dev_channels(
    tmp_path: Path, monkeypatch
):
    machine_cfg_path = _write_machine_cfg(
        tmp_path, group='E3SMinput', base_path='/lus/grand/projects/E3SMinput/soft/e3sm-unified'
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='polaris',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.package_source = 'local-build'
    ctx.args.e3sm_unified_version = '1.13.0rc1'

    built = {}

    def fake_build_local_packages(*, ctx, version, package_mpis):
        built['version'] = version
        built['package_mpis'] = package_mpis

    monkeypatch.setattr(
        deploy_hooks, '_build_local_packages', fake_build_local_packages
    )

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert built == {'version': '1.13.0rc1', 'package_mpis': ['nompi']}
    assert updates['pixi']['channels'][0] == (
        deploy_hooks.LOCAL_CHANNEL_DIR.resolve().as_uri()
    )
    assert 'conda-forge/label/e3sm_unified_dev' in updates['pixi']['channels']
    assert 'conda-forge/label/mache_dev' in updates['pixi']['channels']
    assert updates['pixi']['channels'][-1] == 'conda-forge'


def test_pre_pixi_defaults_to_hpc_dual_for_hpc_machine(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
        use_e3sm_hdf5_netcdf=False,
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert updates['pixi']['mpi'] == 'hpc'
    assert updates['pixi']['login_mpi'] == 'nompi'
    assert updates['pixi']['login_prefix'] is not None
    assert updates['toolchain'] == {'compiler': ['gnu'], 'mpi': ['openmpi']}
    assert updates['permissions'] == {
        'group': 'users',
        'world_readable': True,
    }
    assert updates['e3sm_unified']['env_layout'] == 'dual'


def test_pre_pixi_release_rejects_local_build(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.release = True
    ctx.args.package_source = 'local-build'

    with pytest.raises(
        ValueError, match='--release only supports --package-source conda-forge'
    ):
        deploy_hooks.pre_pixi(ctx)


def test_pre_pixi_release_rejects_mache_overrides(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.release = True
    ctx.args.mache_branch = 'feature-branch'

    with pytest.raises(
        ValueError, match='--release does not support --mache-fork/--mache-branch'
    ):
        deploy_hooks.pre_pixi(ctx)


def test_pre_pixi_hpc_rejects_no_spack(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.no_spack = True
    ctx.args.package_mpi = 'hpc'
    ctx.args.env_layout = 'dual'

    with pytest.raises(
        ValueError, match='hpc package variant cannot be deployed with --no-spack'
    ):
        deploy_hooks.pre_pixi(ctx)


def test_pre_pixi_hpc_requires_dual_layout(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.package_mpi = 'hpc'
    ctx.args.env_layout = 'single'

    with pytest.raises(
        ValueError, match='hpc package variant requires --env-layout dual'
    ):
        deploy_hooks.pre_pixi(ctx)


def test_pre_spack_prefers_cli_path_and_excludes_hdf5_bundle_by_default(
    tmp_path: Path,
):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
        use_e3sm_hdf5_netcdf=False,
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})
    ctx.args.spack_path = '~/custom-spack'
    ctx.config['spack'] = {
        'spack_path': '/should/not/be/used',
        'exclude_packages': ['foo'],
    }

    updates = deploy_hooks.pre_spack(ctx)

    assert updates == {
        'spack': {
            'deploy': True,
            'supported': True,
            'software': {'supported': False},
            'spack_path': str(Path('~/custom-spack').expanduser().resolve()),
            'exclude_packages': ['foo', 'hdf5_netcdf'],
        }
    }


def test_pre_spack_uses_prefix_root_when_no_override_path(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
        use_e3sm_hdf5_netcdf=False,
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})

    updates = deploy_hooks.pre_spack(ctx)

    assert updates == {
        'spack': {
            'deploy': True,
            'supported': True,
            'software': {'supported': False},
            'spack_path': '/share/apps/E3SM/conda_envs/e3smu_1_2_3/compy/spack',
            'exclude_packages': ['hdf5_netcdf'],
        }
    }


def test_pre_spack_skips_hdf5_bundle_exclusion_when_machine_uses_bundle(
    tmp_path: Path,
):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='cli115',
        base_path='/ccs/proj/cli115/software/e3sm-unified',
        compiler='craygnu',
        mpi='mpich',
        use_e3sm_hdf5_netcdf=True,
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='frontier',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})

    updates = deploy_hooks.pre_spack(ctx)

    assert updates == {
        'spack': {
            'deploy': True,
            'supported': True,
            'software': {'supported': False},
            'spack_path': (
                '/ccs/proj/cli115/software/e3sm-unified/'
                'e3smu_1_2_3/frontier/spack'
            ),
        }
    }
