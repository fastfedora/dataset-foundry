from typing import Callable, Union

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...core.key import Key
from ...types.item_action import ItemAction
from ...utils.params.resolve_item_value import resolve_item_value

def set_item_property(
        key: Union[Callable,Key,str],
        value: Union[Callable,Key,str],
    ) -> ItemAction:
    async def set_item_property_action(item: DatasetItem, context: Context):
        resolved_key = resolve_item_value(key, item, context, required_as="key")
        resolved_value = resolve_item_value(value, item, context)

        # TODO: Think about whether we should delete the key if the value is None, and if so, how.
        #       we might do that with history tracking. [fastfedora 5.Aug.25]
        item.push({
            resolved_key: resolved_value
        }, set_item_property);

    return set_item_property_action
