import logging
from typing import Callable, Union, Optional, List
from pathlib import Path

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...core.key import Key
from ...types.item_action import ItemAction
from ...utils.params.resolve_item_value import resolve_item_value
from ...utils.unit_tests.run_python_unit_tests import run_python_unit_tests
from ...utils.unit_tests.parse_python_unit_test_results import parse_python_unit_test_results
from ...utils.docker.sandbox_runner import SandboxRunner

logger = logging.getLogger(__name__)

def run_unit_tests(
        filename: Union[Callable,Key,str],
        dir: Union[Callable,Key,str] = Key("context.input_dir"),
        property: Union[Callable,Key,str] = "test_result",
        sandbox: Optional[Union[Callable,Key,str]] = None,
        stream_logs: Union[Callable,Key,bool] = False,
        timeout: Union[Callable,Key,int] = 300,
    ) -> ItemAction:
    async def run_unit_tests_action(item: DatasetItem, context: Context):
        resolved_filename = resolve_item_value(filename, item, context, required_as="filename")
        resolved_dir = resolve_item_value(dir, item, context, required_as="dir")
        resolved_property = resolve_item_value(property, item, context, required_as="property")
        resolved_sandbox = resolve_item_value(sandbox, item, context)
        resolved_stream_logs = resolve_item_value(stream_logs, item, context)
        resolved_timeout = resolve_item_value(timeout, item, context)

        if resolved_sandbox:
            if isinstance(resolved_sandbox, str):
                sandbox_manager = SandboxRunner(resolved_sandbox)
            else:
                raise ValueError("Sandbox must be a string name of a sandbox")

            command = [f"python -m pytest -v '{resolved_filename}'"]

            logger.info(f"Running tests in sandbox with command: {' '.join(command)}")
            sandbox_result = await sandbox_manager.run(
                target_file=resolved_filename,
                workspace_dir=resolved_dir,
                command=command,
                timeout=resolved_timeout,
                stream_logs=resolved_stream_logs
            )

            result = parse_python_unit_test_results(sandbox_result)
            result.command = command
        else:
            # Run tests locally
            result = run_python_unit_tests(Path(resolved_dir) / resolved_filename)

        item.push({ resolved_property: result }, run_unit_tests)

    return run_unit_tests_action



