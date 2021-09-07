DROP TABLE IF EXISTS credentials;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS birthdays;
DROP TABLE IF EXISTS schedules;

CREATE TABLE credentials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  credential_id INTEGER NOT NULL,
  firstname TEXT NOT NULL,
  lastname TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (credential_id) REFERENCES credentials (id)
);

CREATE TABLE birthdays (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  date TIMESTAMP NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  start_day INTEGER NOT NULL,
  end_day INTEGER NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL,
  enabled BOOLEAN NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE config (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  size INTEGER NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  z INTEGER NOT NULL,
  color INTEGER NOT NULL,
  options TEXT NOT NULL,
  dimensions INTEGER NOT NULL,
  img_size INTEGER NOT NULL,
  refresh_delay INTEGER NOT NULL,
  pause BOOLEAN NOT NULL,
);

insert into config (size, lat, lon, z, color, options, dimensions, img_size, refresh_delay, pause) 
            values (256, 33.317027, -111.875500, 9, 4, '0_0', 200000, 64, 5, false);