CONFIG_PARAM_LOG_LEVEL = "LOG_LEVEL"
CONFIG_PARAM_QUEUE_PASSWORD = "QUEUE_PASSWORD"
CONFIG_PARAM_QUEUE_USER = "QUEUE_USER"
CONFIG_PARAM_QUEUE_HOST = "QUEUE_HOST"
CONFIG_PARAM_QUEUE_PORT = "QUEUE_PORT"
CONFIG_PARAM_NEW_PATH = "CONFIG_PATH"
CONFIG_PARAM_CONFIG_RELOAD_TIME = "CONFIG_RELOAD_TIME"
CONFIG_PARAM_BOT_SECRET = "BOT_SECRET"
CONFIG_PARAM_BOT_SERVER_NAME = "BOT_SERVER_NAME"
CONFIG_PARAM_SECRET_CONST = "Fk34c03"
CONFIG_PARAM_ADMIN_LIST = "ADMIN_ACCOUNTS"
CONFIG_PARAM_DB_PORT = "DB_PORT"
CONFIG_PARAM_DB_NAME = "DB_NAME"
CONFIG_PARAM_DB_HOST = "DB_HOST"
CONFIG_PARAM_DB_USER = "DB_USER"
CONFIG_PARAM_DB_PASSWORD = "DB_PASSWORD"

CMD_GET_CLASS_LIST = "get_class_list"
CMD_SET_CLASS_LIST = "set_class_list"
CMD_CREATE_CHARACTER = "create_character"
CMD_DELETE_CHARACTER = "delete_character"
CMD_GET_CHARACTER_STATUS = "get_character_status"
CMD_SERVER_SHUTDOWN_IMMEDIATE = "shutdown_immediate"
CMD_SERVER_SHUTDOWN_NORMAL = "shutdown_normal"
CMD_GET_SERVER_STATS = "get_server_stats"
CMD_SET_SERVER_STATS = "server_stats"
CMD_SERVER_OK = "server_ok"
CMD_FEEDBACK = "feedback"
CMD_FEEDBACK_RECEIVE = "feedback_receive"
CMD_GET_FEEDBACK = "get_feedback"
CMD_SENT_FEEDBACK = "sent_feedback"
CMD_CONFIRM_FEEDBACK = "confirm_feedback"

CHARACTER_NAME_MAX_LENGTH = 255

QUEUE_NAME_INIT = "InitQueue"
QUEUE_NAME_DICT = "DictionaryQueue"
QUEUE_NAME_CMD = "CommandQueue"
QUEUE_NAME_RESPONSES = "ResponsesQueue"

QUEUE_APP_ID = "Telegram bot"  # second after main app

MAIN_MENU_CREATE = "main_create"
MAIN_MENU_STATUS = "main_status"
MAIN_MENU_SETTINGS = "main_setting"
MAIN_MENU_FEEDBACK = "main_feedback"
MAIN_MENU_DELETE = "main_delete"
MAIN_MENU_ABOUT = "main_about"
MAIN_MENU_ADMIN = "main_admin"


ADMIN_MENU_STATS = "admin_stats"
ADMIN_MENU_BOT_STATS = "admin_bot_stats"
ADMIN_MENU_SHUTDOWN_BASIC = "admin_shutdown_basic"
ADMIN_MENU_GET_FEEDBACK = "admin_get_feedback"
SHUTDOWN_MENU_NORMAL = "shutdown_normal"
SHUTDOWN_MENU_IMMEDIATE = "shutdown_immediate"
SHUTDOWN_MENU_BOT = "shutdown_bot"
READ_MENU_DONE = "confirm__done"

MENU_ABOUT_TEXT = "This bot allow to play in ZPG (https://en.wikipedia.org/wiki/Zero-player_game) \"Idle RPG\", " \
                  "inspired " \
                  "by Progress Quest and Godville. You can create yor character and then check, how is perform. " \
                  "You can find sources of this bot on " \
                  "https://github.com/qvant/idle_rpg_bot and sources of main game on https://github.com/qvant/idleRPG."\
                  " Please, feel free to report bugs and give any other feedback via issues section of relevant github"

STAGE_SELECT_CLASS = "select_class"
STAGE_CHOOSE_NAME = "choose name"
STAGE_CONFIRM_DELETION = "CONFIRM_DELETION"

LOG_CONFIG = "Config"
LOG_MAIN = "Main"
LOG_QUEUE = "Queue"
LOG_TELEGRAM = "Telegram"

MAX_MENU_LENGTH = 25
MAX_FEEDBACK_LENGTH = 2048

PERSIST_LOAD_BATCH = 100
