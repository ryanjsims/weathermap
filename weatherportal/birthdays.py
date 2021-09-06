from weatherportal.auth import login, login_required
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from weatherportal.db import get_db
import logging as log

bp = Blueprint('birthdays', __name__, url_prefix='/birthdays')

def get_birthdays():
    db = get_db()
    return db.execute(
         """select u.firstname, u.lastname, b.date 
                from birthdays b 
                join users u on b.user_id 
            where strftime('%m/%d', b.date) = strftime('%m/%d', datetime(CURRENT_DATE, 'localtime'));"""
        ).fetchall()

@bp.route("/", endpoint="index")
@login_required
def birthdays():
    db = get_db()
    birthdays = db.execute("select * from birthdays join users on birthdays.user_id;").fetchall()
    print(birthdays)
    for birthday in birthdays:
        print(birthday)
    return render_template("birthdays/index.html", birthdays=birthdays)

@bp.route("/delete/<id>")
@login_required
def delete(id):
    db = get_db()
    db.execute("delete from birthdays where id = ?", (id,))
    db.commit()
    return redirect(url_for("birthdays.index"))

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    db = get_db()
    if request.method == "POST":
        id = int(request.form["user"])
        date = request.form["date"]
        db.execute("insert into birthdays (user_id, date) values (?, datetime(?))", (id, date))
        db.commit()
        return redirect(url_for("birthdays.index"))
    users = db.execute("select * from users join credentials on users.credential_id;").fetchall()
    return render_template("birthdays/create.html", users=users)