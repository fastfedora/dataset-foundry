FROM homebrew/ubuntu22.04
USER root

# Install system dependencies, including Python and pip for repo setup scripts
RUN apt-get update && \
    apt-get install -y \
      curl \
      git \
      build-essential \
      software-properties-common \
      python3 \
      python3-pip \
      python3-venv \
      python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Provide common `python` / `pip` entrypoints expected by repos
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# brew expects to run as a non-root user
USER linuxbrew

ENV HOMEBREW_NO_AUTO_UPDATE=1

RUN brew install --cask codex

WORKDIR /workspace

ENV LANG=en_US.UTF-8
ENV PYTHONUNBUFFERED=1

# Allow Python packages to be installed without a virtual environment
ENV PIP_BREAK_SYSTEM_PACKAGES="1"

USER root

# Copy the setup-repo script. The Docker build context is `configs` (see `sandbox.yml`), so these
# paths are relative to `src/dataset_foundry/configs`.
COPY shared/setup-repo.sh /usr/local/bin/setup-repo.sh
RUN chmod +x /usr/local/bin/setup-repo.sh

USER linuxbrew

# Default command (will be overridden by entrypoint)
ENTRYPOINT ["sh", "-c", "/usr/local/bin/setup-repo.sh \"$REPO_DIR\" && exec \"$@\"", "--"]
