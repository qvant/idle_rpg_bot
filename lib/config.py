import codecs
import datetime
import json
from .consts import LOG_CONFIG
from .security import is_password_encrypted, encrypt_password, decrypt_password
from .utility import get_logger

CONFIG_PARAM_LOG_LEVEL = "LOG_LEVEL"
CONFIG_PARAM_QUEUE_PASSWORD = "QUEUE_PASSWORD"
CONFIG_PARAM_QUEUE_USER = "QUEUE_USER"
CONFIG_PARAM_QUEUE_HOST = "QUEUE_HOST"
CONFIG_PARAM_QUEUE_PORT = "QUEUE_PORT"
CONFIG_PARAM_NEW_PATH = "CONFIG_PATH"
CONFIG_PARAM_CONFIG_RELOAD_TIME = "CONFIG_RELOAD_TIME"
CONFIG_PARAM_BOT_SECRET = "BOT_SECRET"
CONFIG_PARAM_BOT_SERVER_NAME = "BOT_SERVER_NAME"
CONFIG_PARAM_ADMIN_LIST = "ADMIN_ACCOUNTS"
CONFIG_PARAM_DB_PORT = "DB_PORT"
CONFIG_PARAM_DB_NAME = "DB_NAME"
CONFIG_PARAM_DB_HOST = "DB_HOST"
CONFIG_PARAM_DB_USER = "DB_USER"
CONFIG_PARAM_DB_PASSWORD = "DB_PASSWORD"


class Config:
    def __init__(self, file: str, reload: bool = False):
        f = file
        fp = codecs.open(f, 'r', "utf-8")
        config = json.load(fp)
        if not reload:
            self.logger = get_logger(LOG_CONFIG, is_system=True)
        self.logger.info("Read settings from {0}".format(file))
        self.file_path = file
        self.old_file_path = file
        self.server_name = config.get(CONFIG_PARAM_BOT_SERVER_NAME)
        self.queue_port = config.get(CONFIG_PARAM_QUEUE_PORT)
        self.queue_host = config.get(CONFIG_PARAM_QUEUE_HOST)
        self.queue_user = config.get(CONFIG_PARAM_QUEUE_USER)
        self.queue_password = config.get(CONFIG_PARAM_QUEUE_PASSWORD)
        self.secret = config.get(CONFIG_PARAM_BOT_SECRET)
        if not is_password_encrypted(self.secret):
            self.logger.info("Secret in plain text, start encryption")
            new_password = encrypt_password(self.secret, self.server_name, self.queue_port)
            self._save_secret(new_password)
            self.logger.info("Secret was encrypted and saved")
        else:
            self.logger.info("Secret in cypher text, start decryption")
            self.secret = decrypt_password(self.secret, self.server_name, self.queue_port)
            self.logger.info("Secret was decrypted")
        if not is_password_encrypted(self.queue_password):
            self.logger.info("Password in plain text, start encryption")
            new_password = encrypt_password(self.queue_password, self.server_name, self.queue_port)
            self._save_password(new_password)
            self.logger.info("Password was encrypted and saved")
        else:
            self.logger.info("Password in cypher text, start decryption")
            self.queue_password = decrypt_password(self.queue_password, self.server_name, self.queue_port)
            self.logger.info("Password was decrypted")
        self.db_name = config.get(CONFIG_PARAM_DB_NAME)
        self.db_port = config.get(CONFIG_PARAM_DB_PORT)
        self.db_host = config.get(CONFIG_PARAM_DB_HOST)
        self.db_user = config.get(CONFIG_PARAM_DB_USER)
        self.db_password_read = config.get(CONFIG_PARAM_DB_PASSWORD)
        if is_password_encrypted(self.db_password_read):
            self.logger.info("DB password encrypted, do nothing")
            self.db_password = decrypt_password(self.db_password_read, self.server_name, self.db_port)
        else:
            self.logger.info("DB password in plain text, start encrypt")
            password = encrypt_password(self.db_password_read, self.server_name, self.db_port)
            self._save_db_password(password)
            self.logger.info("DB password encrypted and save back in config")
            self.db_password = self.db_password_read
        self.log_level = config.get(CONFIG_PARAM_LOG_LEVEL)
        self.admin_list = config.get(CONFIG_PARAM_ADMIN_LIST)
        self.logger.setLevel(self.log_level)

        if config.get(CONFIG_PARAM_NEW_PATH) is not None:
            self.file_path = config.get(CONFIG_PARAM_NEW_PATH)
        self.reload_time = config.get(CONFIG_PARAM_CONFIG_RELOAD_TIME)
        self.next_reload = datetime.datetime.now()
        self.reloaded = False

    def _save_secret(self, password: str):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_BOT_SECRET] = password
        json.dump(config, fp, indent=2)
        fp.close()

    def _save_password(self, password: str):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_QUEUE_PASSWORD] = password
        json.dump(config, fp, indent=2)
        fp.close()

    def _save_db_password(self, password: str):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_DB_PASSWORD] = password
        json.dump(config, fp, indent=2)
        fp.close()
