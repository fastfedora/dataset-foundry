from datetime import datetime
import re
import logging
from typing import Callable, Optional, Union

from langchain_core.prompts import ChatPromptTemplate

from ...core.context import Context
from ...core.dataset import Dataset
from ...core.dataset_item import DatasetItem
from ...core.key import Key
from ...types.dataset_action import DatasetAction
from ...utils.params.resolve_dataset_value import resolve_dataset_value
from ...utils.get_pipeline_metadata import get_pipeline_metadata

variable_regex = r'\{([^}]+)\}'

logger = logging.getLogger(__name__)

def generate_dataset(
        prompt: Union[Callable,Key,str] = Key("context.prompt"),
        model: Union[Callable,Key,str] = Key("context.model"),
        parser: Optional[Union[Callable,Key,str]] = None,
        output_key: Optional[Union[Callable,Key,str]] = None,
        dataset_metadata_key: Optional[Union[Callable,Key,str]] = None,
        dataset_chat_key: Optional[Union[Callable,Key,str]] = "chat",
    ) -> DatasetAction:
    """
    Generate a dataset by given a prompt to a model and parsing the response.

    Args:
        prompt: A dataset generation prompt template.
        model: The model to use for generation.
        parser: The parser to parse the response with, if any.
        output_key: The key under which to save the content in each data item. If not provided
            and not using a custom parser, the content will be saved under the key "output".
        dataset_metadata_key: The key to use for the dataset metadata. If not provided, the
            metadata will be merged with the existing metadata instead.
        dataset_chat_key: The key to save the chat messages used to generate the dataset. If not
            provided, the chat messages will not be saved.

    Returns:
        A dataset action that can be used to generate a dataset.
    """

    async def generate_dataset_action(dataset: Dataset, context: Context):
        resolved_prompt = resolve_dataset_value(prompt, dataset, context, required_as="prompt")
        resolved_model = resolve_dataset_value(model, dataset, context, required_as="model")
        resolved_parser = resolve_dataset_value(parser, dataset, context)
        resolved_output_key = resolve_dataset_value(output_key, dataset, context)
        resolved_dataset_metadata_key = resolve_dataset_value(dataset_metadata_key, dataset, context)
        resolved_dataset_chat_key = resolve_dataset_value(dataset_chat_key, dataset, context)

        # Build the prompt
        variables = re.findall(variable_regex, resolved_prompt)
        prompt_template = ChatPromptTemplate.from_messages([ ("user", resolved_prompt) ])
        model_prompt = prompt_template.partial(
            **{
                variable: context[variable]
                for variable in variables
                if variable in context
            },
            **{
                variable: dataset.metadata.get(variable)
                for variable in variables
                if variable in dataset.metadata
            },
        )

        # Generate the response
        messages = await model_prompt.aformat_messages()
        response = await resolved_model.ainvoke(messages)

        if resolved_parser:
            contents = resolved_parser(response.content)
        else:
            contents = [response.content]
            resolved_output_key = resolved_output_key or "output"

        if context['num_samples'] and len(contents) > context['num_samples']:
            logger.debug(f"Limiting dataset to {context['num_samples']} samples")
            contents = contents[:context['num_samples']]

        for i, content in enumerate(contents):
            # TODO: Make this configurable, so we can set the ID to `scenarios` for the pipeline viewer
            item = DatasetItem(
                f"{i+1:03d}",
                { resolved_output_key: content } if resolved_output_key else content
            )
            dataset.add(item)

        metadata = {
            "num_samples": len(contents),
            "pipeline": get_pipeline_metadata(context),
            "model": context.model.info,
            "created_at": datetime.now().isoformat(),
        }

        dataset.metadata.update(
            { resolved_dataset_metadata_key: metadata }
            if resolved_dataset_metadata_key else metadata
        )

        if resolved_dataset_chat_key:
            dataset.metadata.update({
                resolved_dataset_chat_key: {
                    "messages": messages,
                    "response": response,
                },
            })

    return generate_dataset_action
