#!/usr/bin/env python3
"""Render a temporary pixi manifest for CI install validation."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def _load_shared_helpers():
    repo_root = Path(__file__).resolve().parents[1]
    shared_path = repo_root / "e3sm_unified_shared.py"
    spec = importlib.util.spec_from_file_location(
        "e3sm_unified_shared", shared_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load shared helpers from {shared_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


get_base_channels = _load_shared_helpers().get_base_channels


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a pixi manifest for validating a built package."
    )
    parser.add_argument("--recipe", required=True, help="Path to recipe.yaml")
    parser.add_argument(
        "--local-channel",
        required=True,
        help="Path to local build outputs channel directory",
    )
    parser.add_argument(
        "--python-version",
        required=True,
        help="Python version to pin in the temporary environment",
    )
    parser.add_argument(
        "--package-name",
        default="e3sm-unified",
        help="Built package to install from the local channel",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the generated pixi manifest",
    )
    args = parser.parse_args()

    recipe = Path(args.recipe).resolve()
    local_channel = Path(args.local_channel).resolve()
    output = Path(args.output).resolve()

    channels = [f"file://{local_channel}"] + get_base_channels(recipe)
    dependencies = [(args.package_name, "*")]

    lines = [
        "[workspace]",
        'name = "e3sm-unified-ci-install"',
        "channels = [",
    ]
    lines.extend(f"  {_quote(channel)}," for channel in channels)
    lines.extend(
        [
            "]",
            'platforms = ["linux-64"]',
            'channel-priority = "strict"',
            "",
            "[dependencies]",
            f'python = "{args.python_version}.*"',
        ]
    )
    lines.extend(
        f"{_quote(package)} = {_quote(version)}"
        for package, version in dependencies
    )
    lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
