#!/usr/bin/env python3
"""Find the first package spec that makes a pixi solve fail."""

from __future__ import annotations

import argparse
import json
import os
import platform as pyplatform
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


DEFAULT_TIMEOUT = 240
DEFAULT_CHANNELS = ["conda-forge"]


@dataclass(frozen=True)
class SpecEntry:
    line_number: int
    spec: str


@dataclass
class SolveResult:
    prefix_length: int
    success: bool
    timed_out: bool
    duration_seconds: float
    output: str
    command: list[str]


@dataclass
class FailureSearchResult:
    ordered_specs: list[SpecEntry]
    full_result: SolveResult
    failure_prefix_length: int | None
    highest_valid_prefix: int
    attempt_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find the first pixi dependency spec that breaks solving, and "
            "optionally a likely second conflicting package."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "specfile",
        help="Path to a file containing dependency specs, one per line.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Timeout for each pixi solve attempt, in seconds.",
    )
    parser.add_argument(
        "-c",
        "--channel",
        dest="channels",
        action="append",
        default=None,
        help="Channel to include in the temporary pixi workspace. Repeat as needed.",
    )
    parser.add_argument(
        "-p",
        "--platform",
        default=None,
        help="Pixi platform to solve for. Defaults to the current machine.",
    )
    parser.add_argument(
        "--pixi-bin",
        default="pixi",
        help="Pixi executable to invoke.",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the temporary pixi workspace for inspection after the run.",
    )
    parser.add_argument(
        "--find-second",
        action="store_true",
        help=(
            "After finding the first failing spec, move it to the front of the list "
            "and search again for a likely second conflicting spec."
        ),
    )
    parser.add_argument(
        "--no-markdown-summary",
        action="store_true",
        help="Skip the compact Markdown summary that is printed by default.",
    )
    return parser.parse_args()


def read_specs(specfile: str) -> list[SpecEntry]:
    specs: list[SpecEntry] = []
    with open(specfile, "r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if stripped and not stripped.startswith("#"):
                specs.append(SpecEntry(line_number=line_number, spec=stripped))
    return specs


def detect_default_platform() -> str:
    system = pyplatform.system().lower()
    machine = pyplatform.machine().lower()

    if system == "linux":
        mapping = {
            "x86_64": "linux-64",
            "amd64": "linux-64",
            "aarch64": "linux-aarch64",
            "arm64": "linux-aarch64",
            "ppc64le": "linux-ppc64le",
        }
    elif system == "darwin":
        mapping = {
            "x86_64": "osx-64",
            "amd64": "osx-64",
            "arm64": "osx-arm64",
            "aarch64": "osx-arm64",
        }
    elif system == "windows":
        mapping = {
            "x86_64": "win-64",
            "amd64": "win-64",
            "arm64": "win-arm64",
            "aarch64": "win-arm64",
        }
    else:
        mapping = {}

    platform_name = mapping.get(machine)
    if platform_name is None:
        raise SystemExit(
            "Could not infer a pixi platform for this machine. "
            "Please pass one explicitly with --platform."
        )

    return platform_name


def toml_array(items: list[str]) -> str:
    return "[" + ", ".join(json.dumps(item) for item in items) + "]"


def write_manifest(manifest_path: Path, channels: list[str], platform_name: str) -> None:
    manifest_text = (
        "[workspace]\n"
        f'channels = {toml_array(channels)}\n'
        'name = "pixi-first-failure"\n'
        f'platforms = {toml_array([platform_name])}\n'
        'version = "0.1.0"\n'
        "\n"
        "[tasks]\n"
        "\n"
        "[dependencies]\n"
    )
    manifest_path.write_text(manifest_text, encoding="utf-8")


def normalize_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def build_command(
    pixi_bin: str,
    workspace_dir: Path,
    specs: list[SpecEntry],
) -> list[str]:
    return [
        pixi_bin,
        "add",
        "--manifest-path",
        str(workspace_dir),
        "--no-install",
        "--color",
        "never",
        "--no-progress",
        *(entry.spec for entry in specs),
    ]


def build_pixi_env(workspace_dir: Path) -> dict[str, str]:
    cache_root = workspace_dir / ".pixi-runtime"
    pixi_home = cache_root / "home"
    pixi_cache = cache_root / "pixi-cache"
    rattler_cache = cache_root / "rattler-cache"
    xdg_cache = cache_root / "xdg-cache"

    for path in (pixi_home, pixi_cache, rattler_cache, xdg_cache):
        path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PIXI_HOME"] = str(pixi_home)
    env["PIXI_CACHE_DIR"] = str(pixi_cache)
    env["RATTLER_CACHE_DIR"] = str(rattler_cache)
    env["XDG_CACHE_HOME"] = str(xdg_cache)
    return env


def solve_prefix(
    prefix_length: int,
    all_specs: list[SpecEntry],
    args: argparse.Namespace,
    workspace_dir: Path,
    platform_name: str,
    channels: list[str],
) -> SolveResult:
    manifest_path = workspace_dir / "pixi.toml"
    lock_path = workspace_dir / "pixi.lock"
    pixi_dir = workspace_dir / ".pixi"

    write_manifest(manifest_path, channels, platform_name)
    if lock_path.exists():
        lock_path.unlink()
    if pixi_dir.exists():
        shutil.rmtree(pixi_dir)

    subset_specs = all_specs[:prefix_length]
    command = build_command(args.pixi_bin, workspace_dir, subset_specs)
    env = build_pixi_env(workspace_dir)

    start = time.monotonic()
    try:
        result = subprocess.run(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.timeout,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        duration_seconds = time.monotonic() - start
        partial_output = normalize_output(exc.stdout)
        if exc.stderr:
            partial_output += normalize_output(exc.stderr)
        timeout_message = (
            f"Timed out after {args.timeout} seconds while solving prefix "
            f"of length {prefix_length}."
        )
        if partial_output.strip():
            timeout_message = f"{timeout_message}\n\n{partial_output}"
        return SolveResult(
            prefix_length=prefix_length,
            success=False,
            timed_out=True,
            duration_seconds=duration_seconds,
            output=timeout_message,
            command=command,
        )

    return SolveResult(
        prefix_length=prefix_length,
        success=result.returncode == 0,
        timed_out=False,
        duration_seconds=time.monotonic() - start,
        output=normalize_output(result.stdout),
        command=command,
    )


def describe_spec(index: int, entry: SpecEntry) -> str:
    return f"#{index} (line {entry.line_number}): {entry.spec}"


def print_attempt(
    attempt_number: int,
    total_specs: int,
    left: int,
    right: int,
    candidate_length: int,
    candidate_entry: SpecEntry,
    result: SolveResult,
) -> None:
    status = "PASS" if result.success else "FAIL"
    timeout_suffix = " [timeout]" if result.timed_out else ""
    print(f"[{attempt_number}] Checking first {candidate_length}/{total_specs} specs")
    print(f"    Boundary candidate: {describe_spec(candidate_length, candidate_entry)}")
    print(
        f"    Result: {status}{timeout_suffix} "
        f"after {result.duration_seconds:.1f}s"
    )
    print(f"    Remaining search window: prefix lengths {left}..{right}")


def print_search_header(title: str, specs: list[SpecEntry]) -> None:
    print(title)
    print(f"  Spec count: {len(specs)}")
    print(f"  Last spec in this ordering: {describe_spec(len(specs), specs[-1])}")
    print("")


def run_failure_search(
    specs: list[SpecEntry],
    args: argparse.Namespace,
    platform_name: str,
    channels: list[str],
    workspace_dir: Path,
    title: str,
) -> FailureSearchResult:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    results_by_prefix: dict[int, SolveResult] = {}

    def get_result(prefix_length: int) -> SolveResult:
        cached = results_by_prefix.get(prefix_length)
        if cached is not None:
            return cached
        result = solve_prefix(
            prefix_length=prefix_length,
            all_specs=specs,
            args=args,
            workspace_dir=workspace_dir,
            platform_name=platform_name,
            channels=channels,
        )
        results_by_prefix[prefix_length] = result
        return result

    print_search_header(title, specs)

    full_result = get_result(len(specs))
    attempt_count = 1
    print_attempt(
        attempt_number=attempt_count,
        total_specs=len(specs),
        left=1,
        right=len(specs),
        candidate_length=len(specs),
        candidate_entry=specs[-1],
        result=full_result,
    )

    if full_result.success:
        return FailureSearchResult(
            ordered_specs=specs,
            full_result=full_result,
            failure_prefix_length=None,
            highest_valid_prefix=len(specs),
            attempt_count=attempt_count,
        )

    left = 1
    right = len(specs)
    highest_valid_prefix = 0

    while left < right:
        middle = (left + right) // 2
        result = get_result(middle)
        attempt_count += 1
        print_attempt(
            attempt_number=attempt_count,
            total_specs=len(specs),
            left=left,
            right=right,
            candidate_length=middle,
            candidate_entry=specs[middle - 1],
            result=result,
        )

        if result.success:
            highest_valid_prefix = max(highest_valid_prefix, middle)
            left = middle + 1
        else:
            right = middle

    return FailureSearchResult(
        ordered_specs=specs,
        full_result=get_result(left),
        failure_prefix_length=left,
        highest_valid_prefix=highest_valid_prefix,
        attempt_count=attempt_count,
    )


def print_failure_summary(
    heading: str,
    search_result: FailureSearchResult,
) -> None:
    if search_result.failure_prefix_length is None:
        print(heading)
        print(f"  All {len(search_result.ordered_specs)} specs solve successfully with pixi.")
        return

    failure_prefix_length = search_result.failure_prefix_length
    failing_spec = search_result.ordered_specs[failure_prefix_length - 1]

    print(heading)
    print(f"  Failing spec: {describe_spec(failure_prefix_length, failing_spec)}")
    print(f"  Failing prefix length: {failure_prefix_length}")
    if search_result.highest_valid_prefix > 0:
        print(
            "  Last solvable prefix ends with: "
            f"{describe_spec(search_result.highest_valid_prefix, search_result.ordered_specs[search_result.highest_valid_prefix - 1])}"
        )
    else:
        print("  Even the first dependency in this ordering fails on its own.")

    print("")
    print("--- Output from failing solve ---")
    print(search_result.full_result.output.rstrip() or "(pixi produced no output)")


def move_spec_to_front(specs: list[SpecEntry], index: int) -> list[SpecEntry]:
    return [specs[index], *specs[:index], *specs[index + 1 :]]


def format_spec_markdown(entry: SpecEntry) -> str:
    return f"`{entry.spec}` (line {entry.line_number})"


def build_markdown_summary(
    specfile: str,
    platform_name: str,
    channels: list[str],
    first_search: FailureSearchResult,
    promoted_spec: SpecEntry | None,
    second_search: FailureSearchResult | None,
) -> str:
    lines = [
        "## pixi-first-failure summary",
        "",
        f"- Spec file: `{specfile}`",
        f"- Platform: `{platform_name}`",
        f"- Channels: `{', '.join(channels)}`",
    ]

    if first_search.failure_prefix_length is None:
        lines.extend(
            [
                "- Result: all specs solved successfully with pixi.",
            ]
        )
        return "\n".join(lines)

    first_failing_spec = first_search.ordered_specs[first_search.failure_prefix_length - 1]
    lines.extend(
        [
            f"- First failing spec: {format_spec_markdown(first_failing_spec)}",
            f"- First failing prefix length: `{first_search.failure_prefix_length}`",
        ]
    )

    if first_search.highest_valid_prefix > 0:
        last_valid_spec = first_search.ordered_specs[first_search.highest_valid_prefix - 1]
        lines.append(f"- Last solvable prefix ended with: {format_spec_markdown(last_valid_spec)}")
    else:
        lines.append("- First failing spec also failed on its own.")

    if promoted_spec is None:
        return "\n".join(lines)

    lines.append(f"- Promoted first failing spec for second pass: {format_spec_markdown(promoted_spec)}")

    if second_search is None:
        lines.append("- Second-pass search: not run.")
        return "\n".join(lines)

    if second_search.failure_prefix_length is None:
        lines.append("- Second-pass search: all reordered specs solved successfully.")
        return "\n".join(lines)

    if second_search.failure_prefix_length == 1:
        lines.append("- Second conflicting package candidate: not identified because the promoted spec still failed on its own.")
        return "\n".join(lines)

    second_failing_spec = second_search.ordered_specs[second_search.failure_prefix_length - 1]
    lines.extend(
        [
            f"- Second conflicting package candidate: {format_spec_markdown(second_failing_spec)}",
            "",
            "### Suspected conflict pair",
            "",
            f"- {format_spec_markdown(promoted_spec)}",
            f"- {format_spec_markdown(second_failing_spec)}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    if shutil.which(args.pixi_bin) is None:
        print(f"Could not find pixi executable: {args.pixi_bin}", file=sys.stderr)
        return 2

    specs = read_specs(args.specfile)
    if not specs:
        print("No dependency specs found after ignoring blank lines and comments.")
        return 1

    platform_name = args.platform or detect_default_platform()
    channels = args.channels or list(DEFAULT_CHANNELS)

    print(f"Loaded {len(specs)} dependency specs from {args.specfile}")
    print(f"Solving with pixi on platform {platform_name}")
    print(f"Channels: {', '.join(channels)}")
    print("")

    temp_root = Path(tempfile.mkdtemp(prefix="pixi-first-failure-"))
    promoted_spec: SpecEntry | None = None
    second_search: FailureSearchResult | None = None

    try:
        first_search = run_failure_search(
            specs=specs,
            args=args,
            platform_name=platform_name,
            channels=channels,
            workspace_dir=temp_root / "first-pass",
            title="Initial search",
        )

        if first_search.failure_prefix_length is None:
            print("")
            print_failure_summary("Initial search result", first_search)
            if args.keep_workdir:
                print(f"Temporary workspaces kept at: {temp_root}")
            return 0

        print("")
        print_failure_summary("Initial search result", first_search)

        if args.find_second:
            first_failure_index = first_search.failure_prefix_length - 1

            if first_failure_index == 0:
                print("")
                print("Second-pass search")
                print("  Skipped because the first failing spec is already first in the list.")
                print("  That usually means this spec fails on its own rather than only in combination.")
            else:
                promoted_spec = specs[first_failure_index]
                reordered_specs = move_spec_to_front(specs, first_failure_index)

                print("")
                print("Preparing second-pass search")
                print(f"  Promoting to the front: {describe_spec(first_failure_index + 1, promoted_spec)}")
                print("  Searching for the next spec that fails with that promoted package in place.")
                print("")

                second_search = run_failure_search(
                    specs=reordered_specs,
                    args=args,
                    platform_name=platform_name,
                    channels=channels,
                    workspace_dir=temp_root / "second-pass",
                    title="Second-pass search",
                )

                print("")
                print_failure_summary("Second-pass result", second_search)

                if second_search.failure_prefix_length == 1:
                    print("")
                    print("Second conflicting package")
                    print("  Not identified because the promoted first failing spec still fails by itself.")
                elif second_search.failure_prefix_length is not None:
                    second_failing_spec = reordered_specs[second_search.failure_prefix_length - 1]
                    print("")
                    print("Second conflicting package candidate")
                    print(f"  First failing spec: {describe_spec(first_failure_index + 1, promoted_spec)}")
                    print(
                        "  Second failing spec: "
                        f"{describe_spec(second_search.failure_prefix_length, second_failing_spec)}"
                    )
                    print(
                        "  Interpretation: the promoted spec stays solvable until this spec is added, "
                        "so this is a strong candidate for the second half of the conflict."
                    )

        if not args.no_markdown_summary:
            print("")
            print("--- Markdown summary ---")
            print(
                build_markdown_summary(
                    specfile=args.specfile,
                    platform_name=platform_name,
                    channels=channels,
                    first_search=first_search,
                    promoted_spec=promoted_spec,
                    second_search=second_search,
                )
            )

        if args.keep_workdir:
            print("")
            print(f"Temporary workspaces kept at: {temp_root}")

        return 0
    finally:
        if not args.keep_workdir:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
