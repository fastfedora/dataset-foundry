import logging

from ...core.context import Context
from ...core.dataset_item import DatasetItem
from ...types.item_action import ItemAction
from ...utils.eval.item_eval import item_eval

logger = logging.getLogger(__name__)


def do_while_item(actions: list, condition: str, max_iterations: int = 10) -> ItemAction:
    """
    Creates an action that executes a list of actions at least once and then continues executing
    them while a given condition is met.

    The `iteration` variable passed into the condition represents the number of completed iterations
    at the time the condition is evaluated. For `do_while_item`, the actions execute once before the
    first evaluation, so `iteration` is 1 on the first condition check.

    Args:
        actions (list): A list of actions to execute while the condition is true.
        condition (str): A string representing the condition to evaluate.
        max_iterations (int): The maximum number of iterations to execute. Defaults to 10.

    Returns:
        function: A function that takes a DatasetItem and Context and executes the
            actions at least once and then while the condition is true.
    """

    async def do_while_item_action(item: DatasetItem, context: Context):
        iterations = 0

        # TODO: Think about whether we want to bind `**item.data` here to make things simpler. I
        #       think other item actions are doing this [fastfedora 3.Mar.2025]
        while True:
            iterations += 1
            logger.debug(
                f"Executing do-while loop iteration {iterations} for condition '{condition}'."
            )
            for action in actions:
                await action(item, context)

            if not item_eval(condition, item, context, {"iteration": iterations}):
                break

            if iterations >= max_iterations:
                logger.warning(f"Reached maximum of {max_iterations} iterations for '{condition}'.")
                break

    return do_while_item_action
