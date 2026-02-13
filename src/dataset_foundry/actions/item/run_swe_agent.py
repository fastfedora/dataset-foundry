from typing import Callable, Union, Optional
from pathlib import Path
import asyncio
import shutil
import yaml

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...core.key import Key
from ...types.item_action import ItemAction
from ...utils.params.resolve_item_value import resolve_item_value
from ...utils.format.format_template import format_template
from ...utils.docker.agent_runner import AgentRunner, AgentInputs
from ...utils.docker.container_manager import ContainerManager

def run_swe_agent(
        instructions: Union[Callable, Key, str] = Key("context.swe_agent.instructions"),
        prompt: Union[Callable, Key, str] = Key("context.prompts.implement_spec"),
        spec: Union[Callable, Key, str, dict] = Key("spec"),
        output_dir: Union[Callable, Key, str] = Key("context.output_dir"),
        agent: Union[Callable, Key, str] = Key("context.swe_agent.type"),
        repo_path: Optional[Union[Callable, Key, str]] = None,
        timeout: Union[Callable, Key, int] = 3600,  # 1 hour default
        max_retries: Union[Callable, Key, int] = 3,
        output_key: Union[Callable, Key, str] = "agent_result",
        stream_logs: Union[Callable, Key, bool] = False,
        skip_repo_setup: Union[Callable, Key, bool] = False,
    ) -> ItemAction:
    """
    Run a software engineering agent in a Docker container.

    Args:
        instructions: General operating instructions for the agent (rendered as AGENTS.md)
        prompt: The specific prompt that references the spec
        spec: Specification data (string or dict, rendered as JSON/YAML)
        output_dir: Directory where agent output should be saved
        agent: Name of the agent to run (e.g., "codex", "claude-code")
        repo_path: Optional path to pre-existing repository
        timeout: Maximum execution time in seconds
        max_retries: Maximum number of retry attempts
        output_key: Key to store the agent result in item data
        stream_logs: Whether to stream container logs to logger.info (default: False)
        skip_repo_setup: If True, skips the setting up the repo in the sandbox. Use when you want
            the agent to access the repo sample before any setup is performed (default: False)
    """

    async def run_swe_agent_action(item: DatasetItem, context: Context):
        resolved_instructions = resolve_item_value(instructions, item, context, required_as="instructions")
        resolved_prompt = resolve_item_value(prompt, item, context, required_as="prompt")
        resolved_spec = resolve_item_value(spec, item, context, required_as="spec")
        resolved_output_dir = resolve_item_value(output_dir, item, context, required_as="output_dir")
        resolved_agent = resolve_item_value(agent, item, context, required_as="agent")
        resolved_repo_path = resolve_item_value(repo_path, item, context) if repo_path else None
        resolved_timeout = resolve_item_value(timeout, item, context)
        resolved_max_retries = resolve_item_value(max_retries, item, context)
        resolved_output_key = resolve_item_value(output_key, item, context)
        resolved_stream_logs = resolve_item_value(stream_logs, item, context)
        resolved_skip_repo_setup = resolve_item_value(skip_repo_setup, item, context)

        if isinstance(resolved_output_dir, str):
            resolved_output_dir = format_template(resolved_output_dir, {
                "id": item.id,
                **item.data
            })

        if isinstance(resolved_prompt, str):
            resolved_prompt = format_template(resolved_prompt, {
                "id": item.id,
                **item.data
            })

        output_path = Path(resolved_output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        agent_inputs = await _prepare_agent_inputs(
            item, context, resolved_instructions, resolved_prompt,
            resolved_spec, output_path, resolved_repo_path,
            skip_repo_setup=resolved_skip_repo_setup
        )
        agent_runner = AgentRunner(
            agent_type=resolved_agent,
            container_manager=ContainerManager()
        )

        # Execute agent with retry logic
        result = None
        last_error = None

        for attempt in range(resolved_max_retries):
            try:
                agent_inputs.context_data["attempt"] = attempt + 1

                result = await agent_runner.run(
                    inputs=agent_inputs,
                    output_dir=output_path,
                    timeout=resolved_timeout,
                    attempt=attempt + 1,
                    stream_logs=resolved_stream_logs
                )
                break
            except Exception as e:
                last_error = e
                if attempt < resolved_max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise last_error

        item.push({
            resolved_output_key: result,
        }, run_swe_agent)

    return run_swe_agent_action


async def _prepare_agent_inputs(
    item: DatasetItem,
    context: Context,
    instructions: str,
    prompt: str,
    spec: Union[str, dict],
    output_dir: Path,
    repo_path: Optional[str] = None,
    skip_repo_setup: bool = False,
) -> AgentInputs:
    """Prepare input files for the agent."""

    inputs_dir = output_dir / "input"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    instructions_file = inputs_dir / "AGENTS.md"
    instructions_file.write_text(instructions)

    spec_file = inputs_dir / "spec.yaml"
    if isinstance(spec, dict):
        with open(spec_file, 'w') as f:
            yaml.dump(spec, f, default_flow_style=False)
    else:
        spec_file.write_text(str(spec))

    # Copy existing repo if provided
    if repo_path:
        repo_source = Path(repo_path)
        if repo_source.exists():
            repo_dest = output_dir / "repo"
            if repo_source.is_dir():
                shutil.copytree(repo_source, repo_dest, dirs_exist_ok=True)
            else:
                shutil.copy2(repo_source, repo_dest)

    return AgentInputs(
        prompt=prompt,
        instructions_file=str(instructions_file),
        spec_file=str(spec_file),
        repo_path=str(output_dir / "repo") if repo_path else None,
        output_dir=str(output_dir),
        item_id=item.id,
        context_data={
            "attempt": 0,
        },
        skip_repo_setup=skip_repo_setup,
    )