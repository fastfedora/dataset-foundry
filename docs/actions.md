# Dataset Foundry Actions Documentation

This document provides a comprehensive list of all dataset and item actions available in Dataset
Foundry, along with their parameters and descriptions.

## Dataset Actions

### `generate_dataset`
Generates a dataset by calling a language model with a prompt. If `parser` is specified, the output
is passed to the parser, with the result being used to generate the data items. If `output_key` is
specified, any generated content is stored under the given key of each data item.

**Parameters:**
- `prompt` (Union[Callable,Key,str]): The prompt to use (default: `Key("context.prompt")`)
- `model` (Union[Callable,Key,str]): The model to use (default: `Key("context.model")`)
- `parser` (Union[Callable,Key,str], optional): Custom parser to process the model response
- `output_key` (Union[Callable,Key,str], optional): Key to store the output under

### `if_dataset`
Executes a list of dataset actions if a given condition is met.

**Parameters:**
- `condition` (str): A string representing the condition to evaluate
- `if_actions` (list): A list of dataset actions to execute if the condition is true
- `else_actions` (list, optional): A list of dataset actions to execute if the condition is false

### `load_dataset`
Loads a dataset from a YAML file.

**Parameters:**
- `filename` (Union[Callable,Key,str]): Name of the file to load (default: "dataset.yaml")
- `dir` (Union[Callable,Key,str]): Directory containing the file (default: `Key("context.input_dir")`)
- `property` (Union[Callable,Key,str], optional): Property to store the loaded data under
- `id_generator` (Callable): Function to generate item IDs (default: `lambda index, _data: f"{index+1:03d}"`)

### `load_dataset_metadata`
Loads metadata for the active dataset from a file.

**Parameters:**
- `filename` (Union[Callable,Key,str]): Name of the file to load (default: "metadata.yaml")
- `dir` (Union[Callable,Key,str]): Directory containing the file (default: `Key("context.input_dir")`)
- `property` (Union[Callable,Key,str], optional): Property to store the loaded metadata under

### `reset_dataset`
Resets the active dataset to its initial state.

**Parameters:** None

### `run_pipeline`
Runs a pipeline on the active dataset.

**Parameters:**
- `pipeline` (Union[Callable,Key,Pipeline,str]): The pipeline to execute, specified as either a
  `Pipeline` instance or a fully-qualified Python module name that exports a `Pipeline` using the
  `pipeline` variable.
- `args` (Union[Callable,Key,dict], optional): Arguments to pass to the pipeline

### `save_dataset`
Saves the active dataset to a YAML file.

**Parameters:**
- `filename` (Union[Callable,Key,str]): Name of the file to save to (default: "dataset.yaml")
- `dir` (Union[Callable,Key,str]): Directory to save the file in (default: `Key("context.output_dir")`)
- `property` (Union[Callable,Key,str], optional): Property to save from the dataset items


## Item Actions

### `do_item_steps`
Executes a pipeline of steps on an item. Does not execute the setup or teardown for a pipeline.

**Parameters:**
- `pipeline` (Union[Callable,Key,ItemPipeline,str]): The pipeline defining step to execute

### `do_while_item`
Executes actions at least once and then repeatedly while a condition is true.

**Parameters:**
- `actions` (list): Actions to execute while condition is true
- `condition` (str): The condition to evaluate
- `max_iterations` (int): Maximum number of iterations (default: 10)

For both `while_item` and `do_while_item`, the condition receives an `iteration` variable that
represents the number of completed iterations at the time the condition is evaluated. For
`while_item`, `iteration` is 0 on the first evaluation because the body has not yet run. For
`do_while_item`, the body executes once before the first evaluation, so `iteration` is 1 on the
first condition check.

### `generate_item`
Generates a data item using a language model, storing the result as either the entire data for a
data item, or, if specified, as data underneath the property specified by `output_key`.

**Parameters:**
- `prompt` (Union[Callable,Key,str]): The prompt to use (default: `Key("context.prompt")`)
- `model` (Union[Callable,Key,str]): The model to use (default: `Key("context.model")`)
- `output_key` (Union[Callable,Key,str]): Key to store the output under (default: "output")

### `if_item`
Executes actions conditionally based on an item's properties.

**Parameters:**
- `condition` (str): The condition to evaluate
- `if_actions` (list): Actions to execute if condition is true
- `else_actions` (list, optional): Actions to execute if condition is false

### `load_item`
Loads data from a file into a data item.

**Parameters:**
- `filename` (Union[Callable,Key,str]): Name of the file to load
- `dir` (Union[Callable,Key,str]): Directory containing the file (default: `Key("context.input_dir")`)
- `property` (Union[Callable,Key,str], optional): Property to store the loaded data under
- `format` (Union[Callable,Literal['auto', 'text', 'json', 'yaml']], optional): Format of the file
  (default: 'auto')

### `log_item`
Logs item data or a custom message. If a custom message is specified, it is logged; otherwise the
listed properties are logged along with the item ID.

**Parameters:**
- `properties` (List[str], optional): List of properties to log
- `message` (Union[Callable,Key,str], optional): Custom message to log

### `parse_item`
Extracts content from the property of a data item.

If `parser` is specified, the item and context are passed to it to generate the result; otherwise,
if `code_block` or `xml_block` are specified, the content will be extracted from the corresponding
block.

A code block starts with three backticks and an optional format identifier and ends with three
backticks. The `code_block` parameter specifies the format to search for in the input. If
`code_block` is `json` or `yaml`, the content will additionally be parsed using the corresponding
parser.

An XML block starts with an XML tag and ends with the corresponding closing tag. The `xml_block`
parameter specifies the name of the XML tag.

The final content is saved as the entire data for the data item, or if `output_key` is specified,
under the property specified.

**Parameters:**
- `input` (Union[Callable,Key,str], optional): Input to parse (default: `Key("output")`)
- `output_key` (Union[Callable,Key,str], optional): Key to store parsed output under
- `parser` (Union[Callable,Key,str], optional): Custom parser to use
- `code_block` (Union[Callable,Key,str], optional): Type of code block to extract
- `xml_block` (Union[Callable,Key,str], optional): Type of XML block to extract

### `run_unit_tests`
Runs unit tests for a data item.

**Parameters:**
- `filename` (Union[Callable,Key,str]): Name of the test file
- `dir` (Union[Callable,Key,str]): Directory containing the test file (default: `Key("context.input_dir")`)
- `property` (Union[Callable,Key,str]): Property to store test results under (default: "test_result")
- `sandbox` (Union[Callable,Key,str], optional): Sandbox configuration to use for isolated test execution
- `stream_logs` (Union[Callable,Key,bool]): Whether to stream container logs (default: False)
- `timeout` (Union[Callable,Key,int]): Timeout for execution in seconds (default: 300)

### `save_item`
Saves a data item to a file.

**Parameters:**
- `filename` (Union[Callable,Key,str]): Name of the file to save to
- `contents` (Union[Callable,Key,str], optional): Contents to save (default: item data)
- `dir` (Union[Callable,Key,str]): Directory to save in (default: `Key("context.output_dir")`)
- `format` (Union[Callable,Literal['auto', 'text', 'json', 'yaml']], optional): Format to save in
  (default: 'auto')

### `save_item_chat`
Saves chat messages and responses of a data item stored under the `messages` and `response` keys
respectively to a file.

**Parameters:**
- `dir` (Union[Callable,Key,str]): Directory to save in (default: `Key("context.log_dir")`)
- `filename` (Union[Callable,Key,str]): Name of the file to save to (default: "log.yaml")

### `set_item_metadata`
Sets the default metadata for an item, including information about this pipeline, the current model
and a creation timestamp.

**Parameters:**
- `property` (Union[Callable,Key,str]): Property to store metadata under (default: "metadata")

### `set_item_property`
Sets a property on a data item.

**Parameters:**
- `key` (Union[Callable,Key,str]): The property key to set
- `value` (Union[Callable,Key,str]): The value to set

### `while_item`
Executes actions repeatedly while a condition is true.

**Parameters:**
- `condition` (str): The condition to evaluate
- `actions` (list): Actions to execute while condition is true
- `max_iterations` (int): Maximum number of iterations (default: 10)
