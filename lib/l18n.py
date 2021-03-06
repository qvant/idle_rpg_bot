import json
import codecs

DEFAULT_LOCALE = 'english'


# TODO: replace for gettext
class L18n:
    # Class for translation messages to chosen language
    def __init__(self):
        self.locale = ''
        self.code = ''
        self.encoding = None
        self.msg_map = {}
        self.alternative = None

    def set_locale(self, name: str):
        self.locale = name
        self.code = name[:2]
        f = "l18n//" + name + ".lng"
        fp = codecs.open(f, 'r', "utf-8")
        self.msg_map = json.load(fp)
        if self.locale != DEFAULT_LOCALE:
            self.alternative = L18n()
            self.alternative.set_locale(DEFAULT_LOCALE)

    def add_message(self, msg_type: str, msg_text: str):
        self.msg_map[msg_type] = msg_text

    def is_message_exists(self, msg_type: str):
        return msg_type in self.msg_map.keys()

    def get_message(self, msg_type: str):
        if msg_type in self.msg_map.keys():
            msg = self.msg_map[msg_type]
        elif self.locale != DEFAULT_LOCALE:
            msg = self.alternative.get_message(msg_type)
        else:
            raise KeyError("Can't find message {} in locale {} (default locale {})".format(msg_type, self.locale,
                                                                                           DEFAULT_LOCALE))
        if self.encoding is not None:
            msg = str(msg.encode(self.encoding))
        return msg
