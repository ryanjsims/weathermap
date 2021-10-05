alter table config add column version TEXT NOT NULL;
alter table credentials rename to credentials_old;
create table credentials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT
);

insert into credentials select * from credentials_old;
