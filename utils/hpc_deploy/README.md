# E3SM-Unified HPC deploy utility

`hpc_deploy.py` drives this repo's `./deploy.py` on several HPC machines from
your own computer.  Each command runs a short script in a login shell on the
machine, over the ssh connection you open by logging in.  On a machine you
cannot reach that way, such as Frontier, it runs with `--local`.  An AI agent
can run it for you, following [AGENTS.md](AGENTS.md).

```bash
hpc_deploy.py sync <machine>                 # bring the checkout to this checkout's HEAD
hpc_deploy.py start <machine> [-- <options>] # run ./deploy.py --machine <machine> [<options>]
hpc_deploy.py status <machine> [--tail N]    # running or exit code, test results, log
hpc_deploy.py compute-test <machine> [--submit]  # run deploy.py's tests on a compute node
hpc_deploy.py clean <machine> [--keep N] [--delete]  # delete old testing versions
```

- **`sync`** fetches the branch from the repo it tracks, then checks out the
  commit and its feedstock submodule in the machine's checkout.  It clones
  the checkout if it is missing, from GitHub over https, so the machine needs
  no GitHub key.  It stops if the checkout has changes to tracked files or
  the commit has not been pushed.
- **`start`** runs `./deploy.py` in the background with `nohup`, so it keeps
  going if the connection closes.  It refuses to run while a deploy in the
  same checkout has no exit code.
- **`status`** shows the checkout, whether the deploy is running or its
  exit code, the environment test results and shared load script from the
  log, and the compute-node test.
- **`compute-test`** shows the one-node job that runs the test scripts
  `deploy.py` wrote, where the load script loads the compute environment.
  With `--submit`, it submits the job.  It takes the account, queue and
  other settings from mache's config for the machine, using the deployed
  environment's mache.
- **`clean`** lists the machine's testing versions (deployed without
  `--release`), other than the newest `N` (2 by default), in the base path
  the latest deploy published to.  With `--delete`, it deletes their
  environments and test load scripts.  It also deletes any test load
  script left beside a released version.  After a release, use `--keep 0`.
  It never deletes a released environment or another machine's files.

## Setup

- `~/.config/e3sm_unified_deploy.cfg`, copied from [example.cfg](example.cfg),
  with a `[machines]` line for each machine.
- An alias for each machine in `~/.ssh/config` that shares one connection,
  for example:
  ```
  Host *
      ControlMaster auto
      ControlPath ~/.ssh/connections/%r@%h:%p
  ```
  Log in to each machine and leave the session open while you work.
  `ControlPersist <time>` keeps it open after you log out.

The utility needs Python 3.6 or newer and nothing else.

## Layout

In each machine's checkout:

```
deploy_runs/<machine>/
  latest -> <run id>
  <run id>/                   the UTC start time, such as 20261009T171500Z
    deploy.log  exit_code     deploy.py's output and exit code
    pid  node                 its process and login node
    test_load_*.sh            the test scripts deploy.py wrote
    compute_test_job.sh  compute_job_id  compute_job.out
    compute_test.log  compute_exit_code
```
