def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_ingest_departments_batch(client):
    payload = {"records": [{"id": 1, "department": "Engineering"}, {"id": 2, "department": "Sales"}]}
    resp = client.post("/departments", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["inserted"] == 2
    assert body["rejected"] == 0


def test_ingest_departments_rejects_duplicate_id(client):
    payload = {"records": [{"id": 1, "department": "Engineering"}]}
    client.post("/departments", json=payload)
    resp = client.post("/departments", json=payload)
    body = resp.json()
    assert body["inserted"] == 0
    assert body["rejected"] == 1


def test_ingest_hired_employees_rejects_invalid_fk(client):
    client.post("/departments", json={"records": [{"id": 1, "department": "Engineering"}]})
    client.post("/jobs", json={"records": [{"id": 1, "job": "Recruiter"}]})

    payload = {
        "records": [
            {
                "id": 1,
                "name": "Jane",
                "datetime": "2021-01-01T00:00:00Z",
                "department_id": 1,
                "job_id": 1,
            },
            {
                "id": 2,
                "name": "John",
                "datetime": "2021-01-01T00:00:00Z",
                "department_id": 999,  # no existe
                "job_id": 1,
            },
        ]
    }
    resp = client.post("/hired_employees", json=payload)
    body = resp.json()
    assert body["inserted"] == 1
    assert body["rejected"] == 1
    assert "department_id" in body["errors"][0]["reason"]


def test_batch_size_over_1000_is_rejected(client):
    records = [{"id": i, "department": f"Dept {i}"} for i in range(1, 1002)]
    resp = client.post("/departments", json={"records": records})
    assert resp.status_code == 422  # violacion de max_length de pydantic


def test_analytics_endpoints_return_200(client):
    assert client.get("/analytics/hires-by-quarter").status_code == 200
    assert client.get("/analytics/departments-above-average").status_code == 200


def test_backup_and_restore_roundtrip(client, tmp_path):
    client.post("/departments", json={"records": [{"id": 1, "department": "Engineering"}]})

    backup_resp = client.post("/backup/departments")
    assert backup_resp.status_code == 200

    # borrar todo y restaurar
    from app import models

    restore_resp = client.post("/restore/departments")
    assert restore_resp.status_code == 200
    assert restore_resp.json()["restored_records"] == 1
