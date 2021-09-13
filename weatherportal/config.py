from sqlite3.dbapi2 import IntegrityError, OperationalError
from dateutil.tz.tz import tzlocal
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session, jsonify
)
from werkzeug.exceptions import abort

from weatherportal.auth import login_required
from weatherportal.db import get_db, row_to_dict
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

# Create datetime offset from the start of the week by weekday days with the hours and minutes of time t
#    Sunday is the first day of the week if sunday_is_zero is True (default)
#    otherwise Monday is the first day of the week
def from_dowt(weekday: int, t: datetime.time, sunday_is_zero=True):
    now = datetime.datetime.now(tzlocal())
    week_start = now - datetime.timedelta(days=(now.weekday() + 1 if sunday_is_zero else 0) % 7)
    return (week_start + datetime.timedelta(days=weekday)).replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)

def get_current_schedules():
    db = get_db()
    schedules = db.execute("select * from schedules").fetchall()
    current = []
    now = datetime.datetime.now(tzlocal())
    for schedule in schedules:
        offset = 7 if schedule["end_day"] < schedule["start_day"] else 0
        start = from_dowt(schedule["start_day"], schedule["start_time"].time())
        end = from_dowt(schedule["end_day"] + offset, schedule["end_time"].time())
        if start <= now <= end:
            current.append(schedule)
    return current

def get_display_config():
    db = get_db()
    cfg = db.execute("select * from config;").fetchone()
    to_return = row_to_dict(cfg)
    to_return["dimensions"] = (cfg["dimensions"], cfg["dimensions"])
    to_return["img_size"] = (cfg["img_size"], cfg["img_size"])
    return to_return

# Unchanged If None
def uin(orig, new):
    if new is not None:
        return new
    return orig

def update_display_config(size = None, lat = None, lon = None, z = None, color = None, options = None, dimensions = None, img_size = None, refresh_delay = None, pause = None, realtime = None):
    db = get_db()
    cfg = db.execute("select * from config;").fetchone()
    to_update = (
            uin(cfg["size"], size), 
            uin(cfg["lat"], lat), 
            uin(cfg["lon"], lon), 
            uin(cfg["z"], z), 
            uin(cfg["color"], color), 
            uin(cfg["options"], options), 
            uin(cfg["dimensions"], dimensions), 
            uin(cfg["img_size"], img_size), 
            uin(cfg["refresh_delay"], refresh_delay), 
            uin(cfg["pause"], pause),
            uin(cfg["realtime"], realtime)
        )
    print(to_update)
    db.execute("update config set (size, lat, lon, z, color, options, dimensions, img_size, refresh_delay, pause, realtime) = (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) where id = 1;",
        to_update
    )
    db.commit()

@bp.route("/")
@login_required
def overview():
    db = get_db()
    schedules = db.execute("select * from schedules").fetchall()
    return render_template("config/index.html", schedules=schedules, days=days)

@bp.route("/settings")
@login_required
def settings():
    return render_template("config/settings.html", display_config=get_display_config())

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