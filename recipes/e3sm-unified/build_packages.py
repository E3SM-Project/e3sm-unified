#!/usr/bin/env python3
import argparse
import importlib.util
import os
import subprocess
from pathlib import Path

import yaml


def _load_shared_helpers():
    repo_root = Path(__file__).resolve().parents[2]
    shared_path = repo_root / "e3sm_unified_shared.py"
    spec = importlib.util.spec_from_file_location(
        "e3sm_unified_deploy_shared", shared_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load shared helpers from {shared_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_shared = _load_shared_helpers()
get_base_channels = _shared.get_base_channels
get_version_from_recipe = _shared.get_version_from_recipe


def get_variant_configs(ci_support_dir, python_versions, mpi_versions):
    config_files = sorted(Path(ci_support_dir).glob("*.yaml"))
    if python_versions:
        python_versions = [str(version) for version in python_versions]
    if mpi_versions:
        mpi_versions = [str(mpi) for mpi in mpi_versions]

    filtered = []
    for config in config_files:
        name = config.name
        if python_versions and not any(
            f"python{version}" in name for version in python_versions
        ):
            continue
        if mpi_versions and not any(
            f"mpi{mpi}" in name for mpi in mpi_versions
        ):
            continue
        filtered.append(str(config))
    return filtered


def apply_channel_overrides(variant_config_path, channels, outputs_dir):
    with open(variant_config_path) as handle:
        variant_config = yaml.safe_load(handle) or {}

    variant_config["channel_sources"] = [",".join(channels)]

    override_dir = outputs_dir / "variant_overrides"
    override_dir.mkdir(parents=True, exist_ok=True)
    override_path = override_dir / f"{Path(variant_config_path).stem}_labels.yaml"
    with open(override_path, "w") as handle:
        yaml.safe_dump(variant_config, handle, sort_keys=False)
    return str(override_path)


def main():
    parser = argparse.ArgumentParser(
        description="Build E3SM-Unified conda packages."
    )
    parser.add_argument(
        "--python",
        nargs="+",
        help="Python version(s) to build for (overrides default matrix)."
    )
    parser.add_argument(
        "--mpi",
        nargs="+",
        help="MPI variant(s) to build for (overrides default matrix)."
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where built packages and channel metadata are written.",
    )
    args = parser.parse_args()

    recipe_root = Path(__file__).parent
    repo_root = recipe_root.parent.parent
    feedstock_dir = recipe_root / "e3sm-unified-feedstock"
    ci_support_dir = feedstock_dir / ".ci_support"
    recipe_dir = feedstock_dir / "recipe"
    recipe_yaml_path = recipe_dir / "recipe.yaml"
    outputs_dir = Path(args.output_dir) if args.output_dir else recipe_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    version = get_version_from_recipe(str(recipe_yaml_path))
    matrix_files = get_variant_configs(
        ci_support_dir=ci_support_dir,
        python_versions=args.python,
        mpi_versions=args.mpi,
    )
    if not matrix_files:
        raise ValueError(
            "No variant config files matched the requested filters."
        )

    channels = get_base_channels(recipe_yaml_path, version)

    for file in matrix_files:
        override_file = apply_channel_overrides(
            variant_config_path=file,
            channels=channels,
            outputs_dir=outputs_dir,
        )
        cmd = [
            "rattler-build",
            "build",
            "-m",
            override_file,
            "-r",
            str(recipe_dir),
            "--output-dir",
            str(outputs_dir),
        ]
        env = os.environ.copy()
        env.setdefault("RATTLER_REPODATA_USE_ZSTD", "0")
        env.setdefault("REQWEST_DISABLE_HTTP2", "1")
        env.setdefault("RATTLER_IO_CONCURRENCY_LIMIT", "4")
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True, env=env)


if __name__ == "__main__":
    main()
