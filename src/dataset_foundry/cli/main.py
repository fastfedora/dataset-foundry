import asyncio
import logging
import signal
from datetime import datetime
from pathlib import Path

from ..core.model import Model
from ..displays.get_display import get_display
from ..utils.imports.import_module import import_module
from ..utils.params.parse_dir_arg import parse_dir_arg
from .advanced_argparse import AdvancedArgumentParser
from .config import DATASET_DIR, LOG_DIR
from .config import (
    DEFAULT_MAX_CONCURRENT_ITEMS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_MODEL_TEMPERATURE,
    DEFAULT_NUM_SAMPLES,
)

logger = logging.getLogger(__name__)

async def main_cli():
    parser = AdvancedArgumentParser(description="Build and refine datasets using data pipelines")
    parser.add_argument(
        "pipeline",
        env="DF_PIPELINE",
        type=str,
        help="Path to a Python file containing a `pipeline` object to run"
    )
    parser.add_argument(
        "dataset",
        env="DF_DATASET",
        type=str,
        nargs="?",
        default=datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        help="Name of the dataset to run the pipeline on (defaults to current timestamp)"
    )
    parser.add_argument(
        "--input-dir",
        env="DF_INPUT_DIR",
        type=str,
        help="Directory to read data from (defaults to datasets/<dataset>)"
    )
    parser.add_argument(
        "--output-dir",
        env="DF_OUTPUT_DIR",
        type=str,
        help="Directory to write data to (defaults to datasets/<dataset>)"
    )
    parser.add_argument(
        "--config-dir",
        env="DF_CONFIG_DIR",
        type=str,
        help="Directory to read configuration files from (defaults to same directory as pipeline)"
    )
    parser.add_argument(
        "--log-dir",
        env="DF_LOG_DIR",
        type=str,
        help="Directory to output logs to (defaults to logs/<dataset>)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        env="DF_LOG_LEVEL",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level (debug, info, warning, error, critical)"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        env="DF_NUM_SAMPLES",
        default=DEFAULT_NUM_SAMPLES,
        help=f"Number of samples to generate (default: {DEFAULT_NUM_SAMPLES})"
    )
    parser.add_argument(
        "--limit",
        type=int,
        env="DF_LIMIT",
        default=None,
        help=f"The maximum number of samples to run through the pipeline (default: None)"
    )
    parser.add_argument(
        "--model",
        type=str,
        env="DF_MODEL",
        default=DEFAULT_MODEL,
        help=f"Model to use in format 'provider/model_name' (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        env="DF_MODEL_TEMPERATURE",
        default=DEFAULT_MODEL_TEMPERATURE,
        help=f"Temperature for generation (default: {DEFAULT_MODEL_TEMPERATURE})"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        env="DF_MAX_TOKENS",
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum tokens for model output (default: {DEFAULT_MAX_TOKENS})"
    )
    parser.add_argument(
        "--display",
        type=str,
        env="DF_DISPLAY",
        default="full",
        choices=["full", "log", "none"],
        help="Type of display to use for logging output (default: full)"
    )
    parser.add_argument(
        "--no-exit",
        action="store_true",
        env="DF_NO_EXIT",
        default=False,
        help="Don't exit the full display when pipeline finishes until Ctrl-Q is pressed (default: False)"
    )
    parser.add_argument(
        "--max-items",
        type=int,
        env="DF_MAX_ITEMS",
        default=DEFAULT_MAX_CONCURRENT_ITEMS,
        help=f"Maximum number of items to process concurrently"
    )
    parser.add_argument(
        "-P",
        action="append",
        type=lambda x: dict(item.split("=") for item in x.split(",") if "=" in item),
        dest="pipeline_parameters",
        help="Pipeline parameters in the format 'key=value'. Can be specified multiple times."
    )

    args = vars(parser.parse_args())
    log_level = getattr(logging, args["log_level"].upper())

    display = get_display(args["display"])
    display.setup_logging(log_level=log_level)

    args["input_dir"] = parse_dir_arg(args["input_dir"], DATASET_DIR / args["dataset"], False)
    args["output_dir"] = parse_dir_arg(args["output_dir"], DATASET_DIR / args["dataset"], True)
    args["config_dir"] = parse_dir_arg(args["config_dir"], Path(args["pipeline"]).parent, False)
    args["log_dir"] = parse_dir_arg(args["log_dir"], LOG_DIR / args["dataset"], True)
    args["model"] = Model(
        model=args["model"],
        temperature=args["temperature"],
        max_tokens=args["max_tokens"],
    )

    pipeline_parameters = {
        "max_concurrent_items": args["max_items"],
    }
    parameter_list = args.pop("pipeline_parameters", []) or []
    for param_dict in parameter_list:
        pipeline_parameters.update(param_dict)

    module = import_module(args["pipeline"])
    logger.info(f"Loaded pipeline: {args['pipeline']}")

    await display.run_pipeline(module.pipeline, params={ **args, **pipeline_parameters })

def signal_handler(_signum, _frame):
    print("\nReceived interrupt signal, shutting down gracefully...")
    raise KeyboardInterrupt()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    try:
        asyncio.run(main_cli())
    except KeyboardInterrupt:
        # Interrupt handled; exit without traceback
        pass

if __name__ == "__main__":
    main()
