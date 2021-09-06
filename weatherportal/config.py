from sqlite3.dbapi2 import IntegrityError, OperationalError
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from weatherportal.auth import login_required
from weatherportal.db import get_db
import datetime

bp = Blueprint('config', __name__)

def parsetime(x):
    return datetime.time(*map(int, x.split(":")))

def time_in_range(time, start_str, end_str):
    start = parsetime(start_str)
    end = parsetime(end_str)
    curr = parsetime(time)
    if start <= end:
        return start < curr < end
    else:
        return start < curr or curr < end


def format_12hr(time_str):
    time = parsetime(time_str)
    return time.strftime("%I:%M %p")

@bp.route("/")
@login_required
def overview():
    db = get_db()
    schedules = db.execute("select * from schedules").fetchall()
    print(schedules)
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