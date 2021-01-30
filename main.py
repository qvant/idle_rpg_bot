import argparse
import datetime
import json
import psutil
import os
import sys
import time


import pika
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, CallbackQueryHandler

from lib.config import Config
from lib.consts import *
from lib.l18n import L18n
from lib.messages import *
from lib.persist import Persist
from lib.utility import get_logger

global class_list
global out_channel
global creation_process
global deletion_process
global feedback_process
global feedback_reading
global characters
global updater
global queue_logger
global telegram_logger
global config
global is_shutdown
global user_locales
global translations
global startup_time
global user_settings


def get_locale(update, chat_id=None):
    global user_locales
    global translations
    if update is not None or chat_id is not None:
        if chat_id is None:
            chat_id = update.effective_chat.id
        locale = user_locales.get(chat_id)
        if locale is None and update is not None:
            if update.callback_query is not None:
                locale = update.callback_query.from_user.language_code
            else:
                locale = update.message.from_user.language_code
            user_locales[chat_id] = locale

        if locale in translations.keys():
            return translations[locale]
    return translations['ru']


def start(update, context):
    global telegram_logger
    trans = get_locale(update)
    msg = trans.get_message(M_ABOUT_ME)
    reply_markup = InlineKeyboardMarkup(main_keyboard(update.effective_chat.id, trans))
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
    telegram_logger.info("Proceed start command from user {0}".format(update.effective_chat.id))


def pretty_menu(menu):
    res = [[]]
    cur_menu_len = 0
    for i in menu:
        if len(i.text) + cur_menu_len >= MAX_MENU_LENGTH:
            res.append([])
            cur_menu_len = 0
        res[len(res) - 1].append(i)
        cur_menu_len += len(i.text)
    return res


def class_keyboard(trans):
    keyboard = []
    for i in class_list:
        keyboard.append(InlineKeyboardButton(trans.get_message(i), callback_data="class_" + str(i)))
    return pretty_menu(keyboard)


def main_keyboard(chat_id, trans):
    global config
    keyboard = [
        InlineKeyboardButton(trans.get_message(M_NEW_CHARACTER), callback_data=MAIN_MENU_CREATE),
        InlineKeyboardButton(trans.get_message(M_ABOUT_LABEL), callback_data=MAIN_MENU_ABOUT),
        InlineKeyboardButton(trans.get_message(M_DELETE_CHARACTER), callback_data=MAIN_MENU_DELETE),
        InlineKeyboardButton(trans.get_message(M_GET_CHARACTER), callback_data=MAIN_MENU_STATUS),
        InlineKeyboardButton(trans.get_message(M_SETTINGS), callback_data=MAIN_MENU_SETTINGS),
        InlineKeyboardButton(trans.get_message(M_FEEDBACK), callback_data=MAIN_MENU_FEEDBACK),
    ]
    if chat_id in config.admin_list:
        keyboard.append(InlineKeyboardButton(trans.get_message(M_ADMIN_LABEL), callback_data=MAIN_MENU_ADMIN))

    return pretty_menu(keyboard)


def admin_keyboard(trans):
    keyboard = [
        InlineKeyboardButton(trans.get_message(M_SERVER_STATS), callback_data=ADMIN_MENU_STATS),
        InlineKeyboardButton(trans.get_message(M_BOT_STATS), callback_data=ADMIN_MENU_BOT_STATS),
        InlineKeyboardButton(trans.get_message(M_SHUTDOWN_LABEL), callback_data=ADMIN_MENU_SHUTDOWN_BASIC),
        InlineKeyboardButton(trans.get_message(M_GET_FEEDBACK), callback_data=ADMIN_MENU_GET_FEEDBACK),
    ]

    return pretty_menu(keyboard)


def read_keyboard(trans):
    keyboard = [
        InlineKeyboardButton(trans.get_message(M_FEEDBACK_DONE), callback_data=READ_MENU_DONE)
    ]

    return pretty_menu(keyboard)


def shutdown_keyboard(trans):
    keyboard = [
         InlineKeyboardButton(trans.get_message(M_SHUTDOWN_NORMAL), callback_data=SHUTDOWN_MENU_NORMAL),
         InlineKeyboardButton(trans.get_message(M_SHUTDOWN_IMMEDIATE), callback_data=SHUTDOWN_MENU_IMMEDIATE),
         InlineKeyboardButton(trans.get_message(M_SHUTDOWN_BOT), callback_data=SHUTDOWN_MENU_BOT)
    ]

    return pretty_menu(keyboard)


def locale_keyboard():
    global translations
    keyboard = []
    for i in translations:
        keyboard.append(InlineKeyboardButton(i, callback_data="LOCALE_" + i))

    return pretty_menu(keyboard)


def status(update, context):
    global telegram_logger
    trans = get_locale(update)
    cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_GET_CHARACTER_STATUS, "locale": trans.code}
    msg = trans.get_message(M_REQUESTED_STATUS)
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    enqueue_command(cmd)
    telegram_logger.info("Proceed status command from user {0}".format(update.effective_chat.id))


def create(update, context):
    global creation_process
    global telegram_logger
    trans = get_locale(update)
    msg = trans.get_message(M_CHOOSE_CLASS)
    keyboard = class_keyboard(trans)
    reply_markup = InlineKeyboardMarkup(keyboard)
    creation_process[update.effective_chat.id] = {"stage": STAGE_SELECT_CLASS}
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
    telegram_logger.info("Initialized character creation from user {0}".format(update.effective_chat.id))


def delete(update, context):
    global deletion_process
    global telegram_logger
    deletion_process[update.effective_chat.id] = {"stage": STAGE_CONFIRM_DELETION}
    trans = get_locale(update)
    msg = trans.get_message(M_PRINT_CONFIRM)
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    telegram_logger.info("Initialized character deletion from user {0}".format(update.effective_chat.id))


def settings(update, context):
    global telegram_logger
    global translations
    trans = get_locale(update)
    msg = trans.get_message(M_CHOOSE_LANGUAGE)
    keyboard = locale_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
    telegram_logger.info("Sent language settings menu to user {0}".format(update.effective_chat.id))


def feedback(update, context):
    global telegram_logger
    global translations
    global feedback_process
    trans = get_locale(update)
    msg = trans.get_message(M_FEEDBACK_PROMPT)
    feedback_process[update.effective_chat.id] = 1
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
    telegram_logger.info("Sent feedback prompt to user {0}".format(update.effective_chat.id))


def set_locale(update, context):
    global telegram_logger
    global translations
    global user_locales
    global user_settings
    language = update["callback_query"]["data"][7:]
    if language in translations.keys():
        user_locales[update.effective_chat.id] = language
        user_settings.set(update.effective_chat.id, language)
        trans = get_locale(update)
        msg = trans.get_message(M_LANGUAGE_CHOSEN).format(language)
        keyboard = main_keyboard(update.effective_chat.id, trans)
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
        telegram_logger.info("Set locale {1} for user {0}".format(update.effective_chat.id, language))
    else:
        trans = get_locale(update)
        msg = trans.get_message(M_INCORRECT_LANGUAGE).format(language)
        keyboard = main_keyboard(update.effective_chat.id, trans)
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
        telegram_logger.error("Can't set not existent locale {1} for user {0}".format(update.effective_chat.id, language))


def about(update, context):
    global telegram_logger
    trans = get_locale(update)
    msg = trans.get_message(M_ABOUT_TEXT)
    keyboard = main_keyboard(update.effective_chat.id, trans)
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
    telegram_logger.info("Sent \"About\" to user {0}".format(update.effective_chat.id))


def admin(update, context):
    global telegram_logger
    global config
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_ABOUT_TEXT)
        keyboard = admin_keyboard(trans)
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
        telegram_logger.info("Sent \"Admin menu\" to user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"Admin menu\" from user {0}".format(update.effective_chat.id))


def shutdown(update, context):
    global telegram_logger
    global config
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_SHUTDOWN_PANEL)
        keyboard = shutdown_keyboard(trans)
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
        telegram_logger.info("Sent \"shutdown menu\" to user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"shutdown menu\" from user {0}".format(update.effective_chat.id))


def get_feedback(update, context):
    global telegram_logger
    global config
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_GET_FEEDBACK)
        cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_GET_FEEDBACK, "locale": trans.code}
        enqueue_command(cmd, True)
        keyboard = admin_keyboard(trans)
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
        telegram_logger.info("Sent get_feedback from user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"feedback menu\" from user {0}".format(update.effective_chat.id))


def ask_server_stats(update, context):
    global telegram_logger
    global config
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_REQUESTED_SERVER_STATUS)
        cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_GET_SERVER_STATS, "locale": trans.code}
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        enqueue_command(cmd, True)
        telegram_logger.info("Sent server stats request from user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"ask_server_stats\" from user {0}".format(update.effective_chat.id))


def show_bot_stats(update, context):
    global telegram_logger
    global config
    global startup_time
    if update.effective_chat.id in config.admin_list:
        process = psutil.Process(os.getpid())
        memory_used = round(process.memory_full_info().rss / 1024 ** 2, 2)
        memory_percent = round(process.memory_percent("rss"), 2)
        cpu_times = process.cpu_times()
        cpu_percent = process.cpu_percent()
        msg = "Bot started at {0} (uptime {1} second).".format(startup_time,
                                                               datetime.datetime.now().replace(microsecond=0)
                                                               - startup_time)
        msg += chr(10)
        msg += "Used memory: {0} mb, {1} % from total".format(memory_used, memory_percent)
        msg += chr(10)
        msg += "CPU times: {0}".format(cpu_times)
        msg += chr(10)
        msg += "CPU percent {0}".format(cpu_percent)
        msg += chr(10)
        trans = get_locale(update)
        reply_markup = InlineKeyboardMarkup(admin_keyboard(trans))
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)
        telegram_logger.info("Sent server stats request from user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"show_bot_stats\" from user {0}".format(update.effective_chat.id))


def send_shutdown_immediate(update, context):
    global telegram_logger
    global config
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_SENT_SHUTDOWN_IMMEDIATE)
        cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_SERVER_SHUTDOWN_IMMEDIATE, "locale": trans.code}
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg,)
        enqueue_command(cmd, True)
        telegram_logger.info("Sent command on immediate shutdown from user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"send_shutdown_immediate\" from user {0}".
                              format(update.effective_chat.id))


def send_shutdown_bot(update, context):
    global telegram_logger
    global config
    global is_shutdown
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_SENT_SHUTDOWN_BOT)
        telegram_logger.info("Shutdown requested")
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, )
        is_shutdown = True
    else:
        telegram_logger.error("Illegal access to \"send_shutdown_bot\" from user {0}".format(update.effective_chat.id))


def send_shutdown_normal(update, context):
    global telegram_logger
    global config
    if update.effective_chat.id in config.admin_list:
        trans = get_locale(update)
        msg = trans.get_message(M_SENT_SHUTDOWN)
        cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_SERVER_SHUTDOWN_NORMAL, "locale": trans.code}
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg,)
        enqueue_command(cmd, True)
        telegram_logger.info("Sent command on shutdown from user {0}".format(update.effective_chat.id))
    else:
        telegram_logger.error("Illegal access to \"send_shutdown_normal\" from user {0}".
                              format(update.effective_chat.id))


def class_menu(update, context):
    global creation_process
    global telegram_logger
    is_correct = False
    if update.effective_chat.id in creation_process.keys():
        if creation_process[update.effective_chat.id]["stage"] == STAGE_SELECT_CLASS:
            is_correct = True
    if is_correct:
        char_class = update["callback_query"]["data"][6:]
        creation_process[update.effective_chat.id]["class"] = char_class
        creation_process[update.effective_chat.id]["stage"] = STAGE_CHOOSE_NAME
        trans = get_locale(update)
        msg = trans.get_message(M_ENTER_NAME)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg.
                                 format(trans.get_message(char_class)))
        telegram_logger.info("Character creation by user {0} advanced to name input stage".
                             format(update.effective_chat.id))
    else:
        telegram_logger.warning("Character creation by user {0} not advanced to name input stage because of reasons".
                                format(update.effective_chat.id))
        create(update, context)


def read_done(update, context):
    global feedback_reading
    global telegram_logger
    is_correct = False
    if update.effective_chat.id in feedback_reading.keys():
        is_correct = True
    if is_correct:
        trans = get_locale(update)
        msg = trans.get_message(M_FEEDBACK_SENT)
        cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_CONFIRM_FEEDBACK, "locale": trans.code,
               "message_id": feedback_reading[update.effective_chat.id]}
        enqueue_command(cmd, True)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        telegram_logger.info("Reading message id {0} done by user {1} send".
                             format(feedback_reading[update.effective_chat.id], update.effective_chat.id))
        del feedback_reading[update.effective_chat.id]
    else:
        telegram_logger.warning("Reading done failed".
                                format(update.effective_chat.id))
        start(update, context)


def main_menu(update, context):
    global telegram_logger
    global config
    cur_item = update["callback_query"]["data"]
    telegram_logger.debug("Main menu called. Update {}".format(update))
    telegram_logger.debug("Main menu called. Context {}".format(context))
    telegram_logger.info("Received command {0} from user {1} in main menu".
                         format(cur_item, update.effective_chat.id))
    if cur_item == MAIN_MENU_CREATE:
        create(update, context)
    elif cur_item == MAIN_MENU_STATUS:
        status(update, context)
    elif cur_item == MAIN_MENU_DELETE:
        delete(update, context)
    elif cur_item == MAIN_MENU_ABOUT:
        about(update, context)
    elif cur_item == MAIN_MENU_SETTINGS:
        settings(update, context)
    elif cur_item == MAIN_MENU_FEEDBACK:
        feedback(update, context)
    elif cur_item == MAIN_MENU_ADMIN:
        if update.effective_chat.id in config.admin_list:
            admin(update, context)
        else:
            telegram_logger.error("Received admin command {0} from ordinary user {1} in main menu".
                                  format(cur_item, update.effective_chat.id))
    else:
        telegram_logger.error("Received unknown command {0} from user {1} in main menu".
                              format(cur_item, update.effective_chat.id))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknown command")


def admin_menu(update, context):
    global telegram_logger
    cur_item = update["callback_query"]["data"]
    telegram_logger.info("Received command {0} from user {1} in admin menu".
                         format(cur_item, update.effective_chat.id))
    if cur_item == ADMIN_MENU_STATS:
        ask_server_stats(update, context)
    elif cur_item == ADMIN_MENU_BOT_STATS:
        show_bot_stats(update, context)
    elif cur_item == ADMIN_MENU_SHUTDOWN_BASIC:
        shutdown(update, context)
    elif cur_item == ADMIN_MENU_GET_FEEDBACK:
        get_feedback(update, context)
    else:
        telegram_logger.error("Received unknown command {0} from user {1} in admin menu".
                              format(cur_item, update.effective_chat.id))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknown command")


def shutdown_menu(update, context):
    global telegram_logger
    cur_item = update["callback_query"]["data"]
    telegram_logger.info("Received command {0} from user {1} in shutdown menu".
                         format(cur_item, update.effective_chat.id))
    if cur_item == SHUTDOWN_MENU_NORMAL:
        send_shutdown_normal(update, context)
    elif cur_item == SHUTDOWN_MENU_IMMEDIATE:
        send_shutdown_immediate(update, context)
    elif cur_item == SHUTDOWN_MENU_BOT:
        send_shutdown_bot(update, context)
    else:
        telegram_logger.error("Received unknown command {0} from user {1} in shutdown menu".
                              format(cur_item, update.effective_chat.id))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknown command")


def read_menu(update, context):
    global telegram_logger
    cur_item = update["callback_query"]["data"]
    telegram_logger.info("Received command {0} from user {1} in read menu".
                         format(cur_item, update.effective_chat.id))
    if cur_item == READ_MENU_DONE:
        read_done(update, context)
    else:
        telegram_logger.error("Received unknown command {0} from user {1} in read menu".
                              format(cur_item, update.effective_chat.id))
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknown command")


def enqueue_command(obj, system=False):
    global queue_logger
    global config
    if system:
        queue_name = QUEUE_NAME_INIT
    else:
        queue_name = QUEUE_NAME_CMD
    obj["sent_by_admin"] = obj.get("user_id") in config.admin_list
    msg_body = json.dumps(obj)
    try:
        queue = get_mq_connect(config)
        channel = queue.channel()
        channel.basic_publish(exchange="", routing_key=queue_name,
                              body=msg_body, properties=pika.BasicProperties(delivery_mode=2,
                                                                             content_type="application/json",
                                                                             content_encoding="UTF-8",
                                                                             app_id=QUEUE_APP_ID))
        queue.close()
        queue_logger.info("Sent command {0} in queue {1}".format(msg_body, queue))
    except pika.exceptions.AMQPError as exc:
        queue_logger.critical("Error {2} when Sent command {0} in queue {1}".format(msg_body, queue_name, exc))


def echo(update, context):
    global creation_process
    global deletion_process
    global feedback_process
    global telegram_logger
    telegram_logger.debug("Echo: update: {0}, context {1}".format(update, context))
    trans = get_locale(update, update.effective_chat.id)
    is_correct = False
    if update.effective_chat.id in creation_process.keys():
        if creation_process[update.effective_chat.id]["stage"] == STAGE_CHOOSE_NAME:
            if CHARACTER_NAME_MAX_LENGTH < len(update["message"]["text"]):
                msg = trans.get_message(M_NAME_TOO_LONG).format(CHARACTER_NAME_MAX_LENGTH)
                context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
            else:
                is_correct = True
    if is_correct:
        creation_process[update.effective_chat.id]["stage"] = "confirm"
        creation_process[update.effective_chat.id]["name"] = update["message"]["text"]
        msg = trans.get_message(M_CHECK_NAME)
        context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_CREATE_CHARACTER,
               "name": creation_process[update.effective_chat.id].get("name"),
               "class": creation_process[update.effective_chat.id].get("class"),
               "locale": trans.code}
        enqueue_command(cmd)
    elif update.effective_chat.id in deletion_process.keys():
        if deletion_process[update.effective_chat.id]["stage"] == STAGE_CONFIRM_DELETION:
            if update["message"]["text"] == "CONFIRM":
                cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_DELETE_CHARACTER, "locale": trans.code}
                msg = trans.get_message(M_SENT_CHAR_DELETE)
                context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
                enqueue_command(cmd)
            else:
                del deletion_process[update.effective_chat.id]
                msg = trans.get_message(M_CANCEL_REQUEST)
                context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
                start(update, context)
    elif update.effective_chat.id in feedback_process.keys():
        if len(update["message"]["text"]) <= MAX_FEEDBACK_LENGTH:
            del feedback_process[update.effective_chat.id]
            cmd = {"user_id": update.effective_chat.id, "cmd_type": CMD_FEEDBACK, "locale": trans.code,
                   "message": update["message"]["text"], "user_name": update.effective_chat.username}
            msg = trans.get_message(M_FEEDBACK_SENT)
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
            enqueue_command(cmd)
        else:
            msg = trans.get_message(M_FEEDBACK_TOO_LONG).format(MAX_FEEDBACK_LENGTH)
            reply_markup = InlineKeyboardMarkup(main_keyboard(None, trans))
            context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=reply_markup)

    else:
        telegram_logger.info("User {0} sent message {1}".format(update.effective_chat.id, update.message.text))


def class_list_callback(ch, method, properties, body):
    global class_list
    global translations
    buf = json.loads(body).get("class_list")
    class_list = []
    for i in buf:
        class_list.append(i)
        for j in buf[i]:
            if j in translations.keys():
                translations[j].add_message(i, buf[i][j])


def dict_response_callback(ch, method, properties, body):
    global queue_logger
    global feedback_reading
    queue_logger.info("Received server command " + str(body) + ", started callback")
    msg = json.loads(body)
    cmd_type = msg.get("cmd_type")
    chat_id = msg.get("user_id")
    trans = get_locale(None, chat_id)
    if cmd_type == CMD_SET_CLASS_LIST:
        class_list_callback(ch, method, properties, body)
    elif cmd_type == CMD_SET_SERVER_STATS:
        reply_markup = InlineKeyboardMarkup(admin_keyboard(trans))
        updater.dispatcher.bot.send_message(chat_id=chat_id, text=msg.get("server_info"), reply_markup=reply_markup)
    elif cmd_type == CMD_SERVER_OK:
        reply_markup = InlineKeyboardMarkup(admin_keyboard(trans))
        updater.dispatcher.bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup)
    elif cmd_type == CMD_SENT_FEEDBACK:
        reply_markup = InlineKeyboardMarkup(read_keyboard(trans))
        feedback_reading[chat_id] = msg.get("message_id")
        updater.dispatcher.bot.send_message(chat_id=chat_id,
                                            text="sent by id: {0}, nick: {1} message: {2}, message_id: {3}".
                                            format(msg.get("user_sent_id"), msg.get("user_sent_nick"),
                                                   msg.get("message"), msg.get("message_id")),
                                            reply_markup=reply_markup)
    else:
        if chat_id is not None:
            updater.dispatcher.bot.send_message(chat_id=chat_id, text="Unknown message".format(msg))
        queue_logger.error("Received unknown server command " + str(body) + ", started callback")


def cmd_response_callback(ch, method, properties, body):
    global creation_process
    global deletion_process
    global updater
    global queue_logger
    queue_logger.info("Received command " + str(body) + ", started callback")
    msg = json.loads(body)
    chat_id = msg.get("user_id")
    trans = get_locale(None, chat_id)
    reply_markup = InlineKeyboardMarkup(main_keyboard(chat_id, trans))
    if chat_id is not None:
        if msg.get("cmd_type") == CMD_GET_CHARACTER_STATUS:
            updater.dispatcher.bot.send_message(chat_id=chat_id, text=msg.get("char_info"), reply_markup=reply_markup)
        else:
            updater.dispatcher.bot.send_message(chat_id=chat_id, text=msg.get("message"), reply_markup=reply_markup)
            queue_logger.info("Sent message {0}, received from server to user {1}".format(msg.get("message"), chat_id))
        # clear current operations state, if any
        if chat_id in creation_process.keys():
            del creation_process[chat_id]
        if chat_id in deletion_process.keys():
            del deletion_process[chat_id]


def get_mq_connect(mq_config):
    if mq_config.queue_password is None:
        return pika.BlockingConnection(pika.ConnectionParameters(host=mq_config.queue_host, port=mq_config.queue_port))
    else:
        return pika.BlockingConnection(pika.ConnectionParameters(host=mq_config.queue_host, port=mq_config.queue_port,
                                                                 credentials=pika.credentials.PlainCredentials(
                                                                     mq_config.queue_user, mq_config.queue_password)))


def main():
    global class_list
    global creation_process
    global deletion_process
    global feedback_process
    global feedback_reading
    global characters
    global out_channel
    global updater
    global queue_logger
    global telegram_logger
    global config
    global is_shutdown
    global user_locales
    global translations
    global startup_time
    global user_settings

    is_shutdown = False
    class_list = None
    creation_process = {}
    deletion_process = {}
    feedback_process = {}
    feedback_reading = {}
    characters = {}
    user_locales = {}
    translations = {}
    startup_time = datetime.datetime.now().replace(microsecond=0)

    parser = argparse.ArgumentParser(description='Idle RPG telegram bot.')
    parser.add_argument("--config", '-cfg', help="Path to config file", action="store", default="cfg//main.json")
    parser.add_argument("--test_users", help="Number of test users of each class created", action="store", default=None)
    parser.add_argument("--delay", help="Number of test users of each class created", action="store", default=None)
    parser.add_argument("--db", help="Path to the user settings storage", action="store", default="user_settings.db")
    args = parser.parse_args()
    if args.delay is not None:
        time.sleep(int(args.delay))
    config = Config(args.config)

    logger = get_logger(LOG_MAIN, config.log_level)
    queue_logger = get_logger(LOG_QUEUE, config.log_level)
    telegram_logger = get_logger(LOG_TELEGRAM, config.log_level)
    # set_basic_logging(config.log_level)

    user_settings = Persist(config)
    user_locales = user_settings.get_all()

    for dirpath, dirnames, filenames in os.walk("l18n"):
        for lang_file in filenames:
            logger.info("Start process localization file {0}".format(lang_file))
            translations[lang_file[:2]] = L18n()
            translations[lang_file[:2]].set_locale(lang_file[:-4])
            logger.info("Finish process localization file {0}".format(filenames))

    updater = Updater(token=config.secret, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    create_handler = CommandHandler('create', create)
    # TODO: make patterns with regexp
    class_menu_handler = CallbackQueryHandler(class_menu, pattern="class_")
    main_menu_handler = CallbackQueryHandler(main_menu, pattern="main_")
    admin_menu_handler = CallbackQueryHandler(admin_menu, pattern="admin_")
    shutdown_menu_handler = CallbackQueryHandler(shutdown_menu, pattern="shutdown_")
    locale_menu_handler = CallbackQueryHandler(set_locale, pattern="LOCALE_")
    read_menu_handler = CallbackQueryHandler(read_menu, pattern="confirm_")
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(create_handler)
    dispatcher.add_handler(main_menu_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(class_menu_handler)
    dispatcher.add_handler(admin_menu_handler)
    dispatcher.add_handler(shutdown_menu_handler)
    dispatcher.add_handler(locale_menu_handler)
    dispatcher.add_handler(read_menu_handler)

    out_queue = get_mq_connect(config)
    out_channel = out_queue.channel()
    out_channel.queue_declare(queue=QUEUE_NAME_INIT)
    out_channel.queue_declare(queue=QUEUE_NAME_CMD, durable=True)
    out_channel.queue_declare(queue=QUEUE_NAME_RESPONSES, durable=True)
    out_channel.queue_declare(queue=QUEUE_NAME_DICT, durable=True)

    msg = {"cmd_type": CMD_GET_CLASS_LIST}
    out_channel.basic_publish(exchange="", routing_key=QUEUE_NAME_INIT, body=json.dumps(msg),
                              properties=pika.BasicProperties(content_type="application/json",
                                                              content_encoding="UTF-8",
                                                              app_id=QUEUE_APP_ID))

    logger.info("Asked server for class list")

    out_channel.basic_consume(queue=QUEUE_NAME_DICT, on_message_callback=dict_response_callback, auto_ack=True)

    for method_frame, properties, body in out_channel.consume(QUEUE_NAME_DICT, inactivity_timeout=1):
        if class_list is not None:
            break
    out_channel.cancel()
    logger.info("Class list received")

    if args.test_users is not None:
        test_start_time = datetime.datetime.now()
        cnt_users = 0
        logger.info("Started create test users")
        for i in range(int(args.test_users)):
            for j in class_list:
                cmd = {"cmd_type": CMD_CREATE_CHARACTER, "name": j + '_' + str(i + 1), "class": j, "locale": "en"}
                cnt_users += 1
                enqueue_command(cmd)
        test_finish_time = datetime.datetime.now()
        logger.info("Finish create test users, was created {}. Started at {}, finish at {}".format(cnt_users,
                                                                                                   test_start_time,
                                                                                                   test_finish_time))

    updater.start_polling()

    logger.info("Start listen server responses")
    while True:
        try:
            for method_frame, properties, body in out_channel.consume(QUEUE_NAME_RESPONSES, inactivity_timeout=5,
                                                                      auto_ack=False):
                if body is not None:
                    logger.info("Received user message {0} with delivery_tag {1}".format(body,
                                                                                         method_frame.delivery_tag))
                    cmd_response_callback(None, method_frame, properties, body)
                    out_channel.basic_ack(method_frame.delivery_tag)
                    logger.info("Received user message " + str(body) + " with delivery_tag " +
                                str(method_frame.delivery_tag) + " acknowledged")
                else:
                    logger.info("No more messages in {0}".format(QUEUE_NAME_RESPONSES))
                    out_channel.cancel()
                    break
            for method_frame, properties, body in out_channel.consume(QUEUE_NAME_DICT, inactivity_timeout=5,
                                                                      auto_ack=False):
                if body is not None:
                    logger.info("Received server message {0} with delivery_tag {1}".format(body,
                                                                                           method_frame.delivery_tag))
                    dict_response_callback(None, method_frame, properties, body)
                    out_channel.basic_ack(method_frame.delivery_tag)
                    logger.info("Received server message " + str(body) + " with delivery_tag " +
                                str(method_frame.delivery_tag) + " acknowledged")
                else:
                    logger.info("No more messages in {0}".format(QUEUE_NAME_DICT))
                    out_channel.cancel()
                    break
        except pika.exceptions.AMQPError as exc:
            logger.critical("Error {0} when consume in queue, reconnect.".format(exc))
            out_queue = get_mq_connect(config)
            out_channel = out_queue.channel()
        # should be in QUEUE_NAME_DICT listener, but to make things easier put it here
        if is_shutdown:
            updater.stop()
            sys.exit(0)


if __name__ == '__main__':
    main()
