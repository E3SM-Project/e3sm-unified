# `cime-env` deployment

This directory uses `mache.deploy` to create and publish a shared `cime-env`
pixi environment on machines supported by the pinned `mache` release.

Because this is a shared deployment, do not redeploy in place. Each new
deployment should use a new `project.version` so it creates a new versioned
environment instead of clobbering the existing shared one.

The three files you will usually touch are:

- `deploy/config.yaml.j2`: the published `cime-env` version
- `deploy/pins.cfg`: pinned Python, `mache`, and `evv4esm` versions
- `deploy/pixi.toml.j2`: the actual pixi dependency template

## Update the `cime-env` version

The published version string lives in `project.version` in
`deploy/config.yaml.j2`.

Update this version every time you deploy a new shared environment. That is
how `cime-env` gets a new install location instead of overwriting the current
shared deployment.

1. Edit `deploy/config.yaml.j2` and update:

   ```yaml
   project:
     version: "1.10.0"
   ```

2. Redeploy:

   ```bash
   ./deploy.py
   ```

This creates a versioned install under the machine's shared `base_path` using
the form:

```text
<base_path>/cime_env_<version>/<machine>/pixi
```

The deployment also refreshes the shared load-script alias
`load_latest_cime_env.sh`.

## Update dependencies in the environment

### Update `evv4esm`

`evv4esm` is pinned in `deploy/pins.cfg` and consumed by
`deploy/pixi.toml.j2`.

1. Edit `deploy/pins.cfg`:

   ```ini
   [pixi]
   evv4esm = 0.6.2
   ```

2. Redeploy:

   ```bash
   ./deploy.py
   ```

For shared deployments, make sure you also bump `project.version` first so the
updated dependency set is published as a new versioned environment.

The post-publish smoke test imports `evv4esm` and runs `evv --help`, so a bad
`evv4esm` update should fail during deploy.

### Update other dependencies

- Update `python` in `deploy/pins.cfg` if you want a different Python version.
- Update `deploy/pixi.toml.j2` if you want to add, remove, or change other
  pixi dependencies.
- Leave the Compy compatibility pins alone unless you intentionally want to
  change the legacy glibc behavior in `deploy/hooks.py`.

After any dependency change, redeploy with:

```bash
./deploy.py
```

Before doing so, update `project.version` in `deploy/config.yaml.j2` so the
new environment is deployed to a new shared location.

## Deploy on a supported machine

From this directory, deployment is normally just:

```bash
./deploy.py
```

`./deploy.py` will:

- read the pins from `deploy/pins.cfg`
- bootstrap the pinned `mache` version
- detect the current machine when possible
- install the pixi environment
- publish or refresh `load_latest_cime_env.sh`

Before running `./deploy.py`, always update `project.version` in
`deploy/config.yaml.j2` for a shared deployment. The version determines the
versioned install directory, so bumping it is what prevents a new deploy from
clobbering an existing shared environment.

If automatic machine detection does not do what you want, pass the machine
explicitly:

```bash
./deploy.py --machine chrysalis
```

You can also choose where a copy of the generated load script is written:

```bash
./deploy.py --load-script-dir /path/to/scripts
```

You can override the pixi install location with `--pixi-path`:

```bash
./deploy.py --pixi-path /path/to/test/pixi
```

`--pixi-path` and `--load-script-dir` can be used together for a test deploy
that does not modify the shared `cime-env` install location or the shared
`load_latest_cime_env.sh` alias:

```bash
./deploy.py --pixi-path /path/to/test/pixi --load-script-dir /path/to/scripts
```

Supported machines come from the pinned `mache` release, not from this README.
With the current `mache` pin, machine configs exist for:

- `andes`
- `aurora`
- `bebop`
- `chicoma-cpu`
- `chrysalis`
- `compy`
- `dane`
- `frontier`
- `improv`
- `pm-cpu`
- `pm-gpu`
- `polaris`

In practice, deployment only works where the machine config provides the
`[e3sm_unified]` settings needed by `deploy/hooks.py`, especially a shared
`base_path` you can write to.
