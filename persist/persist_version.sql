create table idle_rpg_bot.persist_version
(
	v_name text,
	n_version integer,
	dt_update timestamp with time zone
);
alter table  idle_rpg_bot.persist_version owner to idle_rpg_bot;
insert into idle_rpg_bot.persist_version(v_name, n_version, dt_update) values('idle RPG bot', 1, current_timestamp);
commit;