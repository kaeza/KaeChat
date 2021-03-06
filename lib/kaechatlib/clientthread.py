
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

import kaeirc
import kaeirc.util

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
        """The `kaeirc.Client' instance."""
        return self._client

    def __init__(self, frame):
        """Construct a new `ClientThread' with the given
        `kaechatlib.ui.networkframe.NetworkFrame' instance as target.

        The network configuration is taken from the `frame' object.
        """
        threading.Thread.__init__(self, name="ClientThread")
        self.daemon = True
        self._frame = frame
        net = frame.network
        self._nick_index = 0
        nick = self._get_next_nick()
        username = (net.username or _kc.default_username)
        realname = (net.realname or _kc.default_realname)
        self._client = kaeirc.Client(username, frame.network.address,
          nickname=nick, realname=realname)
        self._client.add_listener(self)

    def run(self):
        """Main body of the thread. Called by the `start()' method."""
        self.frame.echo("Connecting to %s:%d..." % self._frame.network.address,
          channel=_kl.SERVER_CHANNEL, event=_kl.NOTICE_EV)
        try:
            self._client.connect()
        except socket.error as e:
            self._frame.echo("Error connecting: %s" % str(e),
              channel=_kl.SERVER_CHANNEL, event=_kl.NOTICE_EV)
            self._frame.active = False
            return
        if self._frame.network.channels:
            for chan in self._frame.network.channels:
                self._client.join(chan)
        while self._client.connected:
            self._client.poll()
            time.sleep(0.01)

    def stop(self):
        """Tells the thread to stop itself.

        This just calls `disconnect()' on the client instance.
        """
        self._client.disconnect(_kl.FULL_VERSION_STR)

    def _get_next_nick(self):
        nicks = self._frame.network.nicks or _kc.default_nicks
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
            text = "%s (%s@%s) joined %s" % (who[0], who[1], who[2], channel)
        self._frame.echo(text, channel=channel, event=_kl.JOIN_EV)
        self._frame.refresh_userlist(channel)
        if  (not self._frame.cur_channel) \
         or (self._frame.cur_channel[0] == '('):
            self._frame.select_channel(channel)

    def _on_part(self, who, channel, reason=""):
        if who[0] == self._client.nickname:
            text = "You left %s (%s)" % (channel, reason)
        else:
            text = "%s left %s (%s)" % (who[0], channel, reason)
        self._frame.echo(text, channel=channel, event=_kl.PART_EV)
        self._frame.refresh_userlist(channel)

    def _on_privmsg(self, who, channel, text):
        if channel == self._client.nickname:
            channel = who[0]
        hi = False
        l = _nick_re.findall(text)
        if l:
            for word in l:
                if word == self._client.nickname:
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
            self._on_privmsg_ctcp(who, channel, cmd, args)
            return
        if text:
            self._frame.echo(text, who=who[0], channel=channel, prefix=prefix,
                event=event)
            if hi:
                _show_notification("PRIVMSG from %s:" % who[0], text)
                if _kc.highlights_to_chan:
                    if prefix is None:
                        prefix = ""
                    self._frame.echo(text, who=who[0],
                      channel=_kl.HIGHLIGHTS_CHANNEL,
                      prefix=("[%s] %s" % (channel, prefix)),
                      event=_kl.MESSAGE_EV)

    def _on_privmsg_ctcp(self, who, channel, cmd, args):
        self._frame.echo("Received CTCP %s from %s." % (cmd, who[0]))
        reply = None
        fn = "_on_privmsg_ctcp_" + cmd.lower()
        if hasattr(self, fn):
            f = getattr(self, fn)
            reply = f(who, channel, args)
        elif (_kc.config.has_section("ctcp")
          and (cmd.lower() in _kc.config.options("ctcp"))):
            reply = _kc.config.get("ctcp", cmd)
        if reply:
            self._frame.echo("Sent: %s" % reply)
            self._client.notice_ctcp(who[0], "%s %s" % (cmd.upper(), reply))

    def _on_privmsg_ctcp_version(self, who, channel, args):
        return _kl.FULL_VERSION_STR

    def _on_privmsg_ctcp_time(self, who, channel, args):
        return time.strftime("%c", time.localtime())

    def _on_privmsg_ctcp_ping(self, who, channel, args):
        return args

    def _on_notice(self, who, channel, text):
        if text.startswith('\1') and (text[-1] == '\1'):
            text = text[1:-1]
            self._frame.echo("Received CTCP reply from %s: %s" % (who[0], text))
            return
        hi = False
        l = _nick_re.findall(text)
        if l:
            for word in l:
                if word == self.client.nickname:
                    hi = True
                    break
        event = _kl.HIGHLIGHT_EV if hi else _kl.NOTICE_EV
        if _kc.notices_to_chan:
            channel = _kl.NOTICES_CHANNEL
        elif kaeirc.nick_equals(channel, self.client.nickname):
            channel = who[0]
        prefix = None if _kc.notices_to_chan else "[notice] "
        self._frame.echo(text, who=who[0], channel=channel, event=event,
          prefix=prefix)
        if hi:
            _show_notification("NOTICE from %s:" % who[0], text)

    def _on_topic(self, who, channel, newtopic):
        self._frame.echo("%s changed topic to: %s" % (who[0], newtopic),
          channel=channel, event=_kl.TOPIC_CHANGE_EV)
        self._frame.get_channel_frame(channel)._topicvar.set(newtopic)

    def _before_quit(self, who, reason=None):
        if who[0] != self._client.nickname:
            for channel in self._client.channels:
                chan = self._client.channels[channel]
                if who[0] in chan.nicknames:
                    self._frame.echo("%s quit%s" % (who[0],
                      (" (%s)" % reason) if reason is not None else ""),
                      channel=channel, event=_kl.QUIT_EV)

    def _on_quit(self, who, reason=None):
        for name in self._frame._channel_frames:
            f = self._frame._channel_frames[name]
            f.refresh_userlist()

    def _on_kick(self, who, channel, nickname, reason=None):
        if nickname == self._client.nickname:
            text = "You were kicked by %s (%s)" % (who[0], reason or who[0])
        else:
            text = "%s was kicked by %s (%s)" % (nickname, who[0], reason)
            self._frame.refresh_userlist(channel)
        self._frame.echo(text, channel=channel, event=_kl.KICK_EV)

    def _on_nick(self, who, nickname):
        if who[0] == self._client.nickname:
            self._frame.nicklabel.configure(text=nickname)
            text = "You are now known as %s" % nickname
        else:
            text = ("%s is now known as %s" % (who[0], nickname))
        for name in self.frame._channel_frames:
            if not name[0] in kaeirc.CHANNEL_PREFIXES: continue
            ul = self._client.channels[name].nicknames
            if who[0] in ul:
                f = self._frame._channel_frames[name]
                mode = ul[who[0]]
                del ul[who[0]]
                ul[nickname] = mode
                f.refresh_userlist()
                self._frame.echo(text, channel=name, event=_kl.NICK_CHANGE_EV)

    def _on_mode(self, who, channel, mode, arg1=None, arg2=None):
        if channel[0] in kaeirc.CHANNEL_PREFIXES:
            op = True
            chan = self._client.channels[channel]
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
                    self._frame.refresh_userlist(channel)
            elif c == 'v':
                nickname = arg1
                if nickname is not None:
                    if op:
                        text = "%s gives voice status to %s"
                    else:
                        text = "%s removes voice status from %s"
                    text = (text % (who[0], nickname))
                    self._frame.refresh_userlist(channel)
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
            self._frame.echo(text, channel=channel, event=_kl.MODE_CHANGE_EV)

    def _on_rpl_welcome(self, who, nickname, message):
        self._frame._nicklabel.configure(text=nickname)
        self._frame.echo(message, channel=_kl.SERVER_CHANNEL,
          event=_kl.NOTICE_EV)
        # TODO: Implement some kind of `select_network' function.
        # XXX: It's done, need to use it here.
        _kl.mainframe._notebook.raise_page(self._frame._pagename)

    def _on_rpl_topic(self, who, _, channel, topic):
        self._frame.echo("Topic for %s: %s" % (channel, topic),
          channel=channel, event=_kl.TOPIC_CHANGE_EV)
        self._frame.get_channel_frame(channel)._topicvar.set(topic)

    # XXX: `rpl_topicsetby' was added manually and may need changing in the
    #      future.
    def _on_rpl_topicsetby(self, who, _, channel, mask, secs):
        st = time.strftime("%c", time.localtime(int(secs)))
        self._frame.echo("Topic for %s set by %s on %s" % (channel, mask, st),
          channel=channel, event=_kl.TOPIC_CHANGE_EV)

    def _on_rpl_endofnames(self, who, me, channel, message):
        self._frame.refresh_userlist(channel)

    def _on_rpl_whoisuser(self, who, me, nickname, username, host, _, realname):
        self._frame.echo("%s is %s@%s; Real name: %s"
          % (nickname, username, host, realname))

    def _on_rpl_channelmodeis(self, who, me, channel, mode, _):
        self._frame.echo("Mode of %s is: %s" % (channel, mode))

    def _on_rpl_away(self, who, me, nickname, awaymsg):
        self._frame.echo("%s is away: %s" % (nickname, awaymsg),
          channel=nickname, event=_kl.NOTICE_EV)

    def _on_rpl_unaway(self, who, me, message):
        self._frame.echo(message)

    def _on_rpl_nowaway(self, who, me, message):
        self._frame.echo(message)

    def _before_err_nicknameinuse(self, who, me, nickname, message):
        self._frame.echo("%s: %s" % (nickname, message))
        if not self._client.authed:
            nickname = self._get_next_nick()
            self._frame.echo("Trying `%s'..." % nickname)
            self._client.nick(nickname)
            return True

    def _tgt_msg_error(self, who, me, target, message):
        self._frame.echo("%s: %s" % (target, message))

    _on_err_chanoprivsneeded = _tgt_msg_error
    _on_err_nosuchnick = _tgt_msg_error

    def _server_message(self, who, me, message):
        self._frame.echo(message, channel=_kl.SERVER_CHANNEL,
          event=_kl.NOTICE_EV)

    _on_rpl_yourhost = _server_message
    _on_rpl_created = _server_message
    _on_rpl_motdstart = _server_message
    _on_rpl_motd = _server_message
    _on_rpl_endofmotd = _server_message

#=============================================================================
