from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session, jsonify, json
)
from werkzeug.exceptions import abort

from weatherportal.auth import login_required
from weatherportal.db import get_db
from weatherportal.config import get_display_config, update_display_config
import os, sys

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route("/pause/<state>", methods=["PUT"])
@login_required
def pause(state):
    update_display_config(pause=state == "1")
    return jsonify(get_display_config())

@bp.route("/settings", methods=["GET", "PUT"])
@login_required
def settings():
    if request.method == "PUT":
        request_data = request.get_json(force=True, silent=True)
        if request_data is not None:
            update_display_config(**request_data)
    return jsonify(get_display_config())

@bp.route("/reboot")
@login_required
def reboot():
    os.system("sudo reboot")
    sys.exit(0)
