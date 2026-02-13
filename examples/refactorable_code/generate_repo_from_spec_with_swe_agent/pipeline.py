from pathlib import Path

from dataset_foundry.actions.dataset.load_dataset_from_directory import load_dataset_from_directory
from dataset_foundry.actions.item.log_item import log_item
from dataset_foundry.actions.item.set_item_metadata import set_item_metadata
from dataset_foundry.actions.item.run_swe_agent import run_swe_agent
from dataset_foundry.actions.item.save_item import save_item
from dataset_foundry.core.key import Key
from dataset_foundry.core.template import Template
from dataset_foundry.core.item_pipeline import ItemPipeline
from dataset_foundry.utils.collections.omit import omit

pipeline = ItemPipeline(
    name="generate_repo_from_spec_with_swe_agent",
    metadata={
        "version": "0.1.0",
        "author": "fastfedora",
        "description": "Generate complete repositories from specifications using SWE Agent",
    },
    config=Path(__file__).parent / "config.yaml",
    setup=[
        load_dataset_from_directory(
            include="spec_{id}.yaml",
            property="spec",
            merge=True,
        ),
    ],
    steps=[
        log_item(message=Template("Generating repository with SWE Agent for {id}...")),
        set_item_metadata(),
        run_swe_agent(
            instructions=Key("context.swe_agent.instructions"),
            prompt=Key("context.prompts.implement_spec"),
            spec=Key("spec"),
            output_dir=Template("{context.output_dir}/{id}"),
            agent="codex",
            timeout=7200,  # 2 hours
            max_retries=1,
            output_key="agent_result",
            stream_logs=True,
        ),
        save_item(
            contents=lambda item: omit(["logs"], item.data["agent_result"].model_dump()),
            filename=Template("{id}/runs/{metadata.created_at}/result.yaml"),
            format="yaml"
        ),
        save_item(
            contents=Key("agent_result.logs"),
            filename=Template("{id}/runs/{metadata.created_at}/agent.log"),
        ),
        log_item(message=Template("Repository generation completed for {id}")),
    ]
)
