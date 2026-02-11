import asyncio

import pytest

from dataset_foundry.core.pipeline import Pipeline
from dataset_foundry.core.dataset import Dataset
from dataset_foundry.displays.full.full_display import FullDisplay


class _DummyPipeline(Pipeline):
    async def execute(self, dataset: Dataset, context):
        # Minimal no-op pipeline body for integration testing the display.
        return dataset


@pytest.mark.asyncio
async def test_full_display_runs_pipeline_and_exits():
    """
    FullDisplay.run_pipeline should run the pipeline to completion and exit
    the Textual app cleanly when no_exit is False.
    """
    display = FullDisplay()
    pipeline = _DummyPipeline(name="dummy")

    # We expect this to complete without hanging or raising.
    await asyncio.wait_for(
        display.run_pipeline(pipeline, params={"no_exit": False}),
        timeout=5,
    )


@pytest.mark.asyncio
async def test_full_display_respects_no_exit_flag():
    """
    When no_exit is True, FullDisplay.run_pipeline should still return to the
    caller (so the CLI can continue), even though the app itself keeps the
    UI running until the user exits it.
    """
    display = FullDisplay()
    pipeline = _DummyPipeline(name="dummy")

    # For now we simply assert that the call completes. If Textual changes
    # semantics around no_exit in the future, this test documents the current
    # expectation that run_pipeline still returns.
    await asyncio.wait_for(
        display.run_pipeline(pipeline, params={"no_exit": True}),
        timeout=5,
    )

