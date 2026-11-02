# src/data_validator.py
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be numeric.
    """
    initial_rows = len(df)

    # 1. Check that every name in required_columns exists in the DataFrame
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            raise ValueError(f"Missing required column: {col}")

    # 2. For each configured numeric column, identify non-missing values that cannot be converted
    invalid_rows = []
    for col in numeric_columns:
        if col in df.columns:
            for i, value in df[col].items():
                if pd.notna(value):
                    try:
                        float(value)
                    except ValueError:
                        # Log a warning and record this row's index
                        logger.warning(
                            f"Invalid numeric value '{value}' in column '{col}' at row {i}"
                        )
                        invalid_rows.append(i)

    # 3. Remove the invalid rows (deduplicate indices in case multiple columns fail for the same row)
    if invalid_rows:
        df = df.drop(index=list(set(invalid_rows)))
        removed_count = len(set(invalid_rows))
        logger.warning(
            f"Removed {removed_count} rows with invalid numeric values in {numeric_columns}"
        )

    # 4. Convert each configured numeric column to a numeric data type
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])

    final_rows = len(df)

    # 5. Log the number of valid and removed rows at the DEBUG level
    logger.debug(f"Validation: {initial_rows} -> {final_rows} rows")

    return df