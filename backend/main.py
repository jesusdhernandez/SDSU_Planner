import json, uuid
from flask import Flask, request, jsonify, send_from_directory
import sys
from pathlib import Path
import webbrowser
import threading


HERE = Path(__file__).resolve().parent   

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # Running as a PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)       # temporary unpacked folder
    FRONTEND_DIR = BASE_DIR / "frontend"
    DATA = BASE_DIR / "tasks.json"
else:
    # Running from source
    PROJECT_ROOT = HERE.parent          # project root (..)
    FRONTEND_DIR = PROJECT_ROOT / "frontend"
    DATA = HERE / "tasks.json"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/")



def load():
    with DATA.open("r") as f:
        print(f)
        return json.load(f)
    
def overwrite(tasks):
    with DATA.open("w") as f:
        json.dump(tasks, f, indent=2)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

#getting the tasks from json file
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify(load()["list_of_tasks"])

@app.route("/api/tasks", methods=["POST"])
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
            return jsonify(t), 400
    # print(tasks)
    data["list_of_tasks"].append(t)
    overwrite(data)
    return jsonify(t), 201
    

@app.route("/api/tasks", methods=["DELETE"])
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

@app.route("/api/tasks", methods=["PUT"])
def modify_task():
    print("PUT request received")
    d = request.get_json()
    print(f"Request data: {d}")
    
    # Get the original identifiers (what we're searching for)
    original_day = int(d.get("original_day"))
    original_number = int(d.get("original_number"))
    
    # Get the new values (what we're updating to)
    new_title = d.get("title")
    new_day = int(d.get("day")) if d.get("day") else original_day
    new_number = int(d.get("number")) if d.get("number") else original_number
    
    print(f"Looking for task with day={original_day}, number={original_number}")
    print(f"Will update to: title={new_title}, day={new_day}, number={new_number}")
    
    data = load()
    task_found = False
    
    for task in data["list_of_tasks"]:
        if task["day"] == original_day and task["number"] == original_number:
            print(f"Found task: {task}")
            if new_title:
                task["title"] = new_title.strip()
            task["day"] = new_day
            task["number"] = new_number
            task_found = True
            print(f"Updated task: {task}")
            break
    
    if not task_found:
        print("Task not found!")
        return jsonify({"error": "Task not found"}), 404
    
    overwrite(data)
    print("Task saved successfully")
    return jsonify(task), 200
    
    





def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Open the browser 1 second after the server starts
    threading.Timer(1.0, open_browser).start()

    # Start Flask
    app.run(host="127.0.0.1", port=5000)
