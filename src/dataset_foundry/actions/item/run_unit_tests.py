import logging
import re
from typing import Callable, Union, Optional
from pathlib import Path

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...core.key import Key
from ...types.command_result import CommandResult
from ...types.unit_test_result import UnitTestResult

from ...types.item_action import ItemAction
from ...utils.params.resolve_item_value import resolve_item_value
from ...utils.unit_tests.run_python_unit_tests import run_python_unit_tests
from ...utils.unit_tests.parse_python_unit_test_results import parse_python_unit_test_results
from ...utils.docker.sandbox_runner import SandboxResult, SandboxRunner

logger = logging.getLogger(__name__)

SETUP_START = "::setup:start::"
SETUP_END_PATTERN = re.compile(r"::setup:end:(\d+)::")


def run_unit_tests(
        filename: Union[Callable,Key,str],
        dir: Union[Callable,Key,str] = Key("context.input_dir"),
        property: Union[Callable,Key,str] = "test_result",
        setup_property: Union[Callable,Key,str] = "setup_result",
        sandbox: Optional[Union[Callable,Key,str]] = None,
        stream_logs: Union[Callable,Key,bool] = False,
        timeout: Union[Callable,Key,int] = 300,
    ) -> ItemAction:
    async def run_unit_tests_action(item: DatasetItem, context: Context):
        resolved_filename = resolve_item_value(filename, item, context, required_as="filename")
        resolved_dir = resolve_item_value(dir, item, context, required_as="dir")
        resolved_property = resolve_item_value(property, item, context, required_as="property")
        resolved_setup_property = resolve_item_value(setup_property, item, context)
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
            pytest_result, setup_result = _parse_sandbox_result(sandbox_result)

            if pytest_result.returncode is not None:
                sandbox_result.stdout = pytest_result.stdout
                sandbox_result.stderr = pytest_result.stderr

                result = parse_python_unit_test_results(sandbox_result)
                result.command = command
            else:
                result = UnitTestResult(
                    command=command,
                    returncode=None,
                    num_passed=0,
                    num_failed=0,
                    stdout=pytest_result.stdout,
                    stderr=pytest_result.stderr
                )
        else:
            # Run tests locally
            result = run_python_unit_tests(Path(resolved_dir) / resolved_filename)

        item.push({ resolved_property: result }, run_unit_tests)

        if setup_result is not None and resolved_setup_property:
            item.push({ resolved_setup_property: setup_result }, run_unit_tests)

    return run_unit_tests_action


def _parse_sandbox_result(sandbox_result: SandboxResult) -> tuple[CommandResult, CommandResult]:
    """
    Parse sandbox result into pytest and setup command results.

    Looks for ::setup:start:: and ::setup:end:N:: in stdout and stderr. Content between those
    markers is the setup result; everything after the end marker is treated as pytest output. If no
    setup markers are present, setup is empty/success and all output is pytest.
    """
    pytest_stdout, setup_stdout, setup_stdout_code = _split_stream(sandbox_result.stdout)
    pytest_stderr, setup_stderr, setup_stderr_code = _split_stream(sandbox_result.stderr)

    setup_returncode = setup_stdout_code if setup_stdout_code is not None else setup_stderr_code
    pytest_returncode = sandbox_result.exit_code

    # End tag for setup not found or no pytest output indicates setup failed and pytest never ran
    if setup_returncode == -1 or (pytest_stdout == "" and pytest_stderr == ""):
        setup_returncode = sandbox_result.exit_code
        pytest_returncode = None

    return (
        CommandResult(
            command=[],
            returncode=pytest_returncode,
            stdout=pytest_stdout,
            stderr=pytest_stderr,
        ),
        CommandResult(
            command=[],
            returncode=setup_returncode,
            stdout=setup_stdout,
            stderr=setup_stderr,
        ),
    )


def _split_stream(output: str) -> tuple[str, str, Optional[int]]:
    """
    Split the output into pytest and setup sections.

    Args:
        output: The output to split

    Returns:
        A tuple containing the pytest content, the setup content, and the setup exit code
    """
    start_idx = output.find(SETUP_START)
    if start_idx == -1:
        # No start marker: treat all output as pytest content
        return output.strip("\n"), "", None

    content_after_start = output[start_idx + len(SETUP_START) :]
    end_match = SETUP_END_PATTERN.search(content_after_start)
    if not end_match:
        # Start marker present but no end marker: treat everything after start as setup content
        return "", content_after_start.strip("\n"), -1

    setup_content = content_after_start[: end_match.start()].strip("\n")
    pytest_content = content_after_start[end_match.end() :].strip("\n")

    return pytest_content, setup_content, int(end_match.group(1))
