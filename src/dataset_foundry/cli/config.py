from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
OUTPUT_ROOT = Path.cwd()
DATASET_DIR = OUTPUT_ROOT / "datasets"
LOG_DIR = OUTPUT_ROOT / "logs"

# Model configuration
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_MODEL_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 8096
DEFAULT_NUM_SAMPLES = 10

# Pipeline configuration
DEFAULT_MAX_CONCURRENT_ITEMS = 10
