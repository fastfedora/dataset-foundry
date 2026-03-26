# Dataset Foundry

A toolkit for building validated datasets.

Dataset Foundry uses the concept of data pipelines to load, generate or validate datasets. A
pipeline is a sequence of actions executed either against the dataset itself or the individual items
in the dataset.

For details on which actions are supported, see the [actions](docs/actions.md) documentation.

## Installation

1. Install the package:
   ```bash
   pip install dataset-foundry
   ```

2. Create a `.env` file in the project root:
   ```
   # Provider API keys
   OPENAI_API_KEY=
   ANTHROPIC_API_KEY=

   # Command-line defaults
   DF_MODEL=anthropic/claude-sonnet-4-20250514

   # Keep full display open after finishing so you can browse the results
   # DF_NO_EXIT=true
   ```

### Default Settings

- Default Model: gpt-4o-mini
- Default Temperature: 0.7
- Default Number of Samples: 10
- Dataset Directory: ./datasets
- Logs Directory: ./logs

## Project Structure

```
dataset-foundry/
├── src/
│   └── dataset_foundry/
│       ├── actions/       # Actions for processing datasets and items within those datasets
│       ├── cli/           # Command-line interface tools
│       ├── core/          # Core functionality
│       └── utils/         # Utility functions
├── datasets/              # Generated datasets
├── examples/              # Example pipelines
│   └── refactorable_code/ # Example pipelines to build a dataset of code requiring refactoring
└── logs/                  # Operation logs
```

## Running Pipelines

Pipelines can be run from the command line using the `dataset-foundry` command.

```bash
dataset-foundry <pipeline_module> <dataset_name>
```

For example, to run the `generate_spec` pipeline to create specs for a dataset saved to
`datasets/dataset1`, you would use:

```bash
dataset-foundry examples/refactorable_code/generate_spec/pipeline.py dataset1
```

Use `dataset-foundry --help` to see available arguments.

### Running Examples

To generate a set of specs for a dataset named `o3v5`, you would use:

```bash
dataset-foundry examples/refactorable_code/generate_spec/pipeline.py samples --num-samples=2
```

To generate a set of functions and unit testsfrom the specs, you would use:

```bash
dataset-foundry examples/refactorable_code/generate_all_from_spec/pipeline.py samples
```

To run the unit tests for the generated functions, you would use:

```bash
dataset-foundry examples/refactorable_code/regenerate_unit_tests/pipeline.py samples
```

If some of the unit tests fail, you can regenerate them by running:

```bash
dataset-foundry examples/refactorable_code/regenerate_unit_tests/pipeline.py samples
```

## Variable Substitutions

Variable substitutions allows you to use variables in your prompts and in certain parameters passed
into pipeline actions.

Prompt templates and certain parameters are parsed as f-strings, with the following enhancements:

- Dotted references are supported and resolve both dictionary keys or object attributes. For
  instance, `{spec.name}` will return the value of `spec['name']` if `spec` is a dictionary, or
  the value of `spec.name` if `spec` is an object.
- Formatters can be specified after a colon. For example, `{spec:yaml}` will return the `spec`
  object formatted as a YAML string. Supported formatters include: `yaml`, `json`, `upper`, `lower`.

For instance, if an item is being processed with an id of `123` and a `spec` dictionary with a
`name` key of `my_function`, the following will save the `code` property of the item as a file named
`item_123_my_function.py`:

```python
   ...
   save_item(contents=Key("code"), filename="item_{id}_{spec.name}.py"),
   ...
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.