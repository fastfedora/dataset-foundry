#!/bin/bash
# Install any dependencies or run any setup scripts (which install dependencies & seed databases),
# wrapping the output in ::setup:start:: and ::setup:end:: tags for both stdout and stderr.

dir="${1:-.}"
original_dir="$(pwd)"

echo "::setup:start::" | tee /dev/stderr

if [ -n "${SKIP_REPO_SETUP}" ]; then
    echo "Skipping repo setup because SKIP_REPO_SETUP is set"
    echo "::setup:end:0::" | tee /dev/stderr
    exit 0
fi

# Run all scripts from the repo directory; if no repo directory exists yet, exit with success
cd "$dir" 2>/dev/null || {
    echo "Skipping repo setup because no repo detected in ${dir}"
    echo "::setup:end:0::" | tee /dev/stderr
    exit 0
}


if [ -f "script/setup" ]; then
    echo "Running setup script..."
    chmod u+x script/*
    bash -e ./script/setup
elif [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    echo "Installing dependencies from pyproject.toml..."
    pip install -e .
else
    echo "Skipping setup and dependency installation. No setup details found in working directory."
fi

setup_status=$?

cd "$original_dir" || echo "Warning: failed to restore original directory $original_dir" >&2

echo "::setup:end:${setup_status}::" | tee /dev/stderr
exit $setup_status
