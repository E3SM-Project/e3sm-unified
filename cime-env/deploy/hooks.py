"""Deployment hooks for the cime-env mache.deploy workflow."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # This import is only for static type checking; at runtime, `mache` is
    # already installed in the bootstrap environment when hooks are executed.
    from mache.deploy.hooks import DeployContext


def pre_pixi(ctx: DeployContext) -> dict[str, Any] | None:
    version = ctx.config['project']['version']
    if version is None or version.lower() == 'dynamic':
        raise ValueError(
            'Version must be explicitly specified in config.yaml for cime-env.'
        )
    permissions = _get_permissions_runtime(ctx)

    prefix = _get_pixi_prefix(ctx=ctx, version=version)
    shared = _get_shared_load_script_runtime(ctx)

    return {
        'pixi': {
            'prefix': prefix,
        },
        'permissions': permissions,
        'shared': shared,
    }


def _get_permissions_runtime(ctx: DeployContext) -> dict[str, Any]:
    runtime: dict[str, Any] = {}

    group = _get_machine_option(
        ctx=ctx, section='e3sm_unified', option='group'
    )
    if group is not None:
        runtime['group'] = group
        runtime['world_readable'] = True

    return runtime


def _get_pixi_prefix(
    *,
    ctx: DeployContext,
    version: str,
) -> str | None:
    explicit_prefix = getattr(ctx.args, 'prefix', None)
    if explicit_prefix:
        prefix = _abs_path(str(explicit_prefix))
        return prefix

    prefix_root = _get_prefix_root(ctx)

    if prefix_root is None:
        raise ValueError(
            "Machine config 'e3sm_unified:base_path' is either unset or "
            'empty. Please provide a valid path.'
        )
    version_dir = _get_version_dir_name(version)
    machine_tag = ctx.machine or 'local'
    install_root = prefix_root / version_dir / machine_tag
    prefix_path = install_root / 'pixi'
    return str(prefix_path)


def _get_shared_load_script_runtime(ctx: DeployContext) -> dict[str, Any]:
    requested_load_script_dir = _get_requested_load_script_dir(ctx)
    prefix_root = _get_prefix_root(ctx)

    alias_name = 'load_latest_cime_env.sh'

    if requested_load_script_dir is not None:
        dest_script = requested_load_script_dir / alias_name
    elif prefix_root is not None:
        dest_script = prefix_root / alias_name
    else:
        raise ValueError(
            "Machine config 'e3sm_unified:base_path' is either unset or "
            'empty. Please provide a valid path.'
        )

    return {
        'load_script_copies': [str(dest_script)],
    }


def _abs_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def _normalize_optional_path(value: Any) -> Path | None:
    if value is None:
        return None
    token = str(value).strip()
    if token.lower() in ('', 'none', 'null'):
        return None
    return Path(_abs_path(token))


def _get_version_dir_name(version: str) -> str:
    return f'e3smu_{version.replace(".", "_")}'


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


def _get_requested_load_script_dir(ctx: DeployContext) -> Path | None:
    return _normalize_optional_path(getattr(ctx.args, 'load_script_dir', None))


def _get_prefix_root(ctx: DeployContext) -> Path | None:
    if ctx.machine_config.has_option('e3sm_unified', 'base_path'):
        return _normalize_optional_path(
            ctx.machine_config.get('e3sm_unified', 'base_path')
        )
    return None
