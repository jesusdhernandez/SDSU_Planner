
import json
from pathlib import Path
import uuid
from backend import main as app
def setup_test_data():
    fake_data = {
        "number_of_tasks": 2,
        "list_of_tasks": [
            {"id": str(uuid.uuid4()), "title": "Task1", "day": 1, "number": 1, "done": False},
            {"id": str(uuid.uuid4()), "title": "Task2", "day": 2, "number": 1, "done": False},
        ],
    }
    fake_path = Path(__file__).resolve().parent / "fake_tasks.json"
    fake_path.write_text(json.dumps(fake_data, indent=2), encoding="utf-8")

   
    app.DATA = fake_path

    # test client which can do dummy crud methods
    return app.app.test_client(), fake_path


def read_store(path):
    #returns the json data
    return json.loads(path.read_text(encoding="utf-8"))


def test_get_tasks():
    client, path = setup_test_data()  
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {"title", "day", "number", "id", "done"} <= set(data[0].keys())


def test_add_task_successfully():
    client, path = setup_test_data()  
    dummy_task_to_add = {"title": "C", "day": 3, "number": 1}

    resp = client.post("/api/tasks", json=dummy_task_to_add)
    assert resp.status_code == 201

    created = resp.get_json()
    assert created["title"] == "C"
    assert created["day"] == 3
    assert created["number"] == 1
    assert "id" in created and isinstance(created["id"], str)


def test_duplicate_add_task_fails():
    client, path = setup_test_data()  
    dummy_task_to_add = {"title": "C", "day": 2, "number": 1}

    resp = client.post("/api/tasks", json=dummy_task_to_add)
    assert resp.status_code == 400

    created = resp.get_json()
    
    assert created["title"] == "C"
    assert created["day"] == 2
    assert created["number"] == 1
    assert "id" in created and isinstance(created["id"], str)

    


def test_delete_task_success():
    client, path = setup_test_data()  
    task_to_delete = {"day": 2, "number": 1}

    resp = client.delete("/api/tasks", json=task_to_delete)
    assert resp.status_code == 200
    deleted = resp.get_json()
    assert deleted["day"] == 2 and deleted["number"] == 1

    store = read_store(path)
    num_times = 0
    for t in store["list_of_tasks"]:
        if(t["title"] == "C" and t["day"] == 2 and t["number"] == 1):
            num_times += 1
    assert num_times == 0