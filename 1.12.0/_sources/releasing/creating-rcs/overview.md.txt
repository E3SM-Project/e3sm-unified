# Overview of Release Candidate Workflows

## What Is a Release Candidate?

A release candidate (RC) is a build intended for testing before a final
release. RCs allow us to validate compatibility across the E3SM analysis stack
and to ensure that tools and environments function correctly on supported HPC
platforms.

RC packages are published to special Conda labels (like `e3sm_diags_dev` or
 `e3sm_unified_dev`) to keep them separate from stable releases.

---

## Overview of the Process

There are two major workflows:

### 1. Creating RCs for Dependency Packages

These are individual tools like `e3sm_diags`, `zppy`, or `mpas_analysis` that
are used within the E3SM-Unified environment.

Go to: [Creating RCs for Dependency Packages](rc-dependencies.md)

---

### 2. Creating an RC for E3SM-Unified

This involves assembling a full test environment based on specific versions of
all dependencies — including RCs.

Go to: [Creating an E3SM-Unified RC](rc-e3sm-unified.md)

---

### 3. Troubleshooting Build Failures

Solving Conda environments during builds can fail for complex or subtle
reasons. This section provides detailed strategies for debugging, including
use of `conda_first_failure.py`.

Go to: [Troubleshooting Conda Build Failures](rc-troubleshooting.md)

---

Each page includes step-by-step examples, commands, and best practices
tailored to the E3SM-Unified release workflow.
