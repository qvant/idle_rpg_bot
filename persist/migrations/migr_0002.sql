alter table idle_rpg_bot.user_locales alter column telegram_id type bigint;
update idle_rpg_bot.persist_version set n_version=2, dt_update = current_timestamp where v_name = 'idle RPG bot' ;
commit;