#!/usr/bin/env python3
"""
Drive ./deploy.py on HPC machines from the deployer's own computer

Each command runs a short bash script in a login shell on a machine, over ssh
through the connection the deployer opened by logging in, or here with
--local.  See README.md for the workflow and AGENTS.md for the instructions
agents follow.  Only the standard library of Python 3.6 or newer is needed,
so this also runs with the system python3 of a login node.
"""

import argparse
import configparser
import os
import shlex
import subprocess
import sys

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

DEFAULT_CONFIG = '~/.config/e3sm_unified_deploy.cfg'

#: what each script prints first, so that a login message before it is
#: dropped
MARKER = '@@hpc_deploy@@'

#: prints the command that submits the compute-node test, from the
#: [parallel] section of mache's config for the machine.  It runs with the
#: deployed environment's python, which has mache.
JOB_COMMAND_PY = r'''
import sys
from mache import MachineInfo

config = MachineInfo(machine=sys.argv[1]).config


def get(option):
    return config.get('parallel', option, fallback='').strip()


def target(option):
    # the debug queue, partition or QOS if there is one, else the first
    names = [name.strip() for name in get(option).split(',') if name.strip()]
    return 'debug' if 'debug' in names else (names[0] if names else '')


if get('system') == 'pbs':
    command = ['qsub', '-l', 'select=1', '-l', 'walltime=00:30:00']
    for flag, value in [('-A', get('account')), ('-q', target('queues'))]:
        if value:
            command += [flag, value]
    if get('filesystems'):
        command += ['-l', 'filesystems=' + get('filesystems')]
else:
    command = ['sbatch', '--nodes=1', '--time=00:30:00']
    for option, value in [
        ('account', get('account')),
        ('partition', target('partitions')),
        ('qos', target('qos')),
        ('constraint', target('constraints')),
    ]:
        if value:
            command.append(f'--{option}={value}')
print(' '.join(command))
'''

PRELUDE = r'''
echo @@hpc_deploy@@
exec 2>&1
checkout="${checkout/#\~/$HOME}"
'''

SCRIPTS = {}

# Bring the checkout to a commit of a branch, cloning it if it is missing.
# GitHub is reached over https, so the machine needs no GitHub ssh key.
SCRIPTS['sync'] = r'''
_git() { git -c url.https://github.com/.insteadOf=git@github.com: "$@"; }
if [ ! -e "$checkout" ]; then
  _git clone --branch "$branch" "$repo" "$checkout" || exit 1
fi
cd "$checkout" || exit 1
changes="$(git status --short --untracked-files=no --ignore-submodules=all)"
if [ -n "$changes" ]; then
  echo "Error: $checkout has changes to tracked files:"
  echo "$changes"
  exit 1
fi
_git fetch --quiet "$repo" "$branch" || exit 1
if ! git merge-base --is-ancestor "$commit" FETCH_HEAD 2>/dev/null; then
  echo "Error: $commit is not on $branch of $repo.  Has it been pushed?"
  exit 1
fi
if [ "$(git symbolic-ref -q --short HEAD)" = "$branch" ] \
    && git merge-base --is-ancestor HEAD "$commit"; then
  git merge --quiet --ff-only "$commit"
else
  git checkout --quiet --detach "$commit"
fi || exit 1
_git submodule --quiet update --init || exit 1
echo "$checkout is at $(git log -1 --format='%h %s')"
git submodule status
'''

# Run deploy.py in the background, in a new run directory, with Python's
# output unbuffered so that the log keeps up.  deploy.py replaces deploy_tmp
# when it next runs, so the test scripts it wrote there are copied to the run
# directory.
SCRIPTS['start'] = r'''
cd "$checkout" || exit 1
for latest in deploy_runs/*/latest; do
  if [ -e "$latest" ] && [ ! -f "$latest/exit_code" ] && [ "$force" != true ]
  then
    echo "Error: $(readlink -f "$latest") has no exit code, so its deploy may"
    echo "still be running.  Check with status, and pass --force if it is not."
    exit 1
  fi
done
run_dir="$(pwd -P)/deploy_runs/$machine/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$run_dir" || exit 1
ln -sfn "$(basename "$run_dir")" "deploy_runs/$machine/latest"
PYTHONUNBUFFERED=1 setsid nohup bash -c '
  echo $$ > "$0/pid"
  hostname > "$0/node"
  echo "hpc_deploy: running $* at $(git rev-parse HEAD) on $(hostname), $(date -u)"
  "$@"
  code=$?
  cp deploy_tmp/test_*.sh "$0/" 2>/dev/null
  echo "hpc_deploy: exited with code $code, $(date -u)"
  echo $code > "$0/exit_code"
' "$run_dir" "${command[@]}" > "$run_dir/deploy.log" 2>&1 < /dev/null &
echo "Started ${command[*]} on $(hostname), with its output in"
echo "$run_dir/deploy.log"
'''

SCRIPTS['status'] = r'''
cd "$checkout" 2>/dev/null || { echo "$checkout is missing"; exit 0; }
echo "checkout: $(git log -1 --format='%h %s')" \
  "($(git symbolic-ref -q --short HEAD || echo detached))"
git status --short --untracked-files=no --ignore-submodules=all
git submodule status
run_dir="deploy_runs/$machine/latest"
if [ ! -e "$run_dir" ]; then
  echo "deploy:   none started here for $machine"
  exit 0
fi
run_dir="$(readlink -f "$run_dir")"
echo "run:      $run_dir"
node="$(cat "$run_dir/node" 2>/dev/null)"
if [ -f "$run_dir/exit_code" ]; then
  echo "deploy:   exited with code $(cat "$run_dir/exit_code")"
elif [ "$node" != "$(hostname)" ]; then
  echo "deploy:   no exit code yet; it started on $node, so its process" \
    "cannot be checked from $(hostname)"
elif ps -p "$(cat "$run_dir/pid")" > /dev/null 2>&1; then
  echo "deploy:   running"
else
  echo "deploy:   interrupted: its process is gone, with no exit code"
fi
results='^Resolved e3sm-unified|^Testing the|FAIL:|All tests passed'
results="$results|test\(s\) failed|^Writing shared load-script copy"
grep -E "$results" "$run_dir/deploy.log"
if [ -f "$run_dir/compute_job_id" ]; then
  job="$(cat "$run_dir/compute_job_id")"
  if [ -f "$run_dir/compute_exit_code" ]; then
    echo "compute:  job $job exited with code" \
      "$(cat "$run_dir/compute_exit_code")"
    grep -E "$results" "$run_dir/compute_test.log"
  else
    if command -v squeue > /dev/null; then
      state="$(squeue -h -j "$job" -o %T 2>/dev/null)"
    else
      state="$(qstat -f "$job" 2>/dev/null | sed -n 's/^ *job_state = //p')"
    fi
    echo "compute:  job $job" \
      "${state:-is no longer queued, with no result; see compute_job.out}"
  fi
fi
if [ "$tail" -gt 0 ]; then
  echo "the end of deploy.log:"
  tail -n "$tail" "$run_dir/deploy.log" | sed 's/.*\r//'
fi
'''

# Write a job that runs the latest deploy's test scripts on a compute node,
# where the load script each one sources loads the compute environment, and
# submit it if asked
SCRIPTS['compute-test'] = r'''
cd "$checkout" || exit 1
run_dir="$(readlink -f "deploy_runs/$machine/latest")"
if [ "$(cat "$run_dir/exit_code" 2>/dev/null)" != 0 ]; then
  echo "Error: the latest deploy for $machine has not succeeded."
  exit 1
fi
if [ -z "$submit_command" ]; then
  load_script="$(sed -n 's/^Wrote load script: //p' "$run_dir/deploy.log" \
    | tail -n 1)"
  submit_command="$(source "$load_script" > /dev/null 2>&1 \
    && python -c "$job_command_py" "$machine")"
  if [ -z "$submit_command" ]; then
    echo "Error: could not get the job settings from mache with $load_script"
    exit 1
  fi
fi
job_script="$run_dir/compute_test_job.sh"
printf '#!/bin/bash\ncd %q || exit 1\ncode=0
for script in test_*.sh; do\n  bash "$script" || code=1
done > compute_test.log 2>&1\necho $code > compute_exit_code\n' \
  "$run_dir" > "$job_script"
read -r -a submit <<< "$submit_command"
if [ "${submit[0]}" = qsub ]; then
  submit+=(-N e3smu_env_test -j oe -o "$run_dir/compute_job.out")
else
  submit+=(--job-name=e3smu_env_test --output="$run_dir/compute_job.out")
fi
submit+=("$job_script")
if [ "$submit_job" != true ]; then
  echo "Would submit: ${submit[*]}"
  exit 0
fi
rm -f "$run_dir"/compute_{job_id,job.out,exit_code,test.log}
output="$("${submit[@]}")" || { echo "$output"; exit 1; }
echo "$output"
echo "$output" | tail -n 1 | awk '{print $NF}' > "$run_dir/compute_job_id"
'''

# Delete this machine's testing versions in the base path the latest deploy
# published to, except the newest few.  A testing version has a test load
# script or an environment but no release load script.  A released version
# keeps its environment, but loses any test load script.
SCRIPTS['clean'] = r'''
cd "$checkout" || exit 1
for latest in deploy_runs/*/latest; do
  if [ -e "$latest" ] && [ ! -f "$latest/exit_code" ]; then
    echo "Error: $(readlink -f "$latest") has no exit code, so its deploy may"
    echo "still be running.  Clean up once it has ended."
    exit 1
  fi
done
copy="$(sed -n 's/^Writing shared load-script copy: //p' \
  "deploy_runs/$machine/latest/deploy.log" 2>/dev/null | tail -n 1)"
if [ -z "$copy" ]; then
  echo "Error: the latest deploy for $machine here published no load script,"
  echo "so its base path is not known."
  exit 1
fi
cd "$(dirname "$copy")" || exit 1
echo "In $(pwd):"
_remove() {
  local path
  for path in "$@"; do
    [ -e "$path" ] || continue
    if [ "$delete" = true ]; then
      echo "  delete        $path"
      rm -rf "$path" || exit 1
    else
      echo "  would delete  $path"
    fi
  done
}
versions="$( { ls test_e3sm_unified_*_"$machine".sh
               ls -d e3smu_[0-9]*/"$machine"; } 2>/dev/null \
  | sed -e "s/^test_e3sm_unified_\(.*\)_$machine\.sh$/\1/" \
        -e "s|^e3smu_\(.*\)/$machine$|\1|" -e 's/_/./g' | sort -u)"
testing=""
for version in $versions; do
  script="test_e3sm_unified_${version}_$machine.sh"
  dir="e3smu_${version//./_}/$machine"
  if [ -e "load_e3sm_unified_${version}_$machine.sh" ]; then
    _remove "$script"
  else
    time="$(stat -c %Y "$script" "$dir" 2>/dev/null | sort -n | tail -n 1)"
    testing="$testing$time $version"$'\n'
  fi
done
count=0
for version in $(printf '%s' "$testing" | sort -rn | awk '{print $2}'); do
  count=$((count + 1))
  if [ "$count" -le "$keep" ]; then
    echo "  keep          $version"
    continue
  fi
  _remove "test_e3sm_unified_${version}_$machine.sh" \
    "e3smu_${version//./_}/$machine"
  if [ "$delete" = true ]; then
    rmdir "e3smu_${version//./_}" 2>/dev/null
  fi
done
'''


def main():
    """Run a command of the utility on a machine"""
    args = _parse_args(sys.argv[1:])
    machines, job_commands = _read_config(args.config_file)
    machine = args.machine
    if args.local:
        host, checkout = None, REPO_ROOT
    elif machine in machines:
        host, checkout = machines[machine]
    else:
        sys.exit(
            f'Error: {args.config_file} has no [machines] line for '
            f'{machine}.  Add one, or pass --local on {machine} itself.'
        )

    values = {'checkout': checkout, 'machine': machine}
    if args.command == 'sync':
        target = _target(args)
        print(
            f'Bringing {machine} to {target["commit"][:12]} of '
            f'{target["branch"]} from {target["repo"]}'
        )
        values.update(target)
    elif args.command == 'start':
        values['command'] = ['./deploy.py', '--machine', machine]
        values['command'] += args.deploy_args
        values['force'] = 'true' if args.force else 'false'
    elif args.command == 'status':
        values['tail'] = args.tail
    elif args.command == 'clean':
        values['keep'] = args.keep
        values['delete'] = 'true' if args.delete else 'false'
    else:
        values['submit_command'] = job_commands.get(machine, '')
        values['job_command_py'] = JOB_COMMAND_PY
        values['submit_job'] = 'true' if args.submit else 'false'
    # deleting environments can take a long time
    timeout = None if args.command == 'clean' else 900
    sys.exit(_run(host, values, SCRIPTS[args.command], timeout))


def _run(host, values, script, timeout):
    """Run a script in a login shell on a machine, returning its exit code"""
    lines = []
    for name, value in values.items():
        if isinstance(value, list):
            items = ' '.join(shlex.quote(str(item)) for item in value)
            lines.append(f'{name}=({items})')
        else:
            lines.append(f'{name}={shlex.quote(str(value))}')
    text = '\n'.join(lines) + PRELUDE + script

    if host is None:
        command = ['bash', '-l', '-s']
        # a clean login shell, as over ssh
        env = {
            name: os.environ[name]
            for name in ['HOME', 'USER', 'LOGNAME', 'TERM']
            if name in os.environ
        }
    else:
        command = ['ssh', '-o', 'BatchMode=yes', host, 'bash -l -s']
        env = None
    try:
        result = subprocess.run(
            command,
            input=text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        sys.exit(f'Error: {host or "the script"} did not finish in time.')

    output = result.stdout.partition(MARKER + '\n')[2]
    if not output and result.returncode != 0:
        # the script never ran, so show why
        print(result.stderr.strip(), file=sys.stderr)
        if host is not None:
            print(
                f'Error: could not run on {host}.  Is the requester logged '
                f'in there?',
                file=sys.stderr,
            )
    print(output, end='')
    return result.returncode


def _target(args):
    """The repo, branch and commit to sync to, by default this checkout's"""
    branch = args.branch or _git('symbolic-ref', '--short', 'HEAD')
    repo = args.repo
    if repo is None:
        remote = _git('config', f'branch.{branch}.remote')
        repo = _git('remote', 'get-url', remote)
    commit = args.commit or _git('rev-parse', 'HEAD')
    return {'repo': repo, 'branch': branch, 'commit': commit}


def _git(*args):
    result = subprocess.run(
        ['git'] + list(args),
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        sys.exit(
            f'Error: git {" ".join(args)} failed in {REPO_ROOT}.  Pass '
            f'--repo, --branch and --commit.\n{result.stderr.strip()}'
        )
    return result.stdout.strip()


def _read_config(filename):
    """The [machines] as host and checkout, and the [compute_job] commands"""
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(os.path.expanduser(filename))
    machines = {}
    if parser.has_section('machines'):
        for machine, value in parser.items('machines'):
            host, _, checkout = value.partition(':')
            machines[machine] = (host.strip(), checkout.strip())
    job_commands = {}
    if parser.has_section('compute_job'):
        job_commands = dict(parser.items('compute_job'))
    return machines, job_commands


def _parse_args(argv):
    # options after "--" are passed on to deploy.py
    deploy_args = []
    if '--' in argv:
        index = argv.index('--')
        argv, deploy_args = argv[:index], argv[index + 1 :]

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('machine', help='The machine, as mache names it')
    common.add_argument(
        '--local',
        action='store_true',
        help='Work in this checkout, on the machine itself, not over ssh',
    )
    common.add_argument(
        '-f',
        '--config-file',
        default=DEFAULT_CONFIG,
        help=f'The config file (default: {DEFAULT_CONFIG})',
    )

    parser = argparse.ArgumentParser(
        description='Drive ./deploy.py on HPC machines.  See '
        'utils/hpc_deploy/README.md.'
    )
    subparsers = parser.add_subparsers(dest='command', metavar='command')

    sync = subparsers.add_parser(
        'sync',
        parents=[common],
        help="Bring the machine's checkout to the commit to deploy",
    )
    sync.add_argument(
        '--repo', help='The repo, by default the one the branch tracks here'
    )
    sync.add_argument('--branch', help="The branch, by default this checkout's")
    sync.add_argument('--commit', help="The commit, by default this checkout's")

    start = subparsers.add_parser(
        'start',
        parents=[common],
        help='Run ./deploy.py --machine <machine> in the background.  Options '
        'after "--" are passed on to deploy.py.  Agents run this only with '
        "the requester's permission.",
    )
    start.add_argument(
        '--force',
        action='store_true',
        help='Start even if a deploy in this checkout has no exit code',
    )

    status = subparsers.add_parser(
        'status', parents=[common], help='Show how the latest deploy is going'
    )
    status.add_argument(
        '--tail', type=int, default=0, help='Show the end of the deploy log'
    )

    compute_test = subparsers.add_parser(
        'compute-test',
        parents=[common],
        help="Show the job that runs the latest deploy's tests on a compute "
        'node',
    )
    compute_test.add_argument(
        '--submit',
        action='store_true',
        help="Submit the job.  Agents pass this only with the requester's "
        'permission.',
    )

    clean = subparsers.add_parser(
        'clean',
        parents=[common],
        help="Show this machine's testing versions that would be deleted",
    )
    clean.add_argument(
        '--keep',
        type=int,
        default=2,
        help='How many of the newest testing versions to keep (default: 2), '
        '0 after a release',
    )
    clean.add_argument(
        '--delete',
        action='store_true',
        help="Delete them.  Agents pass this only with the requester's "
        'permission.',
    )

    args = parser.parse_args(argv)
    if args.command is None:
        parser.error('choose a command')
    if deploy_args and args.command != 'start':
        parser.error('only start passes options after "--" to deploy.py')
    args.deploy_args = deploy_args
    return args


if __name__ == '__main__':
    main()
