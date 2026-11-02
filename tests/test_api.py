def test_upload_csv(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={
            "file": ("sample_data.csv", sample_csv_bytes, "text/csv")
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["id"], int) and data["id"] > 0
    assert data["rows"] == 6
    assert data["columns"] == 2
    assert data["column_names"] == ["student_id", "score"]
    


def test_process_and_retrieve(
    client, uploaded_dataset_id, processing_body
):
    response = client.post(
        f"/datasets/{uploaded_dataset_id}/process",
        json=processing_body
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["validation_rows_removed"] == 1
    assert res_json["cleaning_report"]["rows_before"] == 5
    assert res_json["cleaning_report"]["rows_after"] == 3

    get_response = client.get(f"/datasets/{uploaded_dataset_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["total_rows"] == 3


def test_retrieve_missing_dataset(client):
    response = client.get("/datasets/99999")
    assert response.status_code == 404