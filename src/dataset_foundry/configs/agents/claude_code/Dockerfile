FROM node:20

ARG TZ
ENV TZ="$TZ"

# Avoid buffering stdout and stderr and disable creating `__pycache__` directories
ENV PYTHONUNBUFFERED="1"
ENV PYTHONDONTWRITEBYTECODE="1"

# Install basic development tools and iptables/ipset
RUN set -eu; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    less \
    git \
    procps \
    sudo \
    man-db \
    unzip \
    gnupg2 \
    gh \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    aggregate \
    jq \
    yq; \
  rm -rf /var/lib/apt/lists/*;

# Install Python globally along with modules commonly used for development
RUN set -eu; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    python3-pytest \
    python3-pytest-cov; \
  rm -rf /var/lib/apt/lists/*;

# Create python symlink for compatibility
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
  ln -sf /usr/bin/pip3 /usr/bin/pip

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/node/.claude && \
  chown -R node:node /workspace /home/node/.claude

WORKDIR /workspace

# Install `git-delta` for better diffs
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/0.18.2/git-delta_0.18.2_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_0.18.2_${ARCH}.deb" && \
  rm "git-delta_0.18.2_${ARCH}.deb"

# Set up non-root user
USER node

# Install global packages
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Install Claude
RUN npm install -g @anthropic-ai/claude-code

# Copy firewall scripts and config file. The Docker build context is `configs` (see `sandbox.yml`),
# so these paths are relative to `src/dataset_foundry/configs`.
COPY agents/claude_code/firewall/* /usr/local/bin/firewall/

USER root

# Copy the shared setup-repo script
COPY shared/setup-repo.sh /usr/local/bin/setup-repo.sh
RUN chmod +x /usr/local/bin/setup-repo.sh

RUN chmod +x /usr/local/bin/firewall/init.sh && \
  chmod +x /usr/local/bin/firewall/allow-domains.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/firewall/init.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall

USER node

# Initialize firewall, run repo setup and then execute the command passed to the container
ENTRYPOINT ["sh", "-c", "sudo /usr/local/bin/firewall/init.sh && /usr/local/bin/setup-repo.sh \"$REPO_DIR\" && exec \"$@\"", "--"]
