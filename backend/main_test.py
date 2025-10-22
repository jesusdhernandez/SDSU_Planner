# main_test.py
import json
import uuid
import pytest
import main as app_module

@pytest.fixture()
def client(tmp_path):
    """A simpler client fixture without monkeypatch."""
    # Create a fake tasks.json inside pytest's tmp_path
    fake_tasks = tmp_path / "fake_tasks.json"
    fake_data = {
        "number_of_tasks": 2,
        "list_of_tasks": [
            {"id": str(uuid.uuid4()), "title": "Task1", "day": 1, "number": 1, "done": False},
            {"id": str(uuid.uuid4()), "title": "Task2", "day": 2, "number": 1, "done": False},
        ],
    }
    fake_tasks.write_text(json.dumps(fake_data, indent=2))

    app_module.DATA = fake_tasks
    return app_module.app.test_client()

def test_get_tasks_returns_list(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {"title", "day", "number", "id", "done"} <= set(data[0].keys())
