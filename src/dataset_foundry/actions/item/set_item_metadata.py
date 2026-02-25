from datetime import datetime
from typing import Callable, Union

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...core.key import Key
from ...types.item_action import ItemAction
from ...utils.get_pipeline_metadata import get_pipeline_metadata
from ...utils.params.resolve_item_value import resolve_item_value

def set_item_metadata(
        property: Union[Callable,Key,str] = "metadata",
    ) -> ItemAction:
    async def set_item_metadata_action(item: DatasetItem, context: Context):
        resolved_property = resolve_item_value(property, item, context, required_as="property")

        run_at = datetime.now().isoformat()
        metadata = item.data.get("metadata", {})
        metadata["version"] = 2

        if "created_at" in metadata:
            # Convert old metadata format to new format
            if "pipeline" in metadata and "model" in metadata:
                metadata.setdefault("initial", {
                    "pipeline": metadata["pipeline"],
                    "model": metadata["model"],
                    "run_at": metadata["created_at"],
                })
                del metadata["pipeline"]
                del metadata["model"]

                if "swe_agent" in metadata:
                    metadata["initial"]["swe_agent"] = metadata["swe_agent"]
                    del metadata["swe_agent"]

            # Add edit to metadata
            metadata["updated_at"] = run_at
            metadata.setdefault("edits", []).append({
                "pipeline": get_pipeline_metadata(context),
                "model": context.model.info,
                "run_at": run_at,
            })

        else:
            metadata["created_at"] = run_at
            metadata.setdefault("initial", {
                "pipeline": get_pipeline_metadata(context),
                "model": context.model.info,
                "run_at": run_at,
            })

        item.push({
            resolved_property: metadata,
        }, set_item_metadata)

    return set_item_metadata_action
