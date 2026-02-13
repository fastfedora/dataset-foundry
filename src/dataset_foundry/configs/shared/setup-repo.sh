#!/bin/bash
# Install any dependencies or run any setup scripts (which install dependencies & seed databases),

dir="${1:-.}"

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
