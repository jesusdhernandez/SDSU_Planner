import json, uuid
from flask import Flask, request, jsonify, send_from_directory
import sys
from pathlib import Path
import webbrowser
import threading
import datetime


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


def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def get_days_in_month(month, year):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 1 and is_leap_year(year):
        return 29
    return days[month]


def month_to_day_range(month, year=None):
    """Return (start_day, end_day) day-of-year range for 0-based month."""
    if year is None:
        year = datetime.date.today().year
    start = 1
    for m in range(0, month):
        start += get_days_in_month(m, year)
    days = get_days_in_month(month, year)
    end = start + days - 1
    return start, end

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


@app.route("/api/tasks/month/<int:month>", methods=["DELETE", "POST", "OPTIONS"])
def clear_month(month):
    """Clear all tasks for the given 0-based month index."""
    year = datetime.date.today().year
    start, end = month_to_day_range(month, year)
    data = load()
    original = data.get("list_of_tasks", [])
    remaining = [t for t in original if not (start <= int(t.get("day")) <= end)]
    deleted_tasks = [t for t in original if (start <= int(t.get("day")) <= end)]
    deleted_count = len(deleted_tasks)
    if deleted_count == 0:
        return jsonify({"deleted": 0, "tasks": []}), 200
    data["list_of_tasks"] = remaining
    data["number_of_tasks"] = len(remaining)
    overwrite(data)
    return jsonify({"deleted": deleted_count, "tasks": deleted_tasks}), 200


@app.route("/api/tasks/clear_all", methods=["DELETE", "POST", "OPTIONS"])
def clear_all():
    """Clear all tasks from storage and return deleted tasks for undo."""
    data = load()
    original = data.get("list_of_tasks", [])
    deleted_tasks = list(original)
    deleted_count = len(deleted_tasks)
    if deleted_count == 0:
        return jsonify({"deleted": 0, "tasks": []}), 200
    data["list_of_tasks"] = []
    data["number_of_tasks"] = 0
    overwrite(data)
    return jsonify({"deleted": deleted_count, "tasks": deleted_tasks}), 200

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
    task = None
    
    # Find the task to modify
    for t in data["list_of_tasks"]:
        if t["day"] == original_day and t["number"] == original_number:
            task = t
            print(f"Found task: {task}")
            break
    
    if not task:
        print("Task not found!")
        return jsonify({"error": "Task not found"}), 404
    
    # Check if moving to a different day or changing number
    moving_day = (new_day != original_day)
    changing_number = (new_number != original_number)
    
    if moving_day:
        # Moving to a different day
        print(f"Moving task from day {original_day} to day {new_day}")
        
        # Decrement numbers on original day for tasks after the removed slot
        for t in data["list_of_tasks"]:
            if t is task:
                continue
            if t["day"] == original_day and t["number"] > original_number:
                t["number"] -= 1
                print(f"Decremented task on original day: {t}")
        
        # Check for conflicts on destination day
        conflict = False
        for t in data["list_of_tasks"]:
            if t is task:
                continue
            if t["day"] == new_day and t["number"] == new_number:
                conflict = True
                break
        
        if conflict:
            # Increment numbers on destination day for tasks at/after insertion slot
            for t in data["list_of_tasks"]:
                if t is task:
                    continue
                if t["day"] == new_day and t["number"] >= new_number:
                    t["number"] += 1
                    print(f"Incremented task on destination day: {t}")
    
    elif changing_number:
        # Reordering within same day
        print(f"Reordering task on day {original_day} from number {original_number} to {new_number}")
        
        if new_number > original_number:
            # Moving down: shift tasks between old and new position up
            for t in data["list_of_tasks"]:
                if t is task:
                    continue
                if t["day"] == original_day and original_number < t["number"] <= new_number:
                    t["number"] -= 1
                    print(f"Shifted task up: {t}")
        elif new_number < original_number:
            # Moving up: shift tasks between new and old position down
            for t in data["list_of_tasks"]:
                if t is task:
                    continue
                if t["day"] == original_day and new_number <= t["number"] < original_number:
                    t["number"] += 1
                    print(f"Shifted task down: {t}")
    
    # Update the task
    if new_title:
        task["title"] = new_title.strip()
    task["day"] = new_day
    task["number"] = new_number
    print(f"Updated task: {task}")
    
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
