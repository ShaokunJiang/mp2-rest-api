# data_processor.py
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def remove_duplicates(df):
    """Remove duplicate rows."""
    removed = df.drop_duplicates()
    logger.debug(f"remove_duplicates: removed {len(df)-len(removed)} duplicate row(s)")
    return removed


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""

    if axis == 'rows':
        cleaned = df.dropna(axis = 0)
        logger.debug(f"handle_missing: removed {len(df)-len(cleaned)} row(s)")
    elif axis == 'columns':
        cleaned = df.dropna(axis = 1)
        logger.debug(f"handle_missing: removed {len(df)-len(cleaned)} column(s)")
    else:
        logger.error(f"Unsupported axis: {axis}")
        raise ValueError(f"Unsupported axis: {axis}")
    return cleaned



def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""

    if method not in ['iqr', 'zscore']:
        logger.error(f"Unsupported outlier method: {method}")
        raise ValueError(f"Unsupported outlier method: {method}")

    rows_before = len(df)

    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column not found: {col}")
            continue
            
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column is not numeric: {col}")
            continue

        if method == 'iqr':
            q1 = df[col].quantile(0.25)  
            q3 = df[col].quantile(0.75)  
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            df = df[(df[col] >= lower) & (df[col] <= upper)] 
        
        elif method == 'zscore':
            mean = df[col].mean()     
            std = df[col].std()         
            if std == 0 or pd.isna(std):
                continue
            z_score = (df[col] - mean) / std
            df = df[z_score.abs() <= threshold]  

    logger.debug(f"remove_outliers ({method}, threshold={threshold}): removed {rows_before - len(df)} row(s)")
    return df  


def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    proc = config.get("processing", {})

    if proc.get("remove_duplicates"):
        df = remove_duplicates(df)

    if proc.get("missing", {}).get("enabled"):
        df = handle_missing(df, axis=proc["missing"].get("axis", "rows"))


    if proc.get("outliers", {}).get("enabled"):
        out = proc["outliers"]
        df = remove_outliers(df, out.get("columns", []), out.get("method", "iqr"), out.get("threshold", 1.5))
    return df


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    rows_before = len(df_before)
    rows_after = len(df_after)
    cols_before = len(df_before.columns)
    cols_after = len(df_after.columns)
    
    report = {
        'rows_before': rows_before,
        'rows_after': rows_after,
        'rows_removed': rows_before - rows_after,
        'columns_before': cols_before,
        'columns_after': cols_after,
        'columns_removed': cols_before - cols_after
    }
    
    return report