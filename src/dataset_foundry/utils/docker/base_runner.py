"""
Base container runner for managing running commands within Docker containers.
"""

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from docker.types import Mount
from pydantic import BaseModel
import yaml

from ..params.resolve_environment_dict import resolve_environment_dict
from .container_manager import BuildConfig, ContainerConfig, ContainerManager

logger = logging.getLogger(__name__)
base_configs_dir = Path(__file__).parent.parent.parent / "configs"


class LogsConfig(BaseModel):
    """Configuration for container logs."""
    format: Optional[str] = None


class RunnerConfig(BaseModel):
    """Base configuration for container runners."""
    container: ContainerConfig
    logs: Optional[LogsConfig] = None


class BaseRunner:
    """Base class for container-based runners."""

    _config: Optional[RunnerConfig] = None

    def __init__(
        self,
        runner_name: str,
        configs_dir: str,
        config_filename: str,
        container_manager: Optional[ContainerManager] = None
    ):
        """
        Initialize the base container runner.

        Args:
            runner_name: Name of the runner configuration
            configs_dir: Directory where the configurations for runners are stored, either absolute
                or relative to the `src/configs` directory.
            config_filename: Name of the configuration file for this runner.
            container_manager: Optional container manager instance
        """
        self.runner_name = runner_name
        self.configs_dir = configs_dir
        self.config_filename = config_filename
        self.container_manager = container_manager or ContainerManager()
        self._config: Optional[RunnerConfig] = None

    def _get_config_path(self) -> Path:
        """Get the path to the runner configuration files."""
        if not Path(self.configs_dir).is_absolute():
            return base_configs_dir / self.configs_dir / self.runner_name
        else:
            return Path(self.configs_dir) / self.runner_name

    def _parse_config(self, config_data: dict) -> RunnerConfig:
        """Parse the configuration data into a RunnerConfig object."""
        return RunnerConfig(
            name=self.runner_name,
            container=ContainerConfig(**config_data['container']),
            logs=LogsConfig(**config_data.get('logs', {})),
        )

    async def _load_config(self) -> RunnerConfig:
        """Load configuration from YAML file."""
        config_path = self._get_config_path() / self.config_filename

        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            logger.info(f"Loaded configuration from {config_path}")

            return self._parse_config(config_data)
        else:
            raise ValueError(
                f"Unknown runner type: {self.runner_name}: "
                f"No configuration found at {config_path}"
            )

    async def _ensure_image_built(self, stream_logs: bool = False):
        """Ensure the container's Docker image is built."""
        if self._config is None:
            self._config = await self._load_config()

        config = deepcopy(self._config.container.build or BuildConfig())
        runner_config_dir = self._get_config_path()

        if not config.context:
            config.context = runner_config_dir
        elif not Path(config.context).is_absolute():
            config.context = runner_config_dir / config.context

        config.args = resolve_environment_dict(config.args)
        build_required = self._image_build_required(config)

        # `build_required` can only be false if the image exists
        if not build_required:
            logger.info(f"Image {self._config.container.image} already exists")
            return

        if config.context and Path(config.context).exists():
            await self.container_manager.build_image(
                image_name=self._config.container.image,
                config=config,
                stream_logs=stream_logs
            )
        else:
            raise ValueError(f"No context found for {self.runner_name} at {config.context}")

    def _image_build_required(self, build_config: BuildConfig) -> bool:
        """Check if the image needs to be rebuilt."""
        try:
            image_name = self._config.container.image
            last_built = self.container_manager.get_image_last_built(image_name)

            if last_built is None:
                return True

            dockerfile_mtime = self._get_dockerfile_last_modified(build_config)

            if not dockerfile_mtime or dockerfile_mtime > last_built:
                return True

            return False
        except Exception as e:
            return True

    def _get_dockerfile_last_modified(self, build_config: BuildConfig) -> Optional[float]:
        """Get the last modified time of the Dockerfile."""
        dockerfile_path = build_config.dockerfile or "Dockerfile"

        if not Path(dockerfile_path).exists():
            dockerfile_path = build_config.context / dockerfile_path

        dockerfile = Path(dockerfile_path)

        return dockerfile.stat().st_mtime if dockerfile.exists() else None

    def _get_working_dir(self, config: ContainerConfig) -> str:
        """Get the working directory for the container."""
        image_config = self.container_manager.get_image_config(config.image)
        working_dir = config.working_dir or image_config.get("WorkingDir")

        if not working_dir:
            raise ValueError(f"No working directory configured for {self.runner_name}")

        return working_dir

    def _prepare_volumes_config(
        self,
        config: ContainerConfig,
        volumes: List[Mount],
        output_dir: Optional[Path] = None
    ) -> None:
        """Configure volumes for the container."""
        if not config.volumes:
            config.volumes = []
        else:
            for volume in config.volumes:
                if not Path(volume['Source']).is_absolute():
                    if output_dir:
                        volume['Source'] = str(output_dir / volume['Source'])
                    else:
                        raise ValueError(f"No output directory configured for {self.runner_name}")

        if volumes:
            config.volumes.extend(volumes)

    def _prepare_environment_config(
        self,
        config: ContainerConfig,
        environment: Optional[Dict[str, Any]] = None
    ) -> None:
        """Prepare environment configuration for the container."""
        if not config.environment:
            config.environment = {}

        if environment:
            config.environment.update(environment)

        config.environment = resolve_environment_dict(config.environment)

    def _prepare_test_plugins_config(
        self,
        config: ContainerConfig,
        test_plugins_dir: Optional[Path] = None
    ) -> None:
        """
        Configure pytest plugins for the container.

        If `test_plugins_dir` is provided, mounts it read-only at `/pytest-plugins` inside the
        container and prepends `/pytest-plugins` to `PYTHONPATH` so that any modules in the
        directory can be imported by Python code running in the container.
        """
        if not test_plugins_dir:
            return

        test_plugins_dir = test_plugins_dir.resolve()
        if not test_plugins_dir.exists() or not test_plugins_dir.is_dir():
            raise ValueError(
                f"Test plugins directory {test_plugins_dir} does not exist or is not a directory"
            )

        if not config.volumes:
            config.volumes = []

        config.volumes.append(
            Mount(target="/pytest-plugins", source=str(test_plugins_dir), type="bind", read_only=True)
        )

        if not config.environment:
            config.environment = {}

        pythonpath = config.environment.get("PYTHONPATH") or ""
        if pythonpath:
            pythonpath = ":" + pythonpath
        config.environment["PYTHONPATH"] = "/pytest-plugins" + pythonpath

        # Configure pytest plugins so they are loaded automatically when pytest runs in the sandbox.
        pytest_plugins = config.environment.get("PYTEST_PLUGINS") or ""

        for test_plugin_file in sorted(test_plugins_dir.glob("*.py")):
            name = test_plugin_file.stem
            pytest_plugins = f"{pytest_plugins},{name}" if pytest_plugins else name

        if pytest_plugins:
            config.environment["PYTEST_PLUGINS"] = pytest_plugins
