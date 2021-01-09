import codecs
import datetime
import json
from .consts import *
from .security import is_password_encrypted, encrypt_password, decrypt_password
from .utility import get_logger


class Config:
    def __init__(self, file, reload=False):
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
            self.logger.info(self.secret)
        if not is_password_encrypted(self.queue_password):
            self.logger.info("Password in plain text, start encryption")
            new_password = encrypt_password(self.queue_password, self.server_name, self.queue_port)
            self._save_password(new_password)
            self.logger.info("Password was encrypted and saved")
        else:
            self.logger.info("Password in cypher text, start decryption")
            self.queue_password = decrypt_password(self.queue_password, self.server_name, self.queue_port)
            self.logger.info("Password was decrypted")
        self.turn_time = config.get(CONFIG_PARAM_TURN_TIME)
        self.log_level = config.get(CONFIG_PARAM_LOG_LEVEL)
        self.logger.setLevel(self.log_level)

        if config.get(CONFIG_PARAM_NEW_PATH) is not None:
            self.file_path = config.get(CONFIG_PARAM_NEW_PATH)
        self.reload_time = config.get(CONFIG_PARAM_CONFIG_RELOAD_TIME)
        self.next_reload = datetime.datetime.now()
        self.reloaded = False

    def _save_secret(self, password):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_BOT_SECRET] = password
        json.dump(config, fp, indent=2)
        fp.close()

    def _save_password(self, password):
        fp = codecs.open(self.file_path, 'r', "utf-8")
        config = json.load(fp)
        fp.close()
        fp = codecs.open(self.file_path, 'w', "utf-8")
        config[CONFIG_PARAM_QUEUE_PASSWORD] = password
        json.dump(config, fp, indent=2)
        fp.close()
