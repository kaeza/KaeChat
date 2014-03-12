
if 0:

    from threading import Thread
    from random import random, randint
    import time

    import kaechatlib
    import kaechatlib.config

    import irc

    networks = None
    autoconnect = kaechatlib.config.get_bool("asdfbot", "autoconnect", False)

    _nets = [ x.strip() for x in kaechatlib.config.get("asdfbot", "networks", "").split(";") ]

    print "_nets: %r" % (_nets,)

    if len(_nets[0]):
        networks = [ ]
        for net in _nets:
            cfg = [ x.strip() for x in net.split(" ") ]
            if len(cfg) >= 3:
                nw = (cfg[0], cfg[1], cfg[2:])
                print "nw: %r" % (nw,)
                networks.append(nw)

    class BotThread(Thread):

        def __init__(self, nickname, channels):
            Thread.__init__(self)
            self.client = irc.Client(address=("localhost", 6667),
                username="kaeza", nickname=nickname, realname="asdf")
            self.channels = channels
            self.client.add_listener(self)

        def run(self):
            self.client.connect()
            for chan in self.channels:
                self.client.join(chan)
            while self.client.connected:
                self.client.poll()
                time.sleep(0.1)

        def quit(self):
            self.client.disconnect()

        def on_privmsg(self, who, channel, text):
            source = who[0]
            if channel == self.client.nickname:
                target = who[0]
                prefix = ""
            else:
                nl = self.client.nickname.lower()
                tl = text.lower()
                if tl.startswith(nl) and (len(tl) > len(nl)) and (tl[len(nl)] in ",:"):
                    text = text[len(nl)+1:].lstrip()
                    target = who[0]
                    prefix = ""
                else:
                    return
                target = channel
                prefix = who[0] + ": "
            cmd, args = [ x.strip() for x in text.split(" ", 1) ]
            if not cmd:
                return
            fn = "do_" + cmd.lower()
            if hasattr(self, fn):
                f = getattr(self, fn)
                f(prefix, source, target, args)
            else:
                self.client.privmsg(target, "%sI don't have a command named `%s'." % (prefix, cmd))

        def on_err_nicknameinuse(self, who, *args):
            self.client.nick("asdfbot%03d" % randint(0, 999))

        def on_err_erroneusnickname(self, who, *args):
            self.client.nick("asdfbot%03d" % randint(0, 999))

        def do_hello(prefix, source, target, args):
            self.client.privmsg(target, "Hello, %s!" % source)

    bots = { }

    def _start_bot(netid, nickname, channels):
        bot = BotThread(nickname, channels)
        bots[netid] = bot
        bot.start()

    if networks and autoconnect:
        for (netid, nickname, channels) in networks:
            _start_bot(netid, nickname, channels)

    @kaechatlib.chat_command
    def _bot(frame, cmd, args, args_eol):
        """/bot NET_ID [NICKNAME] CHANNEL...

        Start a bot in network with ID NET_ID.
        NICKNAME defaults to "asdfbot".

        NOTE: Only one bot per network is supported!
        """
        if len(args) < 2:
            kaechatlib.usage(frame, cmd, "Missing parameter.")
            return
        netid = args[0]
        if not netid in kaechatlib.networks:
            frame.echo("/%s: Unknown network ID `%s'." % (cmd, netid))
            return
        elif netid in bots:
            frame.echo("/%s: There's already a bot in network ID `%s'." % (cmd, netid))
            return
        elif netid in bots:
            frame.echo("/%s: There's already a bot in network ID `%s'." % (cmd, netid))
            return
        chans = [ ]
        nickname = None
        for x in args[1:]:
            if x[0] in irc.CHANNEL_PREFIXES:
                if not x in chans:
                    chans.append(x)
            elif not nickname:
                nickname = x
            else:
                kaechatlib.usage(frame, cmd, "Multiple nicknames specified.")
                return
        if len(chans) == 0:
            kaechatlib.usage(frame, cmd, "No channels specified.")
            return
        nickname = nickname or "asdfbot"
        frame.echo("Starting bot in `%s'." % netid)
        _start_bot(netid, nickname, chans)

    @kaechatlib.chat_command
    def _unbot(frame, cmd, args, args_eol):
        """/unbot NET_ID

        Stop bot in network with ID NET_ID.
        """
        if len(args) < 1:
            kaechatlib.usage(frame, cmd, "Missing parameter.")
            return
        netid = args[0]
        if not netid in bots:
            frame.echo("/%s: There's no bot in network ID `%s'." % (cmd, netid))
            return
        self.frame.echo("Stopping bot in `%s'." % netid)
        bots[netid].quit()
        del bots[netid]

    def on_kaechat_quit():
        for netid in bots:
            bots[netid].quit()
