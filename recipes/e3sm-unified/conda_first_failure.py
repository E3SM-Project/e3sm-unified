#!/usr/bin/env python

import subprocess
import argparse


def parse_specs(specfile):
    """Parse the spec file, returning a list of specs."""
    specs = []
    with open(specfile, "r") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            if "{{" in raw or "}}" in raw:
                raise ValueError(
                    "Jinja2 templating ({{ or }}) found in spec file; this "
                    "is not supported."
                )
            # Remove leading '-' and whitespace
            spec = raw.lstrip('-').strip()
            # Remove trailing comments
            if '#' in spec:
                spec = spec.split('#', 1)[0].strip()
            if spec:
                specs.append(spec)
    return specs


def find_first_failure(specs, base_command, timeout):
    highest_valid = -1
    lowest_invalid = len(specs)
    end_index = len(specs)
    last_failed_output = None
    while highest_valid != lowest_invalid-1:
        subset_specs = specs[0:end_index]
        print(f'last: {subset_specs[-1]}')

        command = base_command + subset_specs

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                text=True,
            )
            output = result.stdout
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            if result.returncode == 0:
                highest_valid = end_index-1
                end_index = int(0.5 + 0.5*(highest_valid + lowest_invalid)) + 1
                print('  Succeeded!')
            else:
                last_failed_output = output
                lowest_invalid = end_index-1
                end_index = int(0.5 + 0.5*(highest_valid + lowest_invalid)) + 1
                print('  Failed!')
        except subprocess.TimeoutExpired:
            last_failed_output = "Timed out!"
            lowest_invalid = end_index-1
            end_index = int(0.5 + 0.5*(highest_valid + lowest_invalid)) + 1
            print('  Failed!')
        print(
            f'  valid: {highest_valid}, invalid: {lowest_invalid}, '
            f'end: {end_index}'
        )
    return lowest_invalid, last_failed_output


def main():
    parser = argparse.ArgumentParser(
        description="Find first failing conda package spec."
    )
    parser.add_argument(
        "specfile",
        help="Path to file containing conda specs (one per line)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=240,
        help="Timeout for each conda dry-run (seconds)"
    )
    args = parser.parse_args()

    specs = parse_specs(args.specfile)

    base_command = ['conda', 'create', '-y', '-n', 'dry-run', '--dry-run']

    lowest_invalid, last_failed_output = find_first_failure(
        specs, base_command, args.timeout
    )

    if lowest_invalid == len(specs):
        print('No failures!')
    else:
        print(f'First failing package: {specs[lowest_invalid]}')
        if last_failed_output:
            print("\n--- Output from last failed attempt ---\n")
            print(last_failed_output)


if __name__ == "__main__":
    main()
