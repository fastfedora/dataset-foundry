"""
Sandbox manager for running unit tests in isolated Docker containers.
"""

import logging
from copy import deepcopy
from pathlib import Path
from typing import List, Optional

from docker.types import Mount
from pydantic import BaseModel

from .base_runner import BaseRunner, RunnerConfig
from .container_manager import ContainerConfig, ContainerResult

logger = logging.getLogger(__name__)


class SandboxConfig(RunnerConfig):
    """Configuration for a sandbox environment."""

class SandboxResult(ContainerResult):
    """Result from sandbox execution."""


class SandboxRunner(BaseRunner):
    """Manages sandbox environments for running code in isolated containers."""

    def __init__(self, sandbox_name: str, container_manager=None):
        """
        Initialize the sandbox runner.

        Args:
            sandbox_name: Name of sandbox to use
            container_manager: Optional container manager instance
        """
        super().__init__(sandbox_name, "sandboxes", "sandbox.yml", container_manager)

    async def run(
        self,
        target_file: Path,
        workspace_dir: Path,
        command: Optional[List[str]] = None,
        timeout: int = 300,
        stream_logs: bool = False
    ) -> SandboxResult:
        """
        Run code in a sandbox container.

        Args:
            target_file: Path to the target file to execute
            workspace_dir: Directory containing all files to mount
            command: Optional command to override the default
            timeout: Timeout for execution in seconds (default: 300)
            stream_logs: Whether to stream container logs

        Returns:
            SandboxResult with execution results
        """
        try:
            if self._config is None:
                self._config = await self._load_config()

            await self._ensure_image_built(stream_logs)

            container_config = self._create_container_config(
                workspace_dir,
                target_file,
                command,
            )

            logger.info(f"Running sandbox {self.runner_name}")
            container_result = await self.container_manager.run_container(
                container_config,
                timeout=timeout,
                stream_logs=stream_logs
            )
            result = SandboxResult(
                exit_code=container_result.exit_code,
                stdout=container_result.stdout,
                stderr=container_result.stderr,
                logs=container_result.logs,
                container_id=container_result.container_id
            )

            logger.info(f"Sandbox {self.runner_name} completed with exit code {result.exit_code}")
            return result

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            raise

    def _create_container_config(
        self,
        workspace_dir: Path,
        target_file: Path,
        command: Optional[List[str]] = None
    ) -> ContainerConfig:
        """Create container configuration for the sandbox."""
        if not command:
            raise ValueError("No command provided for sandbox")

        config = deepcopy(self._config.container)
        config.command = command

        working_dir = self._get_working_dir(config)

        # TODO: Maybe use a volume mount that copies files into the container instead of a bind
        #       mount so the sandbox runner isn't modifying the original sample unless we want it
        #       to. [fastfedora 25.Feb.26]
        self._prepare_volumes_config(config, [
            Mount(target=working_dir, source=str(workspace_dir), type="bind", read_only=False)
        ])
        self._prepare_environment_config(config)

        return config
