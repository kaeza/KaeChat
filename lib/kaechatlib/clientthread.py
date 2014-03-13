
"""
Client Thread for KaeChat
"""

import os
import threading
import time
import re
import socket

import kaechatlib as _kl
import kaechatlib.config as _kc

import irc

#=============================================================================

_nick_re = re.compile('[A-Za-z0-9_-\\{}\[\]\^`\|]+')

#=============================================================================

def _show_notification(title, message):
    # TODO: This should be configurable.
    os.spawnlp(os.P_NOWAIT,
      "notify-send", "notify-send", "KaeChat: %s" % title, message)

#=============================================================================

class ClientThread(threading.Thread):
    """Thread handling the IRC connection.

    This thread is responsible for constructing, connecting, and polling the
    IRC client, and dispatching methods to the specified
    `kaechatlib.ui.networkframe.NetworkFrame' as required.
    """

    @property
    def frame(self):
        """Frame acting as target of the method calls."""
        return self._frame

    @property
    def client(self):
        """The `irc.Client' instance."""
        return self._client

    def __init__(self, frame):
        """Construct a new `ClientThread' with the given
        `kaechatlib.ui.networkframe.NetworkFrame' instance as target.

        The network configuration is taken from the `frame' object.
        """
        threading.Thread.__init__(self, name="ClientThread")
        self.daemon = True
        self._frame = frame
        net = frame.net
        self._nick_index = 0
        nick = self._get_next_nick()
        username = (net.username or _kc.default_username)
        realname = (net.realname or _kc.default_realname)
        self._client = irc.Client(username, frame.net.address, nickname=nick,
          realname=realname)
        self._client.add_listener(self)

    def run(self):
        """Main body of the thread. Called by the `start()' method."""
        self.frame.echo("Connecting to %s:%d..." % self.frame.net.address,
          channel=_kl.SERVER_CHANNEL, event=_kl.NOTICE_EV)
        try:
            self.client.connect()
        except socket.error as e:
            self.frame.echo("Error connecting: %s" % str(e),
              channel=_kl.SERVER_CHANNEL, event=_kl.NOTICE_EV)
            self.frame.active = False
            return
        if self.frame.net.channels:
            for chan in self.frame.net.channels:
                self.client.join(chan)
        while self.client.connected:
            self.client.poll()
            time.sleep(0.01)

    def stop(self):
        """Tells the thread to stop itself.

        This just calls `disconnect()' on the client instance.
        """
        self.client.disconnect(_kl.FULL_VERSION_STR)

    def _get_next_nick(self):
        nicks = self.frame.net.nicks or _kc.default_nicks
        if self._nick_index < len(nicks):
            r = nicks[self._nick_index]
            self._nick_index += 1
        else:
            r = _kl.random_nick()
        return r

    def _on_join(self, who, channel):
        if who[0] == self.client.nickname:
            text = "Now talking on %s" % channel
        else:
            text = "%s joined %s" % (who[0], channel)
        self.frame.echo(text, channel=channel, event=_kl.JOIN_EV)
        self.frame.refresh_userlist(channel)
        if  (not self.frame.cur_channel) \
         or (self.frame.cur_channel[0] == '('):
            self.frame.select_channel(channel)

    def _on_part(self, who, channel, reason=""):
        if who[0] == self.client.nickname:
            text = "You left %s (%s)" % (channel, reason)
        else:
            text = "%s left %s (%s)" % (who[0], channel, reason)
        self.frame.echo(text, channel=channel, event=_kl.PART_EV)
        self.frame.refresh_userlist(channel)

    def _on_privmsg(self, who, channel, text):
        if channel == self.client.nickname:
            channel = who[0]
        hi = False
        l = _nick_re.findall(text)
        if l:
            for word in l:
                if word == self.client.nickname:
                    hi = True
                    break
        event = _kl.HIGHLIGHT_EV if hi else _kl.MESSAGE_EV
        text = _kl.filter_message(who, channel, text)
        prefix = None
        if text.startswith('\1ACTION ') and (text[-1] == '\1'):
            text = text[8:-1]
            prefix = "* "
        elif text.startswith('\1') and (text[-1] == '\1'):
            args = text[1:-1].split(' ', 1)
            if len(args) == 2:
                cmd, args = args
            else:
                cmd, args = args[0], ""
            self.on_privmsg_ctcp(who, channel, cmd, args)
            return
        if text:
            self.frame.echo(text, who=who[0], channel=channel, prefix=prefix,
                event=event)
            if hi:
                _show_notification("PRIVMSG from %s:" % who[0], text)
                if _kc.highlights_to_chan:
                    if prefix is None:
                        prefix = ""
                    self.frame.echo(text, who=who[0],
                      channel=_kl.HIGHLIGHTS_CHANNEL,
                      prefix=("[%s] %s" % (channel, prefix)),
                      event=_kl.MESSAGE_EV)

    def _on_privmsg_ctcp(self, who, channel, cmd, args):
        self.frame.echo("Received CTCP %s from %s." % (cmd, who[0]))
        fn = "_on_privmsg_ctcp_" + cmd.lower()
        if hasattr(self, fn):
            f = getattr(self, fn)
            reply = f(who, channel, args)
            self.frame.echo("Sent: %s" % (reply,))
            self.client.notice(who[0], "\1%s\1" % reply)

    def _on_privmsg_ctcp_version(self, who, channel, args):
        return "VERSION %s" % _kl.FULL_VERSION_STR

    def _on_privmsg_ctcp_time(self, who, channel, args):
        return "TIME %s" % time.strftime("%c", time.localtime())

    def _on_privmsg_ctcp_ping(self, who, channel, args):
        return "PING %s" % args

    def _on_notice(self, who, channel, text):
        hi = False
        l = _nick_re.findall(text)
        if l:
            for word in l:
                if word == self.client.nickname:
                    hi = True
                    break
        event = _kl.HIGHLIGHT_EV if hi else _kl.NOTICE_EV
        channel = _kl.NOTICES_CHANNEL if _kc.notices_to_chan else who[0]
        prefix = None if _kc.notices_to_chan else "[notice] "
        self.frame.echo(text, who=who[0], channel=channel, event=event,
          prefix=prefix)
        _show_notification("NOTICE from %s:" % who[0], text)

    def _on_topic(self, who, channel, newtopic):
        self.frame.echo("%s changed topic to: %s" % (who[0], newtopic),
          channel=channel, event=_kl.TOPIC_CHANGE_EV)
        self.frame.get_channel_frame(channel).topicvar.set(newtopic)

    def _before_quit(self, who, reason=None):
        if who[0] != self.client.nickname:
            for channel in self.client.channels:
                chan = self.client.channels[channel]
                if who[0] in chan.nicknames:
                    self.frame.echo("%s quit%s" % (who[0],
                      (" (%s)" % reason) if reason is not None else ""),
                      channel=channel, event=_kl.QUIT_EV)

    def _on_quit(self, who, reason=None):
        for name in self.frame.channel_frames:
            f = self.frame.channel_frames[name]
            f.refresh_userlist()

    def _on_kick(self, who, channel, nickname, reason=None):
        if nickname == self.client.nickname:
            text = "You were kicked by %s (%s)" % (who[0], reason or who[0])
        else:
            text = "%s was kicked by %s (%s)" % (nickname, who[0], reason)
            self.frame.refresh_userlist(channel)
        self.frame.echo(text, channel=channel, event=_kl.KICK_EV)

    def _on_nick(self, who, nickname):
        if who[0] == self.client.nickname:
            self.frame.nicklabel.configure(text=nickname)
            text = "You are now known as %s" % nickname
            self.nickname = nickname
        else:
            text = ("%s is now known as %s" % (who[0], nickname))
        for name in self.frame.channel_frames:
            if name[0] == '(': continue
            ul = self.client.channels[name].nicknames
            if who[0] in ul:
                f = self.frame.channel_frames[name]
                mode = ul[who[0]]
                del ul[who[0]]
                ul[nickname] = mode
                f.refresh_userlist()
                self.frame.echo(text, channel=name, event=_kl.NICK_CHANGE_EV)

    def _on_mode(self, who, channel, mode, arg1=None, arg2=None):
        op = True
        chan = self.client.channels[channel]
        op = (mode[0] == '+')
        c = mode[1]
        text = None
        if c == 'o':
            nickname = arg1
            if nickname is not None:
                if op:
                    text = "%s gives channel operator status to %s"
                else:
                    text = "%s removes channel operator status from %s"
                text = text % (who[0], nickname)
                self.frame.refresh_userlist(channel)
        elif c == 'v':
            nickname = arg1
            if nickname is not None:
                if op:
                    text = "%s gives voice status to %s"
                else:
                    text = "%s removes voice status from %s"
                text = (text % (who[0], nickname))
                self.frame.refresh_userlist(channel)
        elif c == 'q':
            mask = arg1
            if op:
                text = "%s sets quiet status on %s"
            else:
                text = "%s unsets quiet status on %s"
            text = text % (who[0], mask)
        elif c == 'b':
            mask = arg1
            if op:
                text = "%s sets ban on %s"
            else:
                text = "%s unsets ban on %s"
            text = text % (who[0], mask)
        if text is None:
            nickname = arg1
            if nickname is not None:
                text = "%s gives mode %s to %s"
            else:
                text = "%s changes mode %s to %s"
            text = text % (who[0], mode, channel)
        self.frame.echo(text, channel=channel, event=_kl.MODE_CHANGE_EV)

    def _on_rpl_welcome(self, who, nickname, message):
        self.frame.nicklabel.configure(text=nickname)
        self.frame.echo(message, channel=_kl.SERVER_CHANNEL,
          event=_kl.NOTICE_EV)
        # TODO: Implement some kind of `select_network' function.
        _kl.mainframe.notebook.raise_page(self.frame.pagename)

    def _on_rpl_topic(self, who, _, channel, topic):
        self.frame.echo("Topic for %s: %s" % (channel, topic),
          channel=channel, event=_kl.TOPIC_CHANGE_EV)
        self.frame.get_channel_frame(channel).topicvar.set(topic)

    # XXX: `rpl_topicsetby' was added manually and may need changing in the
    #      future.
    def _on_rpl_topicsetby(self, who, _, channel, mask, secs):
        st = time.strftime("%c", time.localtime(int(secs)))
        self.frame.echo("Topic for %s set by %s on %s" % (channel, mask, st),
          channel=channel, event=_kl.TOPIC_CHANGE_EV)

    def _on_rpl_endofnames(self, who, me, channel, message):
        self.frame.refresh_userlist(channel)

    def _on_rpl_whoisuser(self, who, me, nickname, username, host, _, realname):
        self.frame.echo("%s is %s@%s; Real name: %s"
          % (nickname, username, host, realname))

    def _on_rpl_channelmodeis(self, who, me, channel, mode, _):
        self.frame.echo("Mode of %s is: %s" % (channel, mode))

    def _on_rpl_away(self, who, me, nickname, awaymsg):
        self.frame.echo("%s is away: %s" % (nickname, awaymsg),
          channel=nickname, event=_kl.NOTICE_EV)

    def _on_rpl_unaway(self, who, me, message):
        self.frame.echo(message)

    def _on_rpl_nowaway(self, who, me, message):
        self.frame.echo(message)

    def _before_err_nicknameinuse(self, who, me, nickname, message):
        self.frame.echo("%s: %s" % (nickname, message))
        if not self.client.authed:
            nickname = self._get_next_nick()
            self.frame.echo("Trying `%s'..." % nickname)
            self.client.nick(nickname)
            return True

    def _tgt_msg_error(self, who, me, target, message):
        self.frame.echo("%s: %s" % (target, message))

    _on_err_chanoprivsneeded = _tgt_msg_error
    _on_err_nosuchnick = _tgt_msg_error

    def _server_message(self, who, me, message):
        self.frame.echo(message, channel=_kl.SERVER_CHANNEL,
          event=_kl.NOTICE_EV)

    _on_rpl_yourhost = _server_message
    _on_rpl_created = _server_message
    _on_rpl_motdstart = _server_message
    _on_rpl_motd = _server_message
    _on_rpl_endofmotd = _server_message

    def _on_raw_recv(self, who, text):
        print "RECV: %s" % text.rstrip().encode('utf-8')

#=============================================================================
