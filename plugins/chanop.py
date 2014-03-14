
import kaechatlib
import kaeirc

@kaechatlib.chat_command
def _kick(frame, cmd, args, args_eol):
    """/kick [CHANNEL] NICKNAME [REASON]

    Kick users from the channel.
    """
    if len(args) < 1:
        usage(frame, cmd, "Missing parameter.")
        return
    if args[0][0] in kaeirc.CHANNEL_PREFIXES:
        channel = args[0]
        args = args[1:]
        if len(args) < 1:
            kaechatlib.usage(frame, cmd, "Missing parameter.")
            return
    else:
        channel = frame.cur_channel
    if len(args) >= 2:
        nickname, reason = args[0], args_eol[1]
    else:
        nickname, reason = args[0], args[0]
    frame.client.kick(channel, nickname, reason)

def _set_user_mode(frame, cmd, args, args_eol, mode):
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    if args[0][0] in kaeirc.CHANNEL_PREFIXES:
        channel = args[0]
        nicks = args[1:]
        if len(nicks) < 1:
            usage(frame, cmd, "Missing parameter.")
            return
    else:
        channel = frame.cur_channel
        nicks = args
    for nick in nicks:
        frame.client.mode(channel, mode, nick)

@kaechatlib.chat_command
def _op(frame, cmd, args, args_eol):
    """/op [CHANNEL] NICKNAME...

    Give channel operator status to users on a channel.
    """
    _set_user_mode(frame, cmd, args, args_eol, "+o")

@kaechatlib.chat_command
def _deop(frame, cmd, args, args_eol):
    """/deop [CHANNEL] NICKNAME...

    Remove channel operator status from users on a channel.
    """
    _set_user_mode(frame, cmd, args, args_eol, "-o")

@kaechatlib.chat_command
def _voice(frame, cmd, args, args_eol):
    """/voice [CHANNEL] NICKNAME...

    Give voice status to users on a channel.
    """
    _set_user_mode(frame, cmd, args, args_eol, "+v")

@kaechatlib.chat_command
def _devoice(frame, cmd, args, args_eol):
    """/devoice [CHANNEL] NICKNAME...

    Remove voice status from users on a channel.
    """
    _set_user_mode(frame, cmd, args, args_eol, "-v")

def _set_ban(frame, cmd, args, args_eol, do_set):
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return False
    if args[0][0] in kaeirc.CHANNEL_PREFIXES:
        if len(args) < 2:
            kaechatlib.usage(frame, cmd, "Missing parameter.")
            return False
        channel, mask = args[0:2]
    else:
        channel = frame.cur_channel
        mask = args[0]
    if not (('!' in mask) or ('@' in mask)):
        mask += "!*@*"
    frame.client.mode(channel, "+b" if do_set else "-b", mask)
    return True

@kaechatlib.chat_command
def _ban(frame, cmd, args, args_eol):
    """/ban [CHANNEL] (NICKNAME|MASK)

    Set ban on a nickname!user@host mask.
    """
    _set_ban(frame, cmd, args, args_eol, True)

@kaechatlib.chat_command
def _unban(frame, cmd, args, args_eol):
    """/unban [CHANNEL] (NICKNAME|MASK)

    Unset a ban previously set with /ban.
    """
    _set_ban(frame, cmd, args, args_eol, False)
