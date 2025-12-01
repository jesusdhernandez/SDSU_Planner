import json, uuid
from flask import Flask, request, jsonify, send_from_directory
import sys
from pathlib import Path

import requests from icalendar import Calendar

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

    #ics 
def normalize_to_date(dt_obj):
    """
    Convert an icalendar date/datetime (or similar) into a Python date.
    Canvas ICS may give either date or datetime objects.
    """
    if isinstance(dt_obj, datetime):
        return dt_obj.date()
    if isinstance(dt_obj, date):
        return dt_obj

    # Fallback: try parsing from string representation
    return datetime.fromisoformat(str(dt_obj)).date()


def load_ics_calendar(url: str) -> Calendar:
    """Download and parse an ICS calendar from a URL."""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return Calendar.from_ical(resp.content)


def get_ics_events_for_month(cal: Calendar, month: int, year: int):
    """
    Return a list of dicts for events in the given month/year.

    Each dict has:
      - summary
      - description
      - start_date (ISO string)
      - end_date (ISO string or None)
    """
    results = []

    for comp in cal.walk("VEVENT"):
        dtstart = comp.get("DTSTART")
        if not dtstart:
            continue

        start_date = normalize_to_date(dtstart.dt)
        if start_date.year != year or start_date.month != month:
            continue

        dtend = comp.get("DTEND")
        end_date = normalize_to_date(dtend.dt) if dtend else None

        summary = str(comp.get("SUMMARY", "Untitled"))
        description = str(comp.get("DESCRIPTION", ""))

        # If you want to only include *assignments*, you can do a simple filter:
        # if "assignment" not in summary.lower():
        #     continue

        results.append({
            "summary": summary,
            "description": description,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
        })

    # sort by start_date
    results.sort(key=lambda e: e["start_date"])
    return results
#displays the initial html
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
    
    




if __name__ == "__main__":
    app.run()

