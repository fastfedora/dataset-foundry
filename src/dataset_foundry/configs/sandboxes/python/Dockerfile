FROM python:3.11-slim

# Avoid buffering stdout and stderr and disable creating `__pycache__` directories
ENV PYTHONUNBUFFERED="1"
ENV PYTHONDONTWRITEBYTECODE="1"

# Allow Python packages to be installed without a virtual environment
ENV PIP_BREAK_SYSTEM_PACKAGES="1"

# Prevent pip from checking for new versions & cluttering up stderr with warnings
ENV PIP_DISABLE_PIP_VERSION_CHECK="1"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Quiet warning about new pip release
RUN pip install --upgrade pip

# Install Python testing dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-mock

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash guest

# Copy the setup-repo and init scripts. The Docker build context is `configs` (see `sandbox.yml`),
# so these paths are relative to `src/dataset_foundry/configs`.
COPY shared/setup-repo.sh /usr/local/bin/setup-repo.sh
RUN chmod +x /usr/local/bin/setup-repo.sh
COPY sandboxes/python/init.sh /usr/local/bin/init.sh
RUN chmod +x /usr/local/bin/init.sh

# Change ownership of workspace directory to guest user
RUN chown -R guest:guest /workspace

USER guest

# Run init script, then execute the command passed to the container
ENTRYPOINT ["sh", "-c", "/usr/local/bin/init.sh && exec \"$@\"", "--"]

# Default command (can be overridden)
CMD ["python"]