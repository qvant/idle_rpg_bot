import codecs
import datetime
import json
from .consts import *
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
        self.secret = config.get(CONFIG_PARAM_BOT_SECRET)
        self.turn_time = config.get(CONFIG_PARAM_TURN_TIME)
        self.log_level = config.get(CONFIG_PARAM_LOG_LEVEL)
        self.logger.setLevel(self.log_level)

        if config.get(CONFIG_PARAM_NEW_PATH) is not None:
            self.file_path = config.get(CONFIG_PARAM_NEW_PATH)
        self.reload_time = config.get(CONFIG_PARAM_CONFIG_RELOAD_TIME)
        self.next_reload = datetime.datetime.now()
        self.reloaded = False


