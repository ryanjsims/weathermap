import functools
from sqlite3.dbapi2 import IntegrityError

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from weatherportal.db import get_db
import logging as log

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        db = get_db()
        error = None
        if not username:
            error = "Username is required"
        elif not password:
            error = "Password is required"
        elif not firstname or not lastname:
            error = "Please provide both your first and last name"
        
        if not error:
            try:
                db.execute("INSERT INTO credentials (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                credential_id = db.execute("SELECT * FROM credentials where username = ?", 
                    (username,)
                ).fetchone()["id"]
                db.execute("INSERT INTO users (credential_id, firstname, lastname) VALUES (?, ?, ?)",
                    (credential_id, firstname, lastname)
                )
                db.commit()
            except db.IntegrityError:
                error = "Username {} is taken".format(username)
                db.rollback()
                log.error("Attempted duplicate registration of username " + username)
            except db.OperationalError as e:
                error = "Internal server error: (Send to Ryan)\n" + repr(e)
                db.rollback()
                log.error(repr(e))
            else:
                session.clear()
                return redirect(url_for("auth.login"))    
        flash(error)
    return render_template('auth/register.html')


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute("SELECT * FROM credentials where username = ?", (username,)).fetchone()
        if user is None or not check_password_hash(user['password'], password):
            error = "Incorrect login details, please try again later"
        
        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for('index'))
        flash(error)
    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM credentials WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view