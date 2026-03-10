import logging

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...types.item_action import ItemAction
from ...utils.eval.item_eval import item_eval

logger = logging.getLogger(__name__)

def while_item(condition: str, actions: list, max_iterations: int = 10) -> ItemAction:
    """
    Creates an action that executes a list of actions while a given condition is met.

    The `iteration` variable passed into the condition represents the number of completed iterations
    at the time the condition is evaluated. On the first evaluation, `iteration` is 0 because the
    actions have not yet executed.

    Args:
        condition (str): A string representing the condition to evaluate.
        actions (list): A list of actions to execute if the condition is true.
        max_iterations (int): The maximum number of iterations to execute. Defaults to 10.

    Returns:
        function: A function that takes a Dataset and Context and executes the actions while the
            condition is true.
    """
    async def while_item_action(item: DatasetItem, context: Context):
        iterations = 0

        # TODO: Think about whether we want to bind `**item.data` here to make things simpler. I
        #       think other item actions are doing this [fastfedora 3.Mar.2025]
        while item_eval(condition, item, context, { 'iteration': iterations }):
            iterations += 1
            logger.debug(f"Condition '{condition}' met. Executing loop {iterations}.")
            for action in actions:
                await action(item, context)

            if iterations >= max_iterations:
                logger.warning(f"Reached maximum of {max_iterations} iterations for '{condition}'.")
                break

    return while_item_action