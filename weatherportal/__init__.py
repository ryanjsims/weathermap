import os
import logging as log
from flask import Flask, g
from threading import Thread
from werkzeug.serving import make_server

display_config = {
    "size": 256,
    "lat": 33.317027,
    "lon": -111.875500,
    "z": 9,                           #zoom level
    "color": 4,                       #Weather channel colors
    "options": "0_0",                 #smoothed with no snow
    "dimensions": (200000, 200000),   #dimensions of final image in meters
    "img_size": (64, 64),             #Number of LEDs in matrix rows and columns
    "refresh_delay": 5,
    "pause": False
}


class ServerThread(Thread):
    def __init__(self, host, port, app):
        super().__init__()
        self.srv = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.app = app

    def run(self):
        log.info("Starting web server...")
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'weatherportal.sqlite'),
        DISPLAY_SETTINGS=None,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    if app.config["DISPLAY_SETTINGS"]:
        display_config = app.config["DISPLAY_SETTINGS"]

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.before_request
    def load_pagenav():
        g.pagenav = [
            {
                "endpoint": "index",
                "icon": "fa-calendar",
                "name": "Schedules"
            },
            {
                "endpoint": "config.controls",
                "icon": "fa-tools",
                "name": "Controls"
            },
            {
                "endpoint": "birthdays.index",
                "icon": "fa-birthday-cake",
                "name": "Birthdays"
            },
        ]
    
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import config
    app.register_blueprint(config.bp)
    app.add_url_rule('/', endpoint='index')

    from . import birthdays
    app.register_blueprint(birthdays.bp)

    return app


def initialize_server(test_config=None, host="localhost", port=8000):
    log.info("Initializing web server...")
    server = create_app(test_config)
    server_thread = ServerThread(host, port, server)
    server_thread.daemon = True
    return server_thread