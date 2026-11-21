"""Shared recipe helpers for E3SM-Unified build and deploy flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEV_LABELS = {
    'chemdyg': 'chemdyg_dev',
    'e3sm_diags': 'e3sm_diags_dev',
    'e3sm_to_cmip': 'e3sm_to_cmip_dev',
    'mache': 'mache_dev',
    'moab': 'moab_dev',
    'mpas-analysis': 'mpas_analysis_dev',
    'mpas_tools': 'mpas_tools_dev',
    'nco': 'nco_dev',
    'xcdat': 'xcdat_dev',
    'zppy': 'zppy_dev',
    'zppy-interfaces': 'zppy_interfaces_dev',
    'zstash': 'zstash_dev',
}
def get_version_from_recipe(recipe_yaml_path: str | Path) -> str:
    """Parse the version from the context or package section in recipe.yaml."""
    recipe = _load_recipe(recipe_yaml_path)
    version = (
        recipe.get('context', {}).get('version')
        or recipe.get('package', {}).get('version')
    )
    if version is None:
        raise ValueError(f'Could not find version in {recipe_yaml_path}')
    return str(version)


def get_rc_dev_labels(recipe_yaml_path: str | Path) -> list[str]:
    """Return dev labels for RC dependencies in the recipe run requirements."""
    recipe = _load_recipe(recipe_yaml_path)
    run_reqs = recipe.get('requirements', {}).get('run', [])
    flattened: list[str] = []
    _collect_requirements(run_reqs, flattened)

    labels: list[str] = []
    for requirement in flattened:
        package, _, version = requirement.partition(' ')
        version = version.strip()
        if package == 'nco' and ('alpha' in version or 'beta' in version):
            label = DEV_LABELS.get(package)
        elif 'rc' in version:
            label = DEV_LABELS.get(package)
        else:
            label = None
        if label is not None and label not in labels:
            labels.append(label)
    return labels


def get_base_channels(
    recipe_yaml_path: str | Path, version: str | None = None
) -> list[str]:
    """Return source channels needed to build or deploy a given recipe version."""
    recipe_version = get_version_from_recipe(recipe_yaml_path)
    if version is None:
        version = recipe_version
    elif 'rc' in version and version != recipe_version:
        raise ValueError(
            'Explicit RC version '
            f'{version!r} does not match feedstock recipe version '
            f'{recipe_version!r}. Update the e3sm-unified feedstock submodule '
            'or omit --e3sm-unified-version.'
        )

    if 'rc' not in version:
        return ['conda-forge']

    ordered = ['conda-forge/label/e3sm_unified_dev']
    for label in get_rc_dev_labels(recipe_yaml_path):
        ordered.append(f'conda-forge/label/{label}')
    ordered.append('conda-forge')
    return list(dict.fromkeys(ordered))


def get_recipe_tests(
    recipe_yaml_path: str | Path, variables: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Return the imports and commands the recipe tests for one variant.

    ``if``/``then``/``else`` selectors are evaluated with ``variables`` (for
    example ``mpi``, ``linux`` and ``aarch64``); a selector that uses any
    other name raises an error rather than being silently skipped.
    """
    recipe = _load_recipe(recipe_yaml_path)
    imports: list[str] = []
    commands: list[str] = []
    for test in recipe.get('tests', []):
        if 'python' in test:
            _collect_selected(
                test['python'].get('imports', []), variables, imports
            )
        if 'script' in test:
            _collect_selected(test['script'], variables, commands)
    return imports, commands


def _load_recipe(recipe_yaml_path: str | Path) -> dict[str, Any]:
    recipe_path = Path(recipe_yaml_path)
    with recipe_path.open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle)


def _collect_requirements(requirements: Any, collected: list[str]) -> None:
    if isinstance(requirements, list):
        for item in requirements:
            _collect_requirements(item, collected)
    elif isinstance(requirements, dict):
        if 'then' in requirements:
            _collect_requirements(requirements['then'], collected)
        if 'else' in requirements:
            _collect_requirements(requirements['else'], collected)
    elif isinstance(requirements, str):
        collected.append(requirements)


def _collect_selected(
    items: Any, variables: dict[str, Any], collected: list[str]
) -> None:
    if isinstance(items, list):
        for item in items:
            _collect_selected(item, variables, collected)
    elif isinstance(items, dict):
        if _evaluate_selector(str(items['if']), variables):
            _collect_selected(items.get('then', []), variables, collected)
        else:
            _collect_selected(items.get('else', []), variables, collected)
    elif isinstance(items, str):
        collected.append(items)


def _evaluate_selector(expression: str, variables: dict[str, Any]) -> bool:
    # rattler-build selectors are minijinja expressions, which jinja2 (a
    # mache dependency) evaluates the same way for the syntax recipes use
    import jinja2

    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    evaluate = env.compile_expression(expression, undefined_to_none=False)
    return bool(evaluate(**variables))
