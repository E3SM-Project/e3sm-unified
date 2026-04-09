"""Deployment hooks for the E3SM-Unified mache.deploy workflow."""

from __future__ import annotations

import importlib.util
import os
import platform
import shlex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from mache.deploy.bootstrap import (
    build_pixi_env,
    build_pixi_shell_hook_prefix,
    check_call,
)

if TYPE_CHECKING:
    from mache.deploy.hooks import DeployContext


REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_HELPERS = REPO_ROOT / 'e3sm_unified_shared.py'
FEEDSTOCK_DIR = (
    REPO_ROOT / 'recipes' / 'e3sm-unified' / 'e3sm-unified-feedstock'
)
RECIPE_PATH = FEEDSTOCK_DIR / 'recipe' / 'recipe.yaml'
CI_SUPPORT_DIR = FEEDSTOCK_DIR / '.ci_support'
GITMODULES_PATH = REPO_ROOT / '.gitmodules'
LOCAL_CHANNEL_DIR = REPO_ROOT / 'deploy_tmp' / 'local-channel'
VARIANT_OVERRIDE_DIR = REPO_ROOT / 'deploy_tmp' / 'variant_overrides'
SOURCE_BUILD_DIR = REPO_ROOT / 'deploy_tmp' / 'hpc-source-builds'


def _load_shared_helpers():
    spec = importlib.util.spec_from_file_location(
        'e3sm_unified_deploy_shared',
        SHARED_HELPERS,
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f'Could not load shared helpers from {SHARED_HELPERS}'
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_shared = _load_shared_helpers()
get_base_channels = _shared.get_base_channels
get_version_from_recipe = _shared.get_version_from_recipe


def pre_pixi(ctx: DeployContext) -> dict[str, Any] | None:
    _ensure_feedstock_submodule(ctx)
    version = _get_version(ctx)
    if not version.strip():
        raise ValueError('Resolved an empty E3SM-Unified version.')
    release = bool(getattr(ctx.args, 'release', False))
    package_source = _get_package_source(ctx)
    package_mpi = _get_package_mpi(ctx)
    env_layout = _get_env_layout(ctx)
    use_system_git = bool(
        _get_machine_bool_option(
            ctx=ctx, section='e3sm_unified', option='use_system_git'
        )
    )
    use_legacy_glibc_pins = bool(
        _get_machine_bool_option(
            ctx=ctx,
            section='e3sm_unified',
            option='use_legacy_glibc_pins',
        )
    )
    permissions = _get_permissions_runtime(ctx)
    toolchain = _get_toolchain_runtime(ctx)
    shared = _get_shared_load_script_runtime(
        ctx=ctx,
        version=version,
        release=release,
    )

    ctx.logger.info(
        'Resolved e3sm-unified version=%s package_source=%s package_mpi=%s '
        'env_layout=%s',
        version,
        package_source,
        package_mpi,
        env_layout,
    )

    if release:
        if ctx.machine is None:
            raise ValueError('Release deployment requires a known machine.')
        if package_source != 'conda-forge':
            raise ValueError(
                '--release only supports --package-source conda-forge.'
            )
        if getattr(ctx.args, 'mache_fork', None) or getattr(
            ctx.args, 'mache_branch', None
        ):
            raise ValueError(
                '--release does not support --mache-fork/--mache-branch.'
            )

    if package_mpi == 'hpc':
        if ctx.machine is None:
            raise ValueError(
                'The hpc package variant requires a known machine.'
            )
        if getattr(ctx.args, 'no_spack', False):
            raise ValueError(
                'The hpc package variant cannot be deployed with --no-spack.'
            )
        if env_layout != 'dual':
            raise ValueError(
                'The hpc package variant requires --env-layout dual.'
            )

    channels = get_base_channels(RECIPE_PATH, version)
    if package_source == 'local-build':
        package_mpis = [package_mpi]
        if env_layout == 'dual' and package_mpi != 'nompi':
            package_mpis = ['nompi', package_mpi]
        _build_local_packages(
            ctx=ctx,
            version=version,
            package_mpis=package_mpis,
        )
        channels = [LOCAL_CHANNEL_DIR.resolve().as_uri(), *channels]

    prefix, login_prefix = _get_pixi_prefixes(
        ctx=ctx,
        version=version,
        release=release,
        package_mpi=package_mpi,
        env_layout=env_layout,
    )
    omit_dependencies: list[str] = []
    if use_system_git:
        omit_dependencies.append('git')
    extra_dependencies: list[str] = []
    if use_legacy_glibc_pins:
        # Compy runs an older OS stack with glibc 2.17, so we pin the
        # transitive toolchain/sysroot and nodejs dependencies to compatible
        # builds when solving the pixi environment.
        extra_dependencies.extend(
            [
                'nodejs = "<22"',
                'sysroot_linux-64 = "2.17.*"',
            ]
        )

    return {
        'project': {'version': version},
        'pixi': {
            'prefix': prefix,
            'login_prefix': login_prefix,
            'login_mpi': 'nompi' if env_layout == 'dual' else None,
            'mpi': package_mpi,
            'channels': channels,
            'omit_dependencies': omit_dependencies,
            'extra_dependencies': extra_dependencies,
        },
        'permissions': permissions,
        'shared': shared,
        'toolchain': toolchain,
        'e3sm_unified': {
            'release': release,
            'package_source': package_source,
            'env_layout': env_layout,
        },
    }


def pre_spack(ctx: DeployContext) -> dict[str, Any] | None:
    package_mpi = _get_runtime_pixi_value(ctx, 'mpi')
    if package_mpi != 'hpc':
        return {
            'spack': {
                'deploy': False,
                'supported': False,
                'software': {'supported': False},
            }
        }

    _sync_e3sm_unified_spack_machine_options(machine_config=ctx.machine_config)

    spack_path = _resolve_spack_path(ctx)
    if spack_path is None:
        raise ValueError(
            'No Spack checkout path could be resolved for the hpc package '
            'variant. Set [e3sm_unified] base_path or [deploy] spack in '
            'machine config, set spack.spack_path in deploy/config.yaml.j2, '
            'or pass --spack-path.'
        )

    updates: dict[str, Any] = {
        'spack': {
            'deploy': True,
            'supported': True,
            'software': {'supported': False},
            'spack_path': spack_path,
        }
    }

    exclude_packages = _get_spack_exclude_packages(ctx)
    _maybe_exclude_e3sm_hdf5_netcdf(
        exclude_packages=exclude_packages, machine_config=ctx.machine_config
    )
    if exclude_packages:
        updates['spack']['exclude_packages'] = exclude_packages

    spack_tmpdir = getattr(ctx.args, 'spack_tmpdir', None)
    if spack_tmpdir:
        updates['spack']['tmpdir'] = spack_tmpdir

    return updates


def post_spack(ctx: DeployContext) -> None:
    if _get_runtime_pixi_value(ctx, 'mpi') != 'hpc':
        return

    spack_result = _get_primary_spack_result(ctx)
    if spack_result is None:
        raise ValueError(
            'The hpc package variant expected a deployed Spack library '
            'environment, but none was recorded.'
        )

    hpc_pins = ctx.pins.get('hpc', {})
    mpi4py_version = _normalize_optional_pin(hpc_pins.get('mpi4py'))
    ilamb_version = _normalize_optional_pin(hpc_pins.get('ilamb'))
    esmpy_version = _normalize_optional_pin(hpc_pins.get('esmpy'))
    xesmf_version = _normalize_optional_pin(hpc_pins.get('xesmf'))

    if all(
        version is None
        for version in (
            mpi4py_version,
            ilamb_version,
            esmpy_version,
            xesmf_version,
        )
    ):
        return

    compute_prefix = _get_runtime_pixi_value(ctx, 'prefix')
    pixi_toml = Path(compute_prefix) / 'pixi.toml'
    pixi_exe = _require_pixi_executable(ctx)
    log_filename = _get_log_filename(ctx)
    quiet = bool(getattr(ctx.args, 'quiet', False))

    SOURCE_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    script_lines = ['#!/bin/bash', 'set -e']

    pixi_shell_hook_prefix = build_pixi_shell_hook_prefix(
        pixi_exe=pixi_exe, pixi_toml=str(pixi_toml)
    )
    script_lines.append(f'{pixi_shell_hook_prefix} true')
    script_lines.append(str(spack_result['activation']).rstrip())

    if mpi4py_version is not None:
        script_lines.append(
            'MPICC="mpicc -shared" python -m pip install '
            '--no-cache-dir --no-binary=mpi4py --no-build-isolation '
            f'"mpi4py=={mpi4py_version}"'
        )
    if ilamb_version is not None:
        script_lines.append(
            'python -m pip install '
            '--no-cache-dir --no-deps --no-binary=ilamb '
            '--no-build-isolation '
            f'"ilamb=={ilamb_version}"'
        )

    view_path = Path(str(spack_result['view_path']))
    if esmpy_version is not None:
        esmf_dir = SOURCE_BUILD_DIR / f'esmf-{esmpy_version}'
        esmpy_dir = esmf_dir / 'src' / 'addon' / 'esmpy'
        if esmf_dir.exists():
            script_lines.append(f'rm -rf {shlex.quote(str(esmf_dir))}')
        script_lines.extend(
            [
                f'git clone https://github.com/esmf-org/esmf.git '
                f'-b v{esmpy_version} {shlex.quote(str(esmf_dir))}',
                'export ESMFMKFILE='
                f'{shlex.quote(str(view_path / "lib/esmf.mk"))}',
                (
                    'cd '
                    f'{shlex.quote(str(esmpy_dir))} '
                    '&& rm -rf src/esmpy/fragments '
                    '&& python -m pip install --no-deps --no-build-isolation .'
                ),
            ]
        )

    if xesmf_version is not None:
        xesmf_dir = SOURCE_BUILD_DIR / f'xesmf-{xesmf_version}'
        if xesmf_dir.exists():
            script_lines.append(f'rm -rf {shlex.quote(str(xesmf_dir))}')
        script_lines.extend(
            [
                f'git clone https://github.com/pangeo-data/xESMF.git '
                f'-b v{xesmf_version} {shlex.quote(str(xesmf_dir))}',
                'export ESMFMKFILE='
                f'{shlex.quote(str(view_path / "lib/esmf.mk"))}',
                (
                    f'cd {shlex.quote(str(xesmf_dir))} '
                    '&& python -m pip install --no-deps --no-build-isolation .'
                ),
            ]
        )

    script_path = Path(ctx.work_dir) / 'post_spack_hpc.sh'
    script_path.write_text('\n'.join(script_lines) + '\n', encoding='utf-8')
    check_call(
        ['/bin/bash', str(script_path)],
        log_filename=log_filename,
        quiet=quiet,
        env=build_pixi_env(),
        cwd=ctx.repo_root,
    )


def post_deploy(ctx: DeployContext) -> dict[str, Any] | None:
    prefix_root = _get_prefix_root(ctx)
    release = bool(ctx.runtime.get('e3sm_unified', {}).get('release', False))
    if not release or prefix_root is None:
        return None

    login_prefix = _normalize_optional_path(
        _get_runtime_pixi_value(ctx, 'login_prefix')
    )
    if login_prefix is None:
        return None

    machine_tag = ctx.machine or 'local'
    nco_root = prefix_root / 'e3smu_latest_for_nco'
    nco_root.mkdir(parents=True, exist_ok=True)
    machine_link = nco_root / machine_tag
    if machine_link.exists() or machine_link.is_symlink():
        machine_link.unlink()
    machine_link.symlink_to(str(login_prefix))

    return {
        'shared': {
            'managed_directories': [str(nco_root)],
        }
    }


def _get_version(ctx: DeployContext | None = None) -> str:
    if ctx is not None:
        explicit_version = getattr(ctx.args, 'e3sm_unified_version', None)
        if explicit_version is not None:
            version = str(explicit_version).strip()
            if version:
                return version
            raise ValueError('--e3sm-unified-version must not be empty.')

    if not RECIPE_PATH.exists():
        raise FileNotFoundError(
            'Could not determine the E3SM-Unified version because the '
            f'feedstock recipe was not found at {RECIPE_PATH}. Pass '
            '--e3sm-unified-version to deploy without the feedstock submodule.'
        )
    return get_version_from_recipe(RECIPE_PATH)


def _ensure_feedstock_submodule(ctx: DeployContext) -> None:
    if RECIPE_PATH.exists():
        return
    if not GITMODULES_PATH.exists():
        return

    gitmodules_text = GITMODULES_PATH.read_text(encoding='utf-8')
    if f'path = {FEEDSTOCK_DIR.relative_to(REPO_ROOT)}' not in gitmodules_text:
        return

    log_filename = _get_log_filename(ctx)
    quiet = bool(getattr(ctx.args, 'quiet', False))
    try:
        check_call(
            [
                'git',
                'submodule',
                'update',
                '--init',
                str(FEEDSTOCK_DIR.relative_to(REPO_ROOT)),
            ],
            log_filename=log_filename,
            quiet=quiet,
            cwd=ctx.repo_root,
            env=build_pixi_env(),
        )
    except subprocess.CalledProcessError as e:
        raise ValueError(
            'Failed to initialize the e3sm-unified feedstock submodule '
            f'(exit code {e.returncode}).'
        ) from e


def _get_package_source(ctx: DeployContext) -> str:
    value = str(getattr(ctx.args, 'package_source', 'conda-forge')).strip()
    if value not in ('conda-forge', 'local-build'):
        raise ValueError(f'Unsupported package source: {value}')
    return value


def _get_package_mpi(ctx: DeployContext) -> str:
    explicit = getattr(ctx.args, 'package_mpi', None)
    if explicit is not None:
        return str(explicit).strip()

    if getattr(ctx.args, 'no_spack', False):
        return 'nompi'

    if _machine_supports_hpc_package(ctx):
        return 'hpc'

    return 'nompi'


def _get_env_layout(ctx: DeployContext) -> str:
    explicit = getattr(ctx.args, 'env_layout', None)
    if explicit is not None:
        return str(explicit).strip()

    if _machine_supports_hpc_package(ctx):
        return 'dual'

    return 'single'


def _machine_supports_hpc_package(ctx: DeployContext) -> bool:
    if ctx.machine is None:
        return False

    compiler = _get_machine_option(
        ctx=ctx, section='e3sm_unified', option='compiler'
    )
    mpi = _get_machine_option(ctx=ctx, section='e3sm_unified', option='mpi')
    return compiler is not None and mpi is not None


def _build_local_packages(
    *,
    ctx: DeployContext,
    version: str,
    package_mpis: list[str],
) -> None:
    python_version = str(
        getattr(ctx.args, 'python', None)
        or ctx.pins.get('pixi', {}).get('python', '')
    ).strip()
    if not python_version:
        raise ValueError('No python version was resolved for local builds.')

    channels = get_base_channels(RECIPE_PATH, version)
    log_filename = _get_log_filename(ctx)
    quiet = bool(getattr(ctx.args, 'quiet', False))

    LOCAL_CHANNEL_DIR.mkdir(parents=True, exist_ok=True)
    VARIANT_OVERRIDE_DIR.mkdir(parents=True, exist_ok=True)

    for package_mpi in package_mpis:
        variant_path = _find_variant_config(
            python_version=python_version,
            package_mpi=package_mpi,
        )
        override_path = _write_variant_override(
            variant_path=variant_path, channels=channels
        )
        env = build_pixi_env()
        env.setdefault('RATTLER_REPODATA_USE_ZSTD', '0')
        env.setdefault('REQWEST_DISABLE_HTTP2', '1')
        env.setdefault('RATTLER_IO_CONCURRENCY_LIMIT', '4')
        check_call(
            [
                'rattler-build',
                'build',
                '-m',
                str(override_path),
                '-r',
                str(FEEDSTOCK_DIR / 'recipe'),
                '--output-dir',
                str(LOCAL_CHANNEL_DIR),
            ],
            log_filename=log_filename,
            quiet=quiet,
            cwd=ctx.repo_root,
            env=env,
        )


def _find_variant_config(*, python_version: str, package_mpi: str) -> Path:
    platform_tag = _get_conda_platform()
    pattern = f'{platform_tag}_mpi{package_mpi}python{python_version}*.yaml'
    matches = sorted(CI_SUPPORT_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            'No rattler-build variant config matched '
            f'{pattern} in {CI_SUPPORT_DIR}.'
        )
    return matches[0]


def _get_conda_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == 'linux':
        if machine == 'x86_64':
            return 'linux_64'
        if machine == 'aarch64':
            return 'linux_aarch64'
    if system == 'darwin':
        if machine == 'x86_64':
            return 'osx_64'
        if machine == 'arm64':
            return 'osx_arm64'

    raise ValueError(
        f'Unsupported platform for deploy hook: {system}/{machine}'
    )


def _write_variant_override(
    *, variant_path: Path, channels: list[str]
) -> Path:
    with variant_path.open('r', encoding='utf-8') as handle:
        variant_cfg = yaml.safe_load(handle) or {}

    variant_cfg['channel_sources'] = [','.join(channels)]

    override_path = VARIANT_OVERRIDE_DIR / f'{variant_path.stem}_deploy.yaml'
    with override_path.open('w', encoding='utf-8') as handle:
        yaml.safe_dump(variant_cfg, handle, sort_keys=False)
    return override_path


def _get_pixi_prefixes(
    *,
    ctx: DeployContext,
    version: str,
    release: bool,
    package_mpi: str,
    env_layout: str,
) -> tuple[str, str | None]:
    explicit_prefix = getattr(ctx.args, 'prefix', None)
    if explicit_prefix:
        prefix = _abs_path(str(explicit_prefix))
        if env_layout == 'single':
            return prefix, None
        if package_mpi == 'nompi':
            return prefix, prefix
        return prefix, f'{prefix}_login'

    prefix_root = _get_prefix_root(ctx)
    if prefix_root is None:
        prefix_root = REPO_ROOT / 'deploy_tmp' / 'prefixes'

    version_dir = _get_version_dir_name(version)
    machine_tag = ctx.machine or 'local'
    install_root = prefix_root / version_dir / machine_tag

    prefix_path = install_root / 'pixi'
    if env_layout == 'single':
        return str(prefix_path), None
    if package_mpi == 'nompi':
        return str(prefix_path), str(prefix_path)

    login_prefix = install_root / 'pixi_login'
    return str(prefix_path), str(login_prefix)


def _get_prefix_root(ctx: DeployContext) -> Path | None:
    if ctx.machine_config.has_option('deploy', 'prefix_root'):
        return _normalize_optional_path(
            ctx.machine_config.get('deploy', 'prefix_root')
        )
    if ctx.machine_config.has_option('e3sm_unified', 'base_path'):
        return _normalize_optional_path(
            ctx.machine_config.get('e3sm_unified', 'base_path')
        )
    return None


def _resolve_spack_path(ctx: DeployContext) -> str | None:
    cli_value = getattr(ctx.args, 'spack_path', None)
    if cli_value:
        return _abs_path(str(cli_value))

    spack_cfg = ctx.config.get('spack', {})
    if isinstance(spack_cfg, dict):
        cfg_value = spack_cfg.get('spack_path')
        cfg_path = _normalize_optional_path(cfg_value)
        if cfg_path is not None:
            return str(cfg_path)

    prefix_root = _get_prefix_root(ctx)
    if prefix_root is not None:
        version = str(
            ctx.runtime.get('project', {}).get('version', '')
        ).strip()
        if not version:
            version = _get_version(ctx)
        machine_tag = ctx.machine or 'local'
        version_dir = _get_version_dir_name(version)
        return str(prefix_root / version_dir / machine_tag / 'spack')

    if ctx.machine_config.has_option('deploy', 'spack'):
        machine_path = _normalize_optional_path(
            ctx.machine_config.get('deploy', 'spack')
        )
        if machine_path is not None:
            return str(machine_path)

    return None


def _get_version_dir_name(version: str) -> str:
    return f'e3smu_{version.replace(".", "_")}'


def _get_primary_spack_result(ctx: DeployContext) -> dict[str, Any] | None:
    runtime_spack = ctx.runtime.get('spack', {})
    if not isinstance(runtime_spack, dict):
        return None
    results = runtime_spack.get('results', [])
    if not isinstance(results, list) or not results:
        return None
    result = results[0]
    if not isinstance(result, dict):
        return None
    return result


def _get_spack_exclude_packages(ctx: DeployContext) -> list[str]:
    spack_cfg = ctx.config.get('spack', {})
    if not isinstance(spack_cfg, dict):
        return []

    exclude_packages = spack_cfg.get('exclude_packages', [])
    if exclude_packages is None:
        return []
    if isinstance(exclude_packages, str):
        return [exclude_packages]
    return [str(package) for package in exclude_packages]


def _maybe_exclude_e3sm_hdf5_netcdf(
    *, exclude_packages: list[str], machine_config
) -> None:
    use_bundle = False
    if machine_config.has_section(
        'e3sm_unified'
    ) and machine_config.has_option(
        'e3sm_unified',
        'use_e3sm_hdf5_netcdf',
    ):
        use_bundle = machine_config.getboolean(
            'e3sm_unified', 'use_e3sm_hdf5_netcdf'
        )

    if not use_bundle and 'hdf5_netcdf' not in exclude_packages:
        exclude_packages.append('hdf5_netcdf')


def _sync_e3sm_unified_spack_machine_options(*, machine_config) -> None:
    if not machine_config.has_section('e3sm_unified'):
        return

    if not machine_config.has_option('e3sm_unified', 'use_e3sm_hdf5_netcdf'):
        return

    if not machine_config.has_section('deploy'):
        machine_config.add_section('deploy')

    machine_config.set(
        'deploy',
        'use_e3sm_hdf5_netcdf',
        machine_config.get('e3sm_unified', 'use_e3sm_hdf5_netcdf'),
    )


def _get_permissions_runtime(ctx: DeployContext) -> dict[str, Any]:
    runtime: dict[str, Any] = {}

    group = _get_machine_option(
        ctx=ctx, section='e3sm_unified', option='group'
    )
    if group is not None:
        runtime['group'] = group
        runtime['world_readable'] = True

    return runtime


def _get_toolchain_runtime(ctx: DeployContext) -> dict[str, Any]:
    runtime: dict[str, Any] = {}

    compiler = _get_machine_option(
        ctx=ctx, section='e3sm_unified', option='compiler'
    )
    mpi = _get_machine_option(ctx=ctx, section='e3sm_unified', option='mpi')

    if compiler is not None:
        runtime['compiler'] = [compiler]
    if mpi is not None:
        runtime['mpi'] = [mpi]

    return runtime


def _get_shared_load_script_runtime(
    *,
    ctx: DeployContext,
    version: str,
    release: bool,
) -> dict[str, Any]:
    machine_tag = ctx.machine or 'local'
    alias_name = _get_e3sm_unified_load_script_name(
        version=version,
        machine_tag=machine_tag,
        release=release,
    )

    runtime: dict[str, Any] = {
        'load_script_copies': [],
        'load_script_symlinks': [],
    }

    requested_load_script_dir = _get_requested_load_script_dir(ctx)
    if requested_load_script_dir is not None:
        runtime['load_script_copies'].append(
            str(requested_load_script_dir / alias_name)
        )

    prefix_root = _get_prefix_root(ctx)
    if prefix_root is None:
        ctx.logger.info(
            'Skipping shared load-script aliases: no deploy prefix root was '
            'configured for this machine.'
        )
        return runtime

    if release:
        versioned = prefix_root / alias_name
        runtime['load_script_copies'].append(str(versioned))
        runtime['load_script_symlinks'].append(
            {
                'path': str(
                    prefix_root / f'load_latest_e3sm_unified_{machine_tag}.sh'
                ),
                'target': str(versioned),
            }
        )
    else:
        runtime['load_script_copies'].append(str(prefix_root / alias_name))

    return runtime


def _get_machine_option(
    *, ctx: DeployContext, section: str, option: str
) -> str | None:
    if not ctx.machine_config.has_section(section):
        return None
    if not ctx.machine_config.has_option(section, option):
        return None

    value = str(ctx.machine_config.get(section, option)).strip()
    if value.lower() in ('', 'none', 'null'):
        return None
    return value


def _get_machine_bool_option(
    *, ctx: DeployContext, section: str, option: str
) -> bool | None:
    value = _get_machine_option(ctx=ctx, section=section, option=option)
    if value is None:
        return None

    normalized = value.lower()
    if normalized in ('true', 'yes', 'on', '1'):
        return True
    if normalized in ('false', 'no', 'off', '0'):
        return False

    raise ValueError(
        f'Expected [{section}] {option} to be a boolean, got {value!r}.'
    )


def _normalize_optional_pin(value: Any) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    if token.lower() in ('', 'none', 'null'):
        return None
    return token


def _normalize_optional_token(value: Any) -> str | None:
    if value is None:
        return None

    token = str(value).strip()
    if token.lower() in ('', 'none', 'null', 'dynamic'):
        return None
    return token


def _normalize_optional_path(value: Any) -> Path | None:
    if value is None:
        return None
    token = str(value).strip()
    if token.lower() in ('', 'none', 'null'):
        return None
    return Path(_abs_path(token))


def _get_requested_load_script_dir(ctx: DeployContext) -> Path | None:
    return _normalize_optional_path(getattr(ctx.args, 'load_script_dir', None))


def _get_e3sm_unified_load_script_name(
    *, version: str, machine_tag: str, release: bool
) -> str:
    prefix = 'load' if release else 'test'
    return f'{prefix}_e3sm_unified_{version}_{machine_tag}.sh'


def _abs_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _get_runtime_pixi_value(ctx: DeployContext, key: str) -> str:
    runtime_pixi = ctx.runtime.get('pixi', {})
    if not isinstance(runtime_pixi, dict):
        raise ValueError('runtime.pixi is missing or invalid')
    value = runtime_pixi.get(key)
    if value is None:
        raise ValueError(f'runtime.pixi.{key} is missing')
    return str(value)


def _require_pixi_executable(ctx: DeployContext) -> str:
    pixi = getattr(ctx.args, 'pixi', None)
    if not pixi:
        raise ValueError('The deploy run did not record a pixi executable.')
    return _abs_path(str(pixi))


def _get_log_filename(ctx: DeployContext) -> str:
    for handler in ctx.logger.handlers:
        base_filename = getattr(handler, 'baseFilename', None)
        if base_filename:
            return str(base_filename)
    return str(Path(ctx.work_dir) / 'logs' / 'mache_deploy_run.log')
