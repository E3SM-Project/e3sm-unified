#!/bin/bash
# line to trigger test on PR
# always start unset
unset abort_message

# start with default of 0
rc=0

# Abort with message
function abort () {
    echo "$abort_message" >&2
    exit $rc
}

# Check if abort is necessary, and if so do it
function check_rc () {
    if [ $# -gt 0 ];
    then
        abort_message="$1"
    fi

    if [ $rc -ne 0 ];
    then
        abort
    fi

    if [ $rc -eq 0 -a "$2" != "" ];
    then
        printf "$2"
    fi
}

# Check if abort is necessary, fetching rc first
function check_last_rc () {
    # must be the first command of the function
    rc=$?
    check_rc "$@"
}

echo "Loading conda profile"
. /opt/conda/etc/profile.d/conda.sh

echo "Activating e3sm conda environment"
conda activate e3sm-unified-nox
check_last_rc "Could not source e3sm-unified conda environment\n"

# Try to run some simple help commands
for cmd in "e3sm_diags" "processflow" "mpas_analysis"
do
    $cmd --help
    check_last_rc "$cmd help failed\n"
done
