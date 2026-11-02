# src/data_output.py
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_data(df, filepath):
    """Save a DataFrame as a CSV file."""
    path = Path(filepath)
    
    # Create the output directory if it does not exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the DataFrame as CSV without the index
    df.to_csv(path, index=False)
    
    # Log the number of rows saved and the output path at the DEBUG level
    logger.debug(f"Saved {len(df)} rows to {path}")
    
    return path