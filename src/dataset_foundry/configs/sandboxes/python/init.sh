#!/bin/bash
# Add local bin directory to PATH to quiet pip warning
export PATH="$HOME/.local/bin:$PATH"

. /usr/local/bin/setup-repo.sh "$PWD"
