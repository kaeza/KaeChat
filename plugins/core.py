
import time

import kaechatlib
import kaeirc

@kaechatlib.chat_command
def _say(frame, cmd, args, args_eol):
    """/say TEXT

    Send TEXT to the current channel. Useful for macros.
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    frame.echo(args_eol[0], who=frame.client.nickname)
    frame.client.privmsg(frame.cur_channel, args_eol[0])

@kaechatlib.chat_command
def _nick(frame, cmd, args, args_eol):
    """/nick NICKNAME

    Change your nickname to NICKNAME.
    """
    if len(args) == 1:
        frame.client.nick(args[0])
    else:
        kaechatlib.usage(frame, cmd, "Missing nickname.")

@kaechatlib.chat_command
def _join(frame, cmd, args, args_eol):
    """/join CHANNEL

    Join channel CHANNEL.
    """
    if len(args) == 1:
        frame.join_channel(args[0])
    else:
        kaechatlib.usage(frame, cmd, "Missing channel.")

@kaechatlib.chat_command
def _part(frame, cmd, args, args_eol):
    """/part [CHANNEL [REASON]]

    Part channel CHANNEL with reason REASON. If no parameters are specified,
    parts current channel.
    """
    chan = args[0] if len(args) >= 1 else frame.cur_channel
    reason = args_eol[1] if len(args) >= 2 else None
    frame.part_channel(chan, reason)

@kaechatlib.chat_command
def _whois(frame, cmd, args, args_eol):
    """/whois NICKNAME...

    Get information about NICKNAME(s).
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing nickname.")
    else:
        for name in args:
            frame.client.whois(name)

@kaechatlib.chat_command
def _msg(frame, cmd, args, args_eol):
    """/msg (NICKNAME|CHANNEL) MESSAGE

    Send a message to a channel or an user.
    """
    if len(args) >= 2:
        frame.client.privmsg(args[0], args_eol[1])
        frame.echo(args_eol[1], who=frame.client.nickname, channel=args[0],
            event=kaechatlib.MESSAGE_EV)
    else:
        kaechatlib.usage(frame, cmd, "Missing parameter.")

@kaechatlib.chat_command
def _me(frame, cmd, args, args_eol):
    """/me ACTION

    Send a message as if performing an action.
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
    else:
        frame.client.privmsg_ctcp(frame.cur_channel, "ACTION %s" % args_eol[0])
        frame.echo(args_eol[0], who=frame.client.nickname,
          channel=frame.cur_channel, prefix="* ", event=kaechatlib.MESSAGE_EV)

@kaechatlib.chat_command
def _quote(frame, cmd, args, args_eol):
    """/quote TEXT

    Send raw protocol text to the server.
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
    else:
        frame.client.send(args_eol[0])

@kaechatlib.chat_command
def _away(frame, cmd, args, args_eol):
    """/away [REASON]

    If REASON is specified, mark yourself as away with that reason. If REASON
    is not specified, mark yourself as not away.
    """
    msg = args_eol[0] if len(args) >= 1 else ""
    frame.client.away(msg)

@kaechatlib.chat_command
def _back(frame, cmd, args, args_eol):
    """/back

    Mark yourself as not being away. Same as `/away' with no parameter.
    """
    frame.client.away()

class PingHandler:

    def __init__(self, frame):
        self.frame = frame
        self.sent = { }

    def on_notice(self, who, channel, text):
        if text.startswith("\1PING ") and (who[0] in self.sent):
            t = time.clock() - self.sent[who[0]]
            self.frame.echo("Message to %s took %f seconds." % (who[0], t))
            del self.sent[who[0]]

ping_handler = None

@kaechatlib.chat_command
def _ping(frame, cmd, args, args_eol):
    """/ping NICKNAME

    Measure the time it takes for NICKNAME's client to respond back.
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    elif args[0][0] in kaeirc.CHANNEL_PREFIXES:
        kaechatlib.usage(frame, cmd, "/ping cannot be used on channels.")
        return
    global ping_handler
    if ping_handler is None:
        ping_handler = PingHandler(frame)
        frame.client.add_listener(ping_handler)
    ping_handler.sent[args[0]] = time.clock()
    # TODO: Use some other number.
    frame.client.privmsg(args[0], "\1PING 12345678\1")

@kaechatlib.chat_command
def _clear(frame, cmd, args, args_eol):
    """/clear [LINE]

    Clear the scrollback buffer.
    if LINE is zero (the default if not specified), clear everything.
    if LINE is positive, clear from line LINE to the end of the buffer.
    if LINE is negative, clear from the start of the buffer to line LINE.
    """
    if len(args) >= 1:
        try:
            line = int(args[0])
        except ValueError:
            frame.echo("/%s: Line must be an integer." % cmd)
            return
    else:
        line = 0
    frame.clear(frame.cur_channel, line)

@kaechatlib.chat_command
def _recv(frame, cmd, args, args_eol):
    """/recv TEXT

    Make the client handle TEXT as if it was received from the server.
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    frame.client.on_received(args_eol[0])

@kaechatlib.chat_command
def _server(frame, cmd, args, args_eol):
    """/server NET_ID

    Connect to the network whose ID is NET_ID.
    """
    if len(args) < 1:
        kaechatlib.usage(frame, cmd, "Missing parameter.")
        return
    if args[0] in kaechatlib.networks:
        kaechatlib.mainframe.connect(args[0])
    else:
        frame.echo("Unknown network `%s'." % args[0])

@kaechatlib.chat_command
def _quit(frame, cmd, args, args_eol):
    """/quit [REASON]

    Disconnect from the current network, optionally with a reason.
    """
    reason = args_eol[0] if len(args) >= 1 else None
    frame.client.disconnect(reason)

@kaechatlib.chat_command
def _help(frame, cmd, args, args_eol):
    """/help [COMMAND]

    Get help on COMMAND, or a short description of all commands if none
    is specified.
    """
    if len(args) == 1:
        kaechatlib.usage(frame, args[0], full=True)
    else:
        for name in sorted(kaechatlib.chat_commands.keys()):
            kaechatlib.usage(frame, name, prefix="")

kaechatlib.chat_command_alias("m", "msg")
kaechatlib.chat_command_alias("afk", "away")
kaechatlib.chat_command_alias("connect", "server")
kaechatlib.chat_command_alias("discon", "quit")
kaechatlib.chat_command_alias("disconnect", "quit")

kaechatlib.macro("ns", "msg NickServ", params="/ns MESSAGE", minargs=1)
kaechatlib.macro("cs", "msg ChanServ", params="/cs MESSAGE", minargs=1)
kaechatlib.macro("id", "msg NickServ identify",
  params="/id USERNAME PASSWORD", minargs=2)
