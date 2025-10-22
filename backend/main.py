import json, uuid
from flask import Flask, request, jsonify, send_from_directory
import sys
from pathlib import Path

BACKEND_DIR  = Path(__file__).resolve().parent           # .../project/backend
PROJECT_ROOT = BACKEND_DIR.parent                        # .../project
FRONTEND_DIR = PROJECT_ROOT / "frontend"                 # .../project/frontend
DATA         = BACKEND_DIR / "tasks.json"               # .../project/tasks.json



app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/")


def load():
    with DATA.open("r") as f:
        print(f)
        return json.load(f)
    
def overwrite(tasks):
    with DATA.open("w") as f:
        json.dump(tasks, f, indent=2)

#displays the initial html
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

#getting the tasks from json file
@app.get("/api/tasks")
def get_tasks():
    return jsonify(load()["list_of_tasks"])

@app.post("/api/tasks")  
def add_task():
    # print("USING FILE:", DATA)
    # print("-------------------------------------------------------")
    d = request.get_json()
    title  = d.get("title").strip()
    day    = int(d.get("day"))
    number = int(d.get("number"))
    t = {"id": str(uuid.uuid4()), "title": title, "day": day, "number": number, "done": False}
    # print(t)
    data = load()
    data["number_of_tasks"]+=1
    # print(tasks)
    tasks = data["list_of_tasks"]
    for task in tasks:
        if(task["day"] == day and task["number"] == number):
            print("cannot add")
            return jsonify(t), 201
    # print(tasks)
    data["list_of_tasks"].append(t)
    overwrite(data)
    return jsonify(t), 201
    

@app.delete("/api/tasks")
def remove_task():
    d = request.get_json()
    day = number = int(d.get("day"))
    number = int(d.get("number"))
    data = load()
    new_tasks = []
    deleted_task = None
    for task in data["list_of_tasks"]:
        if(not(task["day"] == day and task["number"] == number)):
            new_tasks.append(task)
        else:
            deleted_task = task
    if deleted_task is None:
        return jsonify({"error": "Task not found"}), 404
    data["list_of_tasks"] = new_tasks
    overwrite(data)
    return jsonify(deleted_task), 200
    
    






if __name__ == "__main__":
    app.run()

