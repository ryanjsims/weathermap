from sqlite3.dbapi2 import IntegrityError, OperationalError
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from weatherportal.auth import login_required
from weatherportal.db import get_db

bp = Blueprint('config', __name__)

def time_in_range(time, start, end):
    parsetime = lambda x: map(int, x.split(":"))
    start_hr, start_min = parsetime(start)
    end_hr, end_min = parsetime(end)
    curr_hr, curr_min = parsetime(time)
    hours = []
    i = start_hr + 1
    while i < end_hr:
        hours.append(i)
        i = (i + 1) % 24
    return (curr_hr in hours 
        or curr_hr == start_hr and curr_min >= start_min
        or curr_hr == end_hr and curr_min <= end_min)

def format_12hr(time):
    parsetime = lambda x: map(int, x.split(":"))
    half = "am"
    hour, min = parsetime(time)
    if hour == 0:
        hour = 12
    elif hour == 12:
        half = "pm"
    elif hour > 12:
        half = "pm"
        hour = hour % 12
    return "{:02d}:{:02d} {}".format(hour, min, half)

@bp.route("/")
@login_required
def overview():
    db = get_db()
    schedules = db.execute("select * from schedules").fetchall()
    return render_template("config/index.html", schedules=schedules, format_12hr=format_12hr)

@bp.route("/controls")
@login_required
def controls():
    return render_template("config/controls.html")

@bp.route("/create_schedule", methods=["GET", "POST"])
@login_required
def create_schedule():
    if request.method == "POST":
        error = None
        start = request.form["starttime"]
        end = request.form["endtime"]
        enabled = request.form["state"]
        try:
            db = get_db()
            schedules = db.execute("select * from schedules order by start_time").fetchall()
            for schedule in schedules:
                if time_in_range(start, schedule["start_time"], schedule["end_time"]) or time_in_range(end, schedule["start_time"], schedule["end_time"]):
                    error = "Conflicting schedule: {} starting at {} ending at {}".format(schedule["enabled"], schedule["start_time"], schedule["end_time"])
                    break
            if not error:
                db.execute("insert into schedules (user_id, start_time, end_time, enabled) values (?, ?, ?, ?)",
                    (session.get("user_id"), start, end, enabled == "on")
                )
                db.commit()
        except OperationalError as e:
            error = "Internal server error: {}".format(str(e))
        else:
            return redirect(url_for("index"))
        flash(error)
        
    return render_template("config/schedule.html")

@bp.route("/delete_schedule/<id>")
@login_required
def delete_schedule(id):
    db = get_db()
    error = None
    try:
        db.execute("delete from schedules where id = ?", (id,))
        db.commit()
    except OperationalError as e:
        error = "Internal Server Error: {}".format(str(e))
    if error:
        flash(error)
    return redirect(url_for("index"))