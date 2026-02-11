import asyncio
import logging
from typing import Any

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ListView, Tab, Tabs

from ...core.pipeline import Pipeline
from ...core.pipeline_service import pipeline_service
from ...displays.core.console_service import console_service
from .widgets.console_log_view import ConsoleLogView
from .widgets.item_log_view import ItemLogView
from .widgets.item_tabs import ItemTabs

logger = logging.getLogger(__name__)


class FullDisplayApp(App):
    CSS = """
    Screen { layout: vertical; }

    #pane_pipeline { layout: horizontal; }
    #pane_console { layout: horizontal; }

    #item_tabs {
        width: 20%;
        min-width: 20%;
        max-width: 20%;
        height: 100%;
    }
    #item_tabs ListItem { width: 100%; }
    #item_tabs Label { width: 100%; text-wrap: wrap; }

    ItemLogView { width: 80%; }
    """

    def __init__(self, pipeline: Pipeline, params: dict[str, Any]):
        super().__init__()
        self._pipeline = pipeline
        self._params = params
        self._pipeline_worker = None
        self._is_quitting = False

        self.app.begin_capture_print(self, stdout=True, stderr=True)
        self.log_view = ItemLogView()
        self.console_view = ConsoleLogView()

    def on_print(self, event: events.Print) -> None:
        console_service.append(str(event.text))

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Tabs(
                Tab("Pipeline", id="tab_pipeline"),
                Tab("Console", id="tab_console"),
                id="top_tabs"
            )
            with Horizontal(id="pane_pipeline"):
                yield ItemTabs(id="item_tabs")
                yield self.log_view
            with Horizontal(id="pane_console"):
                yield self.console_view

    def on_mount(self) -> None:
        if len(pipeline_service.pipelines) > 0:
            self._select_tab('tab_pipeline')
        else:
            self._select_tab('tab_console')
            # Hide pipeline tab until a pipeline starts
            self.query_one('#tab_pipeline').display = False

        pipeline_service.subscribe("pipeline_started", {}, self._on_pipeline_started)

        self._pipeline_worker = self.run_worker(
            self._run_pipeline(),
            name="pipeline-runner",
            exit_on_error=True,
        )

    def on_list_view_selected(self, event: ListView.Selected):
        # Only handle selections from the item tabs list
        source_list = event.list_view
        if getattr(source_list, 'id', None) != 'item_tabs':
            return

        # Use the ListItem's name to store the item_id
        item_id = event.item.name
        self.log_view.item_id = item_id

    def _on_pipeline_started(self, _event_type, _payload):
        """Show Pipeline tab when a pipeline starts"""
        self._select_tab('tab_pipeline')

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        # HACK: The `TabActivated` event appears to be being send when tabs are added into the DOM
        #       even if they are not actually active. Checking the `-active` class ensures we only
        #       switch to the tab if it is actually active. [fastfedora 10.Oct.25]
        if "-active" in event.tab.classes:
            self._switch_tab(event.tab.id)

    async def _run_pipeline(self) -> None:
        """
        Run the configured pipeline in the background.

        When the pipeline completes, exit the app unless `no_exit` was requested.
        """
        try:
            await self._pipeline.run(params=self._params)
        except asyncio.CancelledError:
            # Expected when the user quits while the pipeline is still running. Let pipeline cleanup
            # complete via its own try/finally, then fall through to the exit logic below without
            # re-raising.
            pass
        finally:
            if self._is_quitting or not self._params.get("no_exit", False):
                self.exit()

    def _cancel_pipeline(self, delay_seconds: float = 0.1) -> None:
        """
        Cancel the pipeline worker if it is still running, after a short delay.

        The delay gives Textual time to refresh the UI so the shutdown message is visible before any
        potentially blocking cleanup work begins.
        """
        worker = self._pipeline_worker

        async def _cancel_after_delay() -> None:
            await asyncio.sleep(delay_seconds)
            if worker is not None and not worker.is_finished and worker.is_running:
                worker.cancel()

        self.call_later(_cancel_after_delay)

    async def action_quit(self) -> None:
        """
        When the user quits the UI while the pipeline worker is still running, show a cleanup
        message and keep the UI visible until the pipeline has finished its own shutdown.
        """
        if self._is_quitting:
            return

        self._is_quitting = True

        if self._pipeline_worker is not None and not self._pipeline_worker.is_finished:
            console_service.append(
                "\nShutting down Docker containers... Please wait for cleanup to complete."
            )
            self._select_tab("tab_console")
            self._cancel_pipeline()
            return

        self.exit()

    def _select_tab(self, tab_id: str) -> None:
        top_tabs = self.query_one('#top_tabs')
        top_tabs.active = tab_id
        self._switch_tab(tab_id)

    def _switch_tab(self, tab_id: str) -> None:
        pipeline_pane = self.query_one('#pane_pipeline')
        console_pane = self.query_one('#pane_console')

        if tab_id == 'tab_pipeline':
            # Ensure the Pipeline tab itself is visible when selected, since it starts hidden
            pipeline_tab = self.query_one('#tab_pipeline')
            pipeline_tab.display = True

            # Switch to the pipeline tab pane
            pipeline_pane.display = True
            console_pane.display = False
        elif tab_id == 'tab_console':
            pipeline_pane.display = False
            console_pane.display = True
