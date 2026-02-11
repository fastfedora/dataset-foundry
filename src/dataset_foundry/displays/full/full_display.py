from ...core.pipeline import Pipeline
from ..core.display import Display
from ..core.pipeline_log_handler import install_pipeline_log_handler
from .full_display_app import FullDisplayApp

class FullDisplay(Display):
    def setup_logging(self, log_level: str):
        install_pipeline_log_handler(log_level)

    async def run_pipeline(self, pipeline: Pipeline, params: dict):
        """
        Run the given pipeline inside the FullDisplayApp, relying on Textual's
        own lifecycle management (workers, timers, shutdown) rather than
        juggling asyncio tasks externally.
        """
        app = FullDisplayApp(pipeline=pipeline, params=params)
        await app.run_async()
