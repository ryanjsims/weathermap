import sqlite3
from sqlite3.dbapi2 import Connection

import click
from flask import current_app, g
from flask.cli import with_appcontext
from typing import Optional

def row_to_dict(row: sqlite3.Row):
    to_return = {}
    for key in row.keys():
        to_return[key] = row[key]
    return to_return


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None) -> None:
    db: Optional[sqlite3.Connection] = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
        db.execute("update config set version = ? where id = 1;", (current_app.config['VERSION'],))
        db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def update_db():
    db = get_db()
    current_version = db.execute("select version from config;").fetchone()["version"]
    if current_version != current_app.config['VERSION']:
        with current_app.open_resource('update_schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
            db.execute("update config set version = ? where id = 1;", (current_app.config['VERSION'],))
            db.commit()
            return True
    return False


@click.command('update-db')
@with_appcontext
def update_db_command():
    """Clear the existing data and create new tables."""
    if update_db():
        click.echo('Updated the database schema.')
    else:
        click.echo("No update needed.")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_command)