
import os

from ConfigParser import ConfigParser, Error

config = None
basedir = None

FILENAME = "kaechat.conf"
DEFAULT_FILE = os.path.join(os.getenv("HOME") or ".", ".kaechat", FILENAME)

def update_config():
    global nick_complete_suffix, notices_to_chan, highlights_to_chan, \
           default_username, default_realname, default_nicks, \
           default_quit_message, default_part_message, confirm_quit
    nick_complete_suffix = get("chat", "nick_complete_suffix", ", ")
    notices_to_chan = get_bool("chat", "notices_to_chan", False)
    highlights_to_chan = get_bool("chat", "highlights_to_chan", True)
    default_username = get("networks", "username", "KaeChat")
    default_realname = get("networks", "realname", "KaeChat User")
    default_nicks = get_list("networks", "nicks")
    default_quit_message = get("chat", "default_quit_message")
    default_part_message = get("chat", "default_part_message")
    confirm_quit = get_bool("general", "confirm_quit")

def reload_config(bd):
    global basedir, config
    basedir = bd
    config = ConfigParser()
    config.read(find_configs(FILENAME))
    update_config()

def find_configs(*names):
    l = [ ]
    HOME = os.getenv("HOME") or "."
    _config_dirs = tuple(os.path.abspath(x) for x in (
        basedir,
        os.path.join(basedir, ".."),
        os.path.join(HOME, ".kaechat"),
    ))
    print "_config_dirs: %r" % (_config_dirs,)
    for d in _config_dirs:
        p = os.path.join(d, *names)
        if os.path.exists(p):
            l.append(p)
    return l

def get(section, option, default=None):
    try:
        s = config.get(section, option)
        if not isinstance(s, unicode):
            s = unicode(s, "utf-8")
        return s
    except Error:
        return default

def set(section, option, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, option, unicode(value))

def get_list(section, option, default=None):
    t = get(section, option, None)
    if t is None:
        return ([] if default is None else default)
    else:
        return [ item.strip() for item in t.split(',') ]

def set_list(section, option, value):
    set(section, option, ",".join(value))

def get_bool(section, option, default=False):
    t = get(section, option, None)
    if t is not None:
        try:
            return (int(t) != 0)
        except ValueError:
            x = t.lower()
            if x == "true":
                return True
            elif x == "false":
                return False
    return default

def set_bool(section, option, value):
    t = "true" if value else "false"
    set(section, option, t)

def save():
    with open(DEFAULT_FILE, "wt") as f:
        config.write(f)
