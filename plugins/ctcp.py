
import kaechatlib
import kaeirc

@kaechatlib.chat_command
def _ctcp(frame, cmd, args, args_eol):
    """/ctcp NICKNAME QUERY

    Send a CTCP query.

    QUERY may be an arbitrary string, but some strings are handled specially:

    /ctcp ... ACTION <message>
    This is the same as using `/me <message>'. Use `/help me' for details.

    /ctcp ... VERSION
    Query NICKNAME's client version.

    /ctcp ... TIME
    Query NICKNAME's current time.
    """
    if len(args) < 2:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    elif args[0][0] in kaeirc.CHANNEL_PREFIXES:
        kaechatlib.usage(frame, cmd, "/CTCP may not be used on channels.")
        return
    frame.client.privmsg(args[0], "\1%s\1" % args_eol[1])

@kaechatlib.chat_command
def _nctcp(frame, cmd, args, args_eol):
    """/nctcp NICKNAME MESSAGE

    Send a CTCP notice. This is usually used to reply to a previous CTCP query.
    """
    if len(args) < 2:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    elif args[0][0] in kaeirc.CHANNEL_PREFIXES:
        kaechatlib.usage(frame, cmd, "/NCTCP may not be used on channels.")
        return
    frame.client.notice(args[0], "\1%s\1" % args_eol[1])
