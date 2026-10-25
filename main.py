import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = DatasetStorage()

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

