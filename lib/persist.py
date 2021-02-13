import psycopg2
from .config import Config
from .consts import PERSIST_LOAD_BATCH
from .utility import get_logger


class Persist:
    def __init__(self, config: Config):
        self.logger = get_logger("LOG_PERSIST", config.log_level)
        self.conn = psycopg2.connect(dbname=config.db_name, user=config.db_user,
                                     password=config.db_password, host=config.db_host, port=config.db_port)
        self.cursor = self.conn.cursor()
        self.was_error = False
        self.logger.info('Persist ready')

    def renew(self, config: Config):
        self.conn.close()
        self.__init__(config)

    def commit(self):
        self.conn.commit()

    def set(self, telegram_id: int, locale: str):
        # TODO: do named binds
        # Where my MERGE?
        # check row blocks when on conflict
        self.cursor.execute(
            """insert into idle_rpg_bot.user_locales as l (telegram_id, locale) 
                    values(%s, %s) 
                    on conflict (telegram_id) do update
                      set locale = %s where l.telegram_id = %s
            """, (telegram_id, locale, locale, telegram_id)
        )
        self.commit()

    def get_all(self):
        locales = {}
        cnt = 0
        self.cursor.execute(
            """
            select telegram_id, locale from idle_rpg_bot.user_locales 
            """
        )
        for telegram_id, locale in self.cursor:
            locales[telegram_id] = locale
            cnt += 1
            if cnt % PERSIST_LOAD_BATCH == 0:
                self.logger.info("Was loaded {0} user locales".format(cnt))
        self.logger.info("Was loaded {0} user locale settings".format(cnt))
        return locales
