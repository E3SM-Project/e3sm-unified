import argparse
import configparser
import importlib.util
import logging
from pathlib import Path
import sys

import pytest
from mache.deploy.hooks import DeployContext
from mache.deploy.spack import _render_spack_specs


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
    assert updates['pixi']['omit_dependencies'] == []
    assert updates['pixi']['extra_dependencies'] == []
    assert updates['toolchain'] == {}


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
