import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import setup_logging, storage, log_requests, ProcessConfig, ProcessingReport,HealthResponse,DatasetInfo
from data_pipeline import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")

# Register request logging middleware
app.middleware('http')(log_requests)

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    suffix = Path(file.filename).suffix.lower()
    if suffix != '.csv':
        logger.warning(f'unsupported file format: {suffix}')
        raise HTTPException(status_code=400, detail='Only CSV files are accepted')
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except(pd.errors.EmptyDataError,pd.errors.ParserError,UnicodeDecodeError) as error:
        logger.warning(f'Failed to parse CSV file ->{error}')
        raise HTTPException(status_code=400, detail = f'invalid CSV file:{error}')
    dataset_id = storage.save(df,file.filename)
    metadata = storage.get_metadata(dataset_id)

    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file.filename}, rows={metadata['rows']}")
    return metadata

@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail=f"Dataset with ID {dataset_id} not found.")
    total_rows = len(df)
    df = df.where(pd.notnull(df),None)

    records = df.head(limit).to_dict(orient = 'records')
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return {
        "id": dataset_id,
        "data": records,
        "total_rows": total_rows
    }

@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport
)

def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    df = storage.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    config_dict = config.model_dump()
    
    for col in config.validation.numeric_columns:
        if col not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Numeric column '{col}' not found in dataset"
            )

    try:
        # Record the row count before validation
        rows_before_val = len(df)
        
        # Depending on the validate_dataframe implementation:
        validated_result = validate_dataframe(
            df, 
            required_columns=config.validation.required_columns,
            numeric_columns=config.validation.numeric_columns
        )
        
        # Compatibility handling: if a tuple (df, count) is returned
        if isinstance(validated_result, tuple):
            validated_df, rows_removed_val = validated_result
        else:
            validated_df = validated_result
            rows_removed_val = rows_before_val - len(validated_df)

        working_df = validated_df.copy()

        # Call the processing function
        processed_df = process_data(working_df, config_dict)

        # Create the cleaning report
        report = create_cleaning_report(validated_df, processed_df)

        # Update storage with the processed dataframe
        storage.update(dataset_id, processed_df)

        logger.info(
            f"Processed dataset: id={dataset_id}, validation_removed={rows_removed_val}, "
            f"rows_before={report['rows_before']}, rows_after={report['rows_after']}"
        )

        return {
            "id": dataset_id,
            "validation_rows_removed": rows_removed_val,
            "cleaning_report": report
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))