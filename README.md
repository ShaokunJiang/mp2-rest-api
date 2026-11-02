# MP2: Data Processing REST API

This project implements a FastAPI-based web service that integrates modular data processing pipelines for uploading, validating, cleaning, and querying CSV datasets. It features custom request-logging middleware, robust Pydantic data modeling, in-memory dataset storage, and endpoints for handling data transformation reports.

## Running Tests

To run the automated test suite and verify all API endpoints, execute:


```bash
python -m pytest tests -v

uvicorn main:app --reload

