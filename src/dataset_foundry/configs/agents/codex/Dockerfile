FROM homebrew/ubuntu22.04
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl git build-essential software-properties-common && \
    rm -rf /var/lib/apt/lists/*

RUN brew install codex

WORKDIR /workspace

ENV LANG=en_US.UTF-8
ENV PYTHONUNBUFFERED=1

# Copy the setup-repo script. The Docker build context is `configs` (see `sandbox.yml`), so these
# paths are relative to `src/dataset_foundry/configs`.
COPY shared/setup-repo.sh /usr/local/bin/setup-repo.sh
RUN chmod +x /usr/local/bin/setup-repo.sh

# Default command (will be overridden by entrypoint)
ENTRYPOINT ["sh", "-c", "/usr/local/bin/setup-repo.sh \"$REPO_DIR\" && exec \"$@\"", "--"]
