#!/bin/bash
# Install any dependencies or run any setup scripts (which install dependencies & seed databases),
# wrapping the output in ::setup:start:: and ::setup:end:: tags for both stdout and stderr.

dir="${1:-.}"

echo "::setup:start::" | tee /dev/stderr

if [ -n "${SKIP_REPO_SETUP}" ]; then
    echo "Skipping repo setup because SKIP_REPO_SETUP is set"
    echo "::setup:end:0::" | tee /dev/stderr
    exit 0
fi

if [ -f "$dir/script/setup" ]; then
    echo "Running setup script..."
    chmod u+x "$dir"/script/*
    "$dir/script/setup"
elif [ -f "$dir/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r "$dir/requirements.txt"
elif [ -f "$dir/pyproject.toml" ]; then
    echo "Installing dependencies from pyproject.toml..."
    pip install -e "$dir"
else
    echo "Skipping setup and dependency installation. No setup details found in working directory."
fi

setup_status=$?

echo "::setup:end:${setup_status}::" | tee /dev/stderr
exit $setup_status
