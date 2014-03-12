
import fnmatch

import kaechatlib

_ignores = { }

CHAN = 0x1
PRIV = 0x2

ALL = CHAN | PRIV

def _filter_ignores(who, channel, message):
    who = who[3].lower()
    for mask in _ignores:
        if fnmatch.fnmatchcase(who, mask):
            if ((channel == frame.client.nickname) and (_ignores[mask] & PRIV)) \
             or (_ignores[mask] & CHAN):
                return ""

kaechatlib.add_message_filter(_filter_ignores)

@kaechatlib.chat_command
def _ignore(frame, cmd, args, args_eol):
    """/ignore [(HOSTMASK|NICKNAME) [MODE...]]

    Add a hostmask or nickname to your ignore list, or check the ignore list
    if no parameter specified.

    MODE specifies what kind of messages to ignore. Currently supported are:

    /ignore ... CHAN: Ignore messages to channels.
    /ignore ... PRIV: Ignore private messages.

    `/ignore foo ...' is sinonym for `/ignore foo!*@* ...'.
    """
    if len(args) < 1:
        for mask in _ignores:
            t = [ ]
            mode = _ignores[mask]
            if mode & CHAN:
                t.append("CHAN")
            if mode & PRIV:
                t.append("PRIV")
            frame.echo(channel=kaechatlib.NOTICES_CHANNEL)
