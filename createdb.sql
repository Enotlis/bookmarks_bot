create table manga(
	url_manga varchar(500) primary key,
	manga_name varchar(500),
	last_chapte varchar(5)
);

create table bookmark(
	id bigserial primary key,
	chat_id integer,
	manga_id varchar(500),
	FOREIGN KEY(manga_id) REFERENCES manga(url_manga) ON DELETE CASCADE
);