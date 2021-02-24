import psycopg2
from .config import Config
from .consts import PERSIST_LOAD_BATCH
from .utility import get_logger


PERSIST_VERSION = 1
PERSIST_NAME = 'idle RPG bot'


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

    def check_version(self):
        self.cursor.execute("""
            select n_version from idle_rpg_bot.persist_version where v_name = %s
        """, (PERSIST_NAME, ))
        ver = self.cursor.fetchone()[0]
        self.logger.info("DB version {0}. Persist version {1}".format(ver, PERSIST_VERSION))
        assert ver == PERSIST_VERSION

    def set_locale(self, telegram_id: int, locale: str):
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

    def delete_locale(self, telegram_id: int):
        self.cursor.execute(
            """delete from idle_rpg_bot.user_locales l where l.telegram_id = %s""",
            (telegram_id,)
        )
        self.commit()

    def get_all_locale(self):
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
