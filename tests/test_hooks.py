import argparse
import configparser
import importlib.util
import logging
from pathlib import Path
import sys

import jinja2
import pytest
import yaml
from mache.deploy.hooks import DeployContext
from mache.deploy.spack import _render_spack_specs
from mache.spack.pins import load_pins


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
CURRENT_RECIPE_VERSION = deploy_hooks.get_version_from_recipe(
    deploy_hooks.RECIPE_PATH
)


def _assert_managed_nco_root(updates: dict, nco_root: Path) -> None:
    assert updates is not None
    assert updates['shared']['managed_directories'] == [
        {
            'path': str(nco_root),
            'root_group_writable': True,
        }
    ]


def _write_machine_cfg(
    tmp_path: Path,
    *,
    group: str = 'users',
    base_path: str = '/tmp/e3sm-unified',
    compiler: str | None = None,
    mpi: str | None = None,
    use_e3sm_hdf5_netcdf: bool | None = None,
    use_system_git: bool | None = None,
    use_legacy_glibc_pins: bool | None = None,
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
    if use_system_git is not None:
        lines.append(
            f'use_system_git = {"True" if use_system_git else "False"}'
        )
    if use_legacy_glibc_pins is not None:
        lines.append(
            'use_legacy_glibc_pins = '
            f'{"True" if use_legacy_glibc_pins else "False"}'
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
            pixi_path=None,
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
    assert updates['pixi']['omit_dependencies'] == []
    assert updates['pixi']['extra_dependencies'] == []
    assert updates['toolchain'] == {}


def test_pre_publish_falls_back_to_pixi_prefix_without_login_prefix(
    tmp_path: Path,
):
    base_path = tmp_path / 'e3sm-unified'
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='E3SMinput',
        base_path=str(base_path),
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='polaris',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.release = True
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})
    ctx.runtime['pixi'].pop('login_prefix')

    updates = deploy_hooks.pre_publish(ctx)

    nco_root = base_path / 'e3smu_latest_for_nco'
    machine_link = nco_root / 'polaris'
    _assert_managed_nco_root(updates, nco_root)
    assert machine_link.is_symlink()
    assert machine_link.readlink() == Path(ctx.runtime['pixi']['prefix'])


def test_pre_publish_adds_nco_alias_for_dual_env_release(tmp_path: Path):
    base_path = tmp_path / 'e3sm-unified'
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path=str(base_path),
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.release = True
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})

    updates = deploy_hooks.pre_publish(ctx)

    nco_root = base_path / 'e3smu_latest_for_nco'
    machine_link = nco_root / 'compy'
    _assert_managed_nco_root(updates, nco_root)
    assert machine_link.is_symlink()
    assert machine_link.readlink() == Path(ctx.runtime['pixi']['login_prefix'])


def test_ensure_feedstock_submodule_initializes_missing_recipe(
    tmp_path: Path, monkeypatch
):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='E3SMinput',
        base_path='/lus/grand/projects/E3SMinput/soft/e3sm-unified',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='polaris',
        machine_cfg_path=machine_cfg_path,
    )

    feedstock_dir = tmp_path / 'recipes' / 'e3sm-unified' / 'e3sm-unified-feedstock'
    recipe_path = feedstock_dir / 'recipe' / 'recipe.yaml'
    gitmodules_path = tmp_path / '.gitmodules'
    gitmodules_path.write_text(
        '[submodule "recipes/e3sm-unified/e3sm-unified-feedstock"]\n'
        'path = recipes/e3sm-unified/e3sm-unified-feedstock\n',
        encoding='utf-8',
    )

    monkeypatch.setattr(deploy_hooks, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(deploy_hooks, 'FEEDSTOCK_DIR', feedstock_dir)
    monkeypatch.setattr(deploy_hooks, 'RECIPE_PATH', recipe_path)
    monkeypatch.setattr(deploy_hooks, 'GITMODULES_PATH', gitmodules_path)

    called = {}

    def fake_check_call(cmd, *, log_filename, quiet, cwd, env):
        called['cmd'] = cmd
        called['log_filename'] = log_filename
        called['quiet'] = quiet
        called['cwd'] = cwd
        called['env'] = env
        recipe_path.parent.mkdir(parents=True, exist_ok=True)
        recipe_path.write_text('context:\n  version: "1.13.0rc1"\n', encoding='utf-8')

    monkeypatch.setattr(deploy_hooks, 'check_call', fake_check_call)

    deploy_hooks._ensure_feedstock_submodule(ctx)

    assert called['cmd'] == [
        'git',
        'submodule',
        'update',
        '--init',
        'recipes/e3sm-unified/e3sm-unified-feedstock',
    ]
    assert called['cwd'] == str(tmp_path)
    assert recipe_path.exists()


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
    ctx.args.e3sm_unified_version = CURRENT_RECIPE_VERSION

    built = {}

    def fake_build_local_packages(*, ctx, version, package_mpis):
        built['version'] = version
        built['package_mpis'] = package_mpis

    monkeypatch.setattr(
        deploy_hooks, '_build_local_packages', fake_build_local_packages
    )

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert built == {'version': CURRENT_RECIPE_VERSION, 'package_mpis': ['nompi']}
    assert updates['pixi']['channels'] == [
        deploy_hooks.LOCAL_CHANNEL_DIR.resolve().as_uri(),
        *deploy_hooks.get_base_channels(
            deploy_hooks.RECIPE_PATH, CURRENT_RECIPE_VERSION
        ),
    ]


def test_pre_pixi_explicit_rc_version_must_match_feedstock_recipe(
    tmp_path: Path,
):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='E3SMinput',
        base_path='/lus/grand/projects/E3SMinput/soft/e3sm-unified',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='polaris',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.e3sm_unified_version = '999.0.0rc0'

    with pytest.raises(
        ValueError, match='does not match feedstock recipe version'
    ):
        deploy_hooks.pre_pixi(ctx)


def test_pre_pixi_defaults_to_hpc_dual_for_hpc_machine(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path='/share/apps/E3SM/conda_envs',
        compiler='gnu',
        mpi='openmpi',
        use_e3sm_hdf5_netcdf=False,
        use_system_git=True,
        use_legacy_glibc_pins=True,
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
    assert updates['pixi']['omit_dependencies'] == ['git']
    assert updates['pixi']['extra_dependencies'] == [
        'nodejs = "<22"',
        'sysroot_linux-64 = "2.17.*"',
    ]
    assert updates['toolchain'] == {'compiler': ['gnu'], 'mpi': ['openmpi']}
    assert updates['permissions'] == {
        'group': 'users',
        'world_readable': True,
    }
    assert updates['shared']['base_path'] == (
        '/share/apps/E3SM/conda_envs/e3smu_1_2_3'
    )
    assert updates['e3sm_unified']['env_layout'] == 'dual'


def test_explicit_pixi_path_keeps_deploy_out_of_base_path(tmp_path: Path):
    base_path = tmp_path / 'e3sm-unified'
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path=str(base_path),
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    pixi_path = tmp_path / 'scratch' / 'e3sm-unified-pixi'
    ctx.args.pixi_path = str(pixi_path)

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert updates['pixi']['prefix'] == str(pixi_path)
    assert updates['pixi']['login_prefix'] == f'{pixi_path}_login'
    assert 'base_path' not in updates['shared']
    assert updates['shared']['load_script_copies'] == []
    assert updates['shared']['load_script_symlinks'] == []

    ctx.runtime.update(updates)
    spack_updates = deploy_hooks.pre_spack(ctx)

    assert spack_updates is not None
    assert spack_updates['spack']['spack_path'] == f'{pixi_path}_spack'


def test_explicit_prefix_alias_is_honored(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path=str(tmp_path / 'e3sm-unified'),
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    pixi_path = tmp_path / 'scratch' / 'e3sm-unified-pixi'
    del ctx.args.pixi_path
    ctx.args.prefix = str(pixi_path)

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert updates['pixi']['prefix'] == str(pixi_path)
    assert 'base_path' not in updates['shared']


def test_release_with_explicit_pixi_path_still_publishes_load_scripts(
    tmp_path: Path,
):
    base_path = tmp_path / 'e3sm-unified'
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path=str(base_path),
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.args.release = True
    ctx.args.pixi_path = str(tmp_path / 'scratch' / 'e3sm-unified-pixi')

    updates = deploy_hooks.pre_pixi(ctx)

    assert updates is not None
    assert 'base_path' not in updates['shared']
    assert updates['shared']['load_script_copies'] == [
        str(base_path / 'load_e3sm_unified_1.2.3_compy.sh')
    ]
    assert len(updates['shared']['load_script_symlinks']) == 1


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
    (tmp_path / 'deploy_tmp').mkdir(parents=True, exist_ok=True)
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
    assert ctx.machine_config.getboolean('deploy', 'use_e3sm_hdf5_netcdf') is False


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
    (tmp_path / 'deploy_tmp').mkdir(parents=True, exist_ok=True)
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


def test_config_spack_pins_are_valid():
    config_path = Path(deploy_hooks.REPO_ROOT) / 'deploy' / 'config.yaml.j2'
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))

    pins = load_pins([config['spack'].get('pins') or {}])

    assert set(pins['repos']) == {'e3sm', 'builtin'}


def _hpc_release_ctx(tmp_path: Path, version: str) -> DeployContext:
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path=str(tmp_path / 'e3sm-unified'),
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    (tmp_path / 'deploy_tmp').mkdir(parents=True, exist_ok=True)
    ctx.args.e3sm_unified_version = version
    ctx.args.release = True
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})
    return ctx


@pytest.mark.parametrize('ref', [{'commit': 'abc123'}, {'branch': 'main'}])
def test_pre_spack_release_rejects_untagged_config_pins(
    tmp_path: Path, ref: dict
):
    ctx = _hpc_release_ctx(tmp_path, '1.2.3')
    ctx.config['spack'] = {'pins': {'repos': {'e3sm': ref}}}

    with pytest.raises(ValueError, match='pinned to tags'):
        deploy_hooks.pre_spack(ctx)


def test_pre_spack_release_rejects_untagged_cli_pins(tmp_path: Path):
    ctx = _hpc_release_ctx(tmp_path, '1.2.3')
    pins_path = tmp_path / 'pins.yaml'
    pins_path.write_text(
        'repos:\n  e3sm:\n    commit: abc123\n', encoding='utf-8'
    )
    ctx.args.spack_pins = str(pins_path)

    with pytest.raises(ValueError, match='pinned to tags'):
        deploy_hooks.pre_spack(ctx)


def test_pre_spack_release_accepts_tagged_pins(tmp_path: Path):
    ctx = _hpc_release_ctx(tmp_path, '1.2.3')
    ctx.config['spack'] = {'pins': {'repos': {'e3sm': {'tag': 'v2099.01.0'}}}}

    updates = deploy_hooks.pre_spack(ctx)

    assert updates is not None
    assert updates['spack']['deploy'] is True


def test_pre_spack_allows_untagged_pins_for_test_deployments(tmp_path: Path):
    ctx = _hpc_release_ctx(tmp_path, '1.2.3')
    ctx.runtime['e3sm_unified']['release'] = False
    ctx.config['spack'] = {'pins': {'repos': {'e3sm': {'commit': 'abc123'}}}}

    updates = deploy_hooks.pre_spack(ctx)

    assert updates is not None
    assert updates['spack']['deploy'] is True


def test_post_spack_installs_mpi4py_and_ilamb_without_rewriting_pixi(
    tmp_path: Path, monkeypatch
):
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
    (tmp_path / 'deploy_tmp').mkdir(parents=True, exist_ok=True)
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})
    ctx.pins['hpc'] = {
        'mpi4py': '4.1.1',
        'ilamb': '2.7.3',
        'esmpy': 'None',
        'xesmf': 'None',
    }

    monkeypatch.setattr(
        deploy_hooks,
        '_get_primary_spack_result',
        lambda _ctx: {
            'activation': 'source /tmp/spack/setup-env.sh\nspack env activate test',
            'view_path': '/tmp/spack/view',
        },
    )
    monkeypatch.setattr(
        deploy_hooks,
        '_require_pixi_executable',
        lambda _ctx: '/tmp/pixi',
    )
    monkeypatch.setattr(
        deploy_hooks,
        'build_pixi_shell_hook_prefix',
        lambda *, pixi_exe, pixi_toml: (
            f'eval "$({pixi_exe} shell-hook -s bash -m {pixi_toml})" &&'
        ),
    )

    called: dict[str, object] = {}

    def fake_check_call(cmd, *, log_filename, quiet, env, cwd):
        called['cmd'] = cmd
        called['log_filename'] = log_filename
        called['quiet'] = quiet
        called['env'] = env
        called['cwd'] = cwd

    monkeypatch.setattr(deploy_hooks, 'check_call', fake_check_call)

    deploy_hooks.post_spack(ctx)

    script_path = tmp_path / 'deploy_tmp' / 'post_spack_hpc.sh'
    script_text = script_path.read_text(encoding='utf-8')

    assert called['cmd'] == ['/bin/bash', str(script_path)]
    assert called['cwd'] == str(tmp_path)
    assert 'pixi add --manifest-path' not in script_text
    assert (
        'MPICC="mpicc -shared" python -m pip install '
        '--no-cache-dir --no-binary=mpi4py --no-build-isolation '
        '"mpi4py==4.1.1"'
    ) in script_text
    assert (
        'python -m pip install --no-cache-dir --no-deps '
        '--no-binary=ilamb --no-build-isolation "ilamb==2.7.3"'
    ) in script_text


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
    assert ctx.machine_config.getboolean('deploy', 'use_e3sm_hdf5_netcdf') is True


def test_spack_specs_omit_hdf5_bundle_when_machine_uses_bundle(tmp_path: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='e3sm',
        base_path='/global/common/software/e3sm/anaconda_envs',
        compiler='gnu',
        mpi='mpich',
        use_e3sm_hdf5_netcdf=True,
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='pm-cpu',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})
    deploy_hooks.pre_spack(ctx)

    specs = _render_spack_specs(
        template_path=str(deploy_hooks.REPO_ROOT / 'deploy' / 'spack.yaml.j2'),
        ctx=ctx,
        compiler='gnu',
        mpi='mpich',
        section='library',
        e3sm_hdf5_netcdf=True,
        exclude_packages=set(),
    )

    spec_names = {spec.split('@', 1)[0] for spec in specs}

    assert 'hdf5' not in spec_names
    assert 'netcdf-c' not in spec_names
    assert 'netcdf-fortran' not in spec_names
    assert 'parallel-netcdf' not in spec_names


ENV_TEST_RECIPE = """\
tests:
  - python:
      imports:
        - json
        - if: not (linux and aarch64)
          then: e3sm_compareview
        - if: mpi != "nompi" and mpi != "hpc"
          then: ILAMB
      pip_check: false
  - script:
      - echo ok
      - if: mpi != "hpc"
        then:
          - ncks --help
          - test -f ${PREFIX}/bin/Climatology
"""


def _write_env_test_recipe(tmp_path: Path, text: str = ENV_TEST_RECIPE) -> Path:
    recipe_path = tmp_path / 'recipe.yaml'
    recipe_path.write_text(text, encoding='utf-8')
    return recipe_path


def _linux(machine: str = 'x86_64', **variables) -> dict:
    return {'linux': True, 'aarch64': machine == 'aarch64', **variables}


def test_get_recipe_tests_evaluates_selectors(tmp_path: Path):
    recipe_path = _write_env_test_recipe(tmp_path)

    imports, commands = deploy_hooks.get_recipe_tests(
        recipe_path, _linux(mpi='nompi')
    )
    assert imports == ['json', 'e3sm_compareview']
    assert commands == [
        'echo ok',
        'ncks --help',
        'test -f ${PREFIX}/bin/Climatology',
    ]

    imports, commands = deploy_hooks.get_recipe_tests(
        recipe_path, _linux('aarch64', mpi='openmpi')
    )
    assert imports == ['json', 'ILAMB']

    imports, commands = deploy_hooks.get_recipe_tests(
        recipe_path, _linux(mpi='hpc')
    )
    assert imports == ['json', 'e3sm_compareview']
    assert commands == ['echo ok']


def test_get_recipe_tests_rejects_unknown_selector_variable(tmp_path: Path):
    recipe_path = _write_env_test_recipe(tmp_path)

    with pytest.raises(jinja2.UndefinedError, match='aarch64'):
        deploy_hooks.get_recipe_tests(recipe_path, {'linux': True, 'mpi': 'nompi'})


@pytest.mark.parametrize('mpi', ['nompi', 'hpc', 'mpich', 'openmpi'])
def test_get_recipe_tests_understands_feedstock_selectors(mpi: str):
    variables = {
        **deploy_hooks._get_recipe_platform_variables(),
        'mpi': mpi,
    }

    imports, commands = deploy_hooks.get_recipe_tests(
        deploy_hooks.RECIPE_PATH, variables
    )

    assert 'mache' in imports
    assert commands


def _hpc_publish_ctx(tmp_path: Path, monkeypatch, load_script: Path):
    machine_cfg_path = _write_machine_cfg(
        tmp_path,
        group='users',
        base_path=str(tmp_path / 'e3sm-unified'),
        compiler='gnu',
        mpi='openmpi',
    )
    ctx = _ctx(
        tmp_path=tmp_path,
        machine='compy',
        machine_cfg_path=machine_cfg_path,
    )
    ctx.runtime.update(deploy_hooks.pre_pixi(ctx) or {})
    ctx.runtime['load_scripts'] = [str(load_script)]
    ctx.pins['hpc'] = {
        'mpi4py': '4.1.1',
        'ilamb': '2.7.2',
        'esmpy': 'None',
        'xesmf': 'None',
    }
    monkeypatch.setattr(
        deploy_hooks, 'RECIPE_PATH', _write_env_test_recipe(tmp_path)
    )
    monkeypatch.setattr(
        deploy_hooks,
        '_get_recipe_platform_variables',
        lambda: _linux(),
    )
    return ctx


def test_pre_publish_tests_login_and_compute_envs(tmp_path: Path, monkeypatch):
    load_script = tmp_path / 'load_e3sm_unified_compy.sh'
    ctx = _hpc_publish_ctx(tmp_path, monkeypatch, load_script)

    called = []

    def fake_check_call(cmd, *, log_filename, quiet, env, cwd):
        called.append(cmd)

    monkeypatch.setattr(deploy_hooks, 'check_call', fake_check_call)

    deploy_hooks.pre_publish(ctx)

    script_path = tmp_path / 'deploy_tmp' / 'test_load_e3sm_unified_compy.sh'
    assert called == [['/bin/bash', str(script_path)]]
    script_text = script_path.read_text(encoding='utf-8')
    assert f'source {load_script} || exit 1' in script_text

    hpc_checks = script_text.split('  hpc)\n', 1)[1].split('    ;;', 1)[0]
    assert hpc_checks.splitlines() == [
        """    _check 'python -c "import json"'""",
        """    _check 'python -c "import e3sm_compareview"'""",
        "    _check 'echo ok'",
        "    _check 'ncks --help'",
        "    _check 'test -f ${MACHE_DEPLOY_SPACK_LIBRARY_VIEW}/bin/Climatology'",
        """    _check 'python -c "import mpi4py"'""",
        """    _check 'python -c "import ILAMB"'""",
    ]

    nompi_checks = script_text.split('  nompi)\n', 1)[1].split('    ;;', 1)[0]
    assert nompi_checks.splitlines() == [
        """    _check 'python -c "import json"'""",
        """    _check 'python -c "import e3sm_compareview"'""",
        "    _check 'echo ok'",
        "    _check 'ncks --help'",
        "    _check 'test -f ${CONDA_PREFIX}/bin/Climatology'",
    ]


def test_env_test_script_sources_load_script_by_absolute_path(
    tmp_path: Path, monkeypatch
):
    # mache records load scripts relative to the repo root, but the test
    # script may be rerun by hand from any directory
    ctx = _hpc_publish_ctx(
        tmp_path, monkeypatch, Path('load_e3sm_unified_compy.sh')
    )
    monkeypatch.setattr(
        deploy_hooks, 'check_call', lambda cmd, **kwargs: None
    )

    deploy_hooks.pre_publish(ctx)

    script_path = tmp_path / 'deploy_tmp' / 'test_load_e3sm_unified_compy.sh'
    load_script = tmp_path.resolve() / 'load_e3sm_unified_compy.sh'
    script_text = script_path.read_text(encoding='utf-8')
    assert f'source {load_script} || exit 1' in script_text


def test_pre_publish_skips_env_tests_when_requested(
    tmp_path: Path, monkeypatch
):
    ctx = _hpc_publish_ctx(tmp_path, monkeypatch, tmp_path / 'load.sh')
    ctx.args.skip_env_tests = True

    def fail_check_call(*args, **kwargs):
        raise AssertionError('environment tests should be skipped')

    monkeypatch.setattr(deploy_hooks, 'check_call', fail_check_call)

    deploy_hooks.pre_publish(ctx)

    assert not list((tmp_path / 'deploy_tmp').glob('test_*.sh'))


def _write_fake_load_script(tmp_path: Path, mpi: str) -> Path:
    conda_prefix = tmp_path / 'env'
    (conda_prefix / 'bin').mkdir(parents=True, exist_ok=True)
    load_script = tmp_path / 'load_fake.sh'
    load_script.write_text(
        f'export PATH="{Path(sys.executable).parent}:$PATH"\n'
        f'export CONDA_PREFIX="{conda_prefix}"\n'
        'export MACHE_DEPLOY_ACTIVE_ENV_KIND=login\n'
        f'export MACHE_DEPLOY_ACTIVE_PIXI_MPI={mpi}\n',
        encoding='utf-8',
    )
    return load_script


def _single_env_publish_ctx(tmp_path: Path, monkeypatch, recipe: str):
    ctx = _hpc_publish_ctx(
        tmp_path, monkeypatch, _write_fake_load_script(tmp_path, 'nompi')
    )
    ctx.runtime['pixi']['mpi'] = 'nompi'
    ctx.runtime['pixi']['login_mpi'] = None
    monkeypatch.setattr(
        deploy_hooks, 'RECIPE_PATH', _write_env_test_recipe(tmp_path, recipe)
    )
    (tmp_path / 'deploy_tmp' / 'logs').mkdir(parents=True, exist_ok=True)
    return ctx


def test_env_test_script_passes_in_a_working_env(tmp_path: Path, monkeypatch):
    ctx = _single_env_publish_ctx(
        tmp_path,
        monkeypatch,
        'tests:\n'
        '  - python:\n'
        '      imports: [json]\n'
        '  - script:\n'
        '      - test -f ${PREFIX}/bin/Climatology\n'
        '      - touch written-by-a-test\n',
    )
    (tmp_path / 'env' / 'bin' / 'Climatology').touch()

    deploy_hooks.pre_publish(ctx)

    log_text = (tmp_path / 'deploy_tmp' / 'logs' / 'mache_deploy_run.log').read_text()
    assert 'Testing the login environment (nompi)' in log_text
    assert '  PASS: test -f ${CONDA_PREFIX}/bin/Climatology' in log_text
    assert 'All tests passed' in log_text
    assert not (tmp_path / 'written-by-a-test').exists()


def test_env_test_script_reports_every_failure(tmp_path: Path, monkeypatch):
    ctx = _single_env_publish_ctx(
        tmp_path,
        monkeypatch,
        'tests:\n'
        '  - python:\n'
        '      imports: [json, not_a_real_module]\n'
        '  - script:\n'
        '      - test -f ${PREFIX}/bin/Climatology\n',
    )

    with pytest.raises(ValueError, match='Nothing has been published'):
        deploy_hooks.pre_publish(ctx)

    log_text = (tmp_path / 'deploy_tmp' / 'logs' / 'mache_deploy_run.log').read_text()
    assert '''  PASS: python -c "import json"''' in log_text
    assert '''  FAIL: python -c "import not_a_real_module"''' in log_text
    assert "No module named 'not_a_real_module'" in log_text
    assert '  FAIL: test -f ${CONDA_PREFIX}/bin/Climatology' in log_text
    assert '2 test(s) failed' in log_text
