DROP TABLE IF EXISTS credentials;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS birthdays;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS config;
DROP TABLE IF EXISTS holidays;

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
  realtime BOOLEAN NOT NULL
);

CREATE TABLE palette (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  color1 INTEGER,
  color2 INTEGER,
  color3 INTEGER,
  color4 INTEGER
);

CREATE TABLE holidays (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  message TEXT,
  path TEXT,
  palette_id INTEGER,
  FOREIGN KEY (palette_id) REFERENCES palette (id)
);

insert into config (size, lat, lon, z, color, options, dimensions, img_size, refresh_delay, pause, realtime) 
            values (256, 33.317027, -111.875500, 9, 4, '0_0', 200000, 64, 5, false, false);

--Christmas
insert into palette (color1, color2) values (0xE40A2D, 0x1FD537);
--Halloween
insert into palette (color1, color2) values (0xF4831B, 0x902EBB);
--Chinese New Year
insert into palette (color1, color2) values (0xCC232A, 0xCC9902);
--Valentines 
insert into palette (color1, color2) values (0xE07498, 0xC45E94);
--St Patrick's Day 
insert into palette (color1, color2) values (0x148E48, 0xF77E33);
--Juneteenth
insert into palette (color1, color2) values (0xE31C23, 0x00843E);
--4th of July
insert into palette (color1, color2, color3) values (0x3C3B6E, 0xFFFFFF, 0xB22234);
--Mexican Independance day
insert into palette (color1, color2, color3) values (0x006847, 0xFFFFFF, 0xCE1126);
--Thanksgiving
insert into palette (color1, color2) values (0xBE5634, 0xDEBF7E);

insert into holidays (name, message, path, palette_id) values ('New Year''s Day', '...in with the new!', './weatherportal/static/images/hourglass_full.png', NULL);
insert into holidays (name, message, path, palette_id) values ('Dr. Martin Luther King Jr./Civil Rights Day', 'MLK Jr. Day', NULL, NULL);
insert into holidays (name, message, path, palette_id) values ('Chinese New Year', 'Lunar New Year', NULL, 3);
insert into holidays (name, message, path, palette_id) values ('Valentine''s Day', 'Will you be my Valentine?', './weatherportal/static/images/heart.png', 4);
insert into holidays (name, message, path, palette_id) values ('St. Patrick''s Day', 'It looks pretty Irish out there!', './weatherportal/static/images/clover.png', 5);
insert into holidays (name, message, path, palette_id) values ('Easter Sunday', 'Happy Easter!', './weatherportal/static/images/cross.png', NULL);
insert into holidays (name, message, path, palette_id) values ('Mother''s Day', 'Yay for Mom!', './weatherportal/static/images/heart.png', NULL);
insert into holidays (name, message, path, palette_id) values ('Juneteenth National Independence Day', 'Juneteenth', './weatherportal/static/images/juneteenth.png', 6);
insert into holidays (name, message, path, palette_id) values ('Independence Day', 'America the Beautiful', NULL, 7);
insert into holidays (name, message, path, palette_id) values ('Día de la Independencia', '¡Viva Mexico!', NULL, 8);
insert into holidays (name, message, path, palette_id) values ('Halloween', 'Trick or Treat?', './weatherportal/static/images/pumpkin.png', 2);
insert into holidays (name, message, path, palette_id) values ('Día de los Muertos', 'Dia de los Muertos', './weatherportal/static/images/skull.png', NULL);
insert into holidays (name, message, path, palette_id) values ('Veterans Day', 'Celebrate our Veterans', NULL, NULL);
insert into holidays (name, message, path, palette_id) values ('Thanksgiving', 'What are you thankful for?', NULL, 9);
insert into holidays (name, message, path, palette_id) values ('Christmas Eve', NULL, './weatherportal/static/images/christmas_tree.png', 1);
insert into holidays (name, message, path, palette_id) values ('Christmas Day', 'Ho ho ho!', './weatherportal/static/images/christmas.png', 1);
insert into holidays (name, message, path, palette_id) values ('New Year''s Eve', 'Out with the old...', './weatherportal/static/images/hourglass_empty.png', NULL);