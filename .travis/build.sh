#!/bin/bash

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

definitionfile=$1
definition=`echo $definitionfile | sed 's/.def//'`
imagefile="${definition}.simg"

echo "Creating $imagefile using $definitionfile..."
sudo singularity build $imagefile ${definitionfile}
check_last_rc "Build of $definitionfile failed\n"
echo

# Example testing using run (you could also use test command)

echo "Trying simple echo exec of $imagefile"
singularity exec $imagefile echo "Working"
check_last_rc "Basic exec failed\n"
echo
