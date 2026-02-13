import logging
from typing import Any, Callable, Optional, Union

from ...core.context import Context
from ...core.key import Key
from ...core.template import Template
from ..get import get

logger = logging.getLogger(__name__)

def resolve_value(
        value: Union[Callable,Key,str,None],
        object: Any,
        data: dict,
        context: Context,
        required_as: Optional[str] = None,
    ):
    resolved_value = None
    variables = { **data, 'context': context }

    if hasattr(object, 'id'):
        variables['id'] = object.id

    if value is not None:
        if callable(value):
            arg_count = value.__code__.co_argcount
            resolved_value = value(object) if arg_count == 1 else value(object, context)
        elif isinstance(value, Key):
            resolved_value = get(variables, value.path)
        else:
            resolved_value = value

    if required_as and (resolved_value is None or resolved_value == ""):
        raise ValueError(f"'{required_as}' must be passed in or defined in the data or context")

    logger.debug(
        f"Resolved '{value.path if isinstance(value, Key) else value}' to '{resolved_value}'"
    )

    if isinstance(resolved_value, Template):
        resolved_value = resolved_value.resolve(variables)

    return resolved_value
