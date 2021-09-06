from sqlite3.dbapi2 import IntegrityError, OperationalError
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from weatherportal.auth import login_required
from weatherportal.db import get_db
import datetime

bp = Blueprint('config', __name__)

days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

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

def get_current_schedules():
    db = get_db()
    return db.execute(
         """select * 
                from schedules 
            where start_day <= strftime('%w', date(CURRENT_DATE, 'localtime'))
                    and time(start_time) <= time(CURRENT_TIME, 'localtime')
                    and end_day >= strftime('%w', date(CURRENT_DATE, 'localtime'))
                    and time(end_time) >= time(CURRENT_TIME, 'localtime');"""
        ).fetchall()

@bp.route("/")
@login_required
def overview():
    db = get_db()
    schedules = db.execute("select * from schedules").fetchall()
    return render_template("config/index.html", schedules=schedules, days=days)

@bp.route("/controls")
@login_required
def controls():
    return render_template("config/controls.html")

@bp.route("/create_schedule", methods=["GET", "POST"])
@login_required
def create_schedule():
    if request.method == "POST":
        error = None
        start = parsetime(request.form["starttime"])
        end = parsetime(request.form["endtime"])
        startday = request.form["startday"]
        endday = request.form["endday"]
        enabled = request.form["state"]
        try:
            db = get_db()            
            if not error:
                db.execute("insert into schedules (user_id, start_day, end_day, start_time, end_time, enabled) values (?, ?, ?, ?, ?, ?)",
                    (session.get("user_id"), startday, endday, start.strftime("1970-01-01 %H:%M:00"), end.strftime("1970-01-01 %H:%M:00"), enabled == "on")
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