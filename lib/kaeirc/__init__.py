
"""
Internet Relay Chat Library

This module contains classes, interfaces, and functions to create IRC clients.

The descriptions for the exported symbols in this module are intentionally
simple. If you need more information, it's recommended to look at RFCs 2811,
2812, and 2813.

Constants:

CHANNEL_PREFIXES
  This is a convenience string designating which characters are valid as the
  first character of a channel name. Useful to check if the target of an
  operation is a channel or an user. The order of the characters is also useful
  in case you want to sort a list of channels.
"""

import sys
import socket
import collections
import re
import time
import random

import kaeirc.aliases
import kaeirc.util

#=============================================================================

__version__ = "0.1.2"

CHANNEL_PREFIXES = "#&+!"

#=============================================================================

_USER_RE = re.compile(r':([^!]+)!([^@]+)@(.+)')

#=============================================================================

def is_valid_nickname(name):
    """Returns whether NAME is a valid nickname, that is, it contains only
    letters, numbers, '_', '[', ']', '{', '}', '\', '|', '`', or '^'.
    """
    return (re.find(r'[^A-Za-z0-9_\[\]\{\}\\\|\`\^]', name) == -1)

#=============================================================================

def is_valid_channel(name):
    """Returns whether NAME is a valid channel name, that is, it starts with
    any of '#', '&', '+', or '!', and does not contain NUL, BEL, CR, LF, ' ',
    ',', or ':'.
    """
    return (
      (name[0] in CHANNEL_PREFIXES)
      and (re.find('[\0\7\r\n ,:]', name) == -1)
    )

#=============================================================================

def parse_prefix(user):
    """Parses a "nickname!username@host" prefix.

    Returns a 4-tuple, `(nickname, username, host, user)'. If `username' or
    `host' is not specified, it's returned as None.
    """
    # TODO: This does not match docs.
    m = _USER_RE.match(user)
    if m:
        nick, username, host = m.group(1, 2, 3)
        return (nick, username, host, user)
    else:
        return (None, None, None, user)

#=============================================================================

def nick_equals(n1, n2):
    """Compare two nicknames for equality.

    Comparison is done as defined by the IRC protocol. See
    `kaeirc.util.strlower()' for details.
    """
    return (kaeirc.util.strlower(n1) == kaeirc.util.strlower(n2))

#=============================================================================

class Error(Exception):
    """Base exception class for other exceptions defined here."""
    pass

#=============================================================================

class ConnectionError(Error):
    """Exception raised in case of errors while connecting."""
    pass

#=============================================================================

class NickInfo(object):
    """Holds the real nickname of an user and it's mode."""

    @property
    def nickname(self):
        """Real nickname as specified by the user."""
        return self._nickname

    @property
    def mode(self):
        """Mode of this user as a string."""
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode

    def __init__(self, nickname, mode=""):
        """Create a new `NickInfo' instance with the given name and mode."""
        self._nickname = nickname
        self._mode = mode

#=============================================================================

class Channel(object):
    """Holds the name of a channel and the list of users in that channel."""

    @property
    def name(self):
        """Name of this channel."""
        return self._name

    @property
    def nicknames(self):
        """Mapping from lower-cased nicknames to `NickInfo' objects."""
        return self._nicknames

    def __init__(self, name):
        """Create a new `Channel' instance with the given name and an empty
        user list.
        """
        self._name = name
        self._nicknames = kaeirc.util.casedict()

#=============================================================================

class Client(object):
    """This class represents a connection to an IRC network.

    The client is not connected automatically; it's connect method should be
    used for this purpose.

    The application must call the `poll()' method regularly in the main loop,
    until the `connected' attribute is false. That method is responsible for
    reading from the socket (if data is available) and dispatch calls to the
    registered listeners.
    """

    @property
    def username(self):
        """User name as passed to constructor."""
        return self._username

    @property
    def nickname(self):
        """Current nickname in use. Updated when the client receives the
        `RPL_WELCOME' reply or a `NICK' command for this client.

        This property is None if `authed' is false.
        """
        return self._nickname

    @property
    def realname(self):
        """Real name as passed to constructor."""
        return self._realname

    @property
    def address(self):
        """Address this client is connected to, as passed to the
        constructor.
        """
        return self._address

    @property
    def channels(self):
        """List of channels currently joined.

        This is a dictionary mapping channel names to `Channel' instances.
        """
        return self._channels

    @property
    def listeners(self):
        """List of registered listeners called when an event occurs."""
        return self._listeners

    @property
    def connected(self):
        """Boolean telling whether this client is still connected to the
        network. Set by `connect()' and unset by `disconnect()'.
        """
        return self._connected

    @property
    def authed(self):
        """Boolean telling whether this client authenticated successfully to
        the server. Set to true when the `RPL_WELCOME' (001) reply is received
        at the start of the connection, and unset by `disconnect()'.
        """
        return self._authed

    @property
    def socket(self):
        """Underlying socket object used for communication."""
        return self._socket

    @property
    def file(self):
        """Underlying file object used to read/write to the socket. Created in
        connect() by calling `self.socket.makefile()'.
        """
        return self._file

    @property
    def encoding(self):
        """Encoding used for conversion to/from unicode."""
        return self._encoding

    def __init__(self, username, address, nickname=None, realname=None,
      encoding="utf-8"):
        """Create a new `kaeirc.Client' using the specified username and
        address.

        The `username' and `realname' parameters are passed in the initial
        `USER' command. If not specified, or None, `realname' defaults to
        `username'.

        `address' must be a 2-tuple, with the first item being the host name (a
        string) and the second item the port number (an integer).

        `nickname' is passed in the initial `NICK' command. If this nickname is
        already in use, the listeners will be called to handle that, and if
        none handles it, the client will try by modifying a random character.
        This will be tried up to three times, and if still not available, an
        exception is raised. If not specified, or None, `nickname' defaults to
        `username'.
        """
        self._username = username
        self._nickname = nickname or username
        self._realname = realname or username
        self._encoding = encoding
        self._address = address
        self._channels = kaeirc.util.casedict()
        self._listeners = [ ]
        self._socket = None
        self._file = None
        self._connected = False
        self._quitting = False
        self._authed = False
        self._send_queue = [ ]

    def add_listener(self, listener):
        """Adds an object to the list of listeners for the instance.

        See the description about `on_received()' for more information about
        listeners.
        """
        if not listener in self.listeners:
            self.listeners.append(listener)

    def remove_listener(self, listener):
        """Removes an object from the list of listeners, so it won't receive
        more events.
        """
        if listener in self.listeners:
            self.listeners.remove(listener)

    def connect(self, timeout=10):
        """Establish connection to the IRC server.

        This method first connects the socket to the address specified in the
        constructor, and sends the required `USER' and `NICK' commands to
        initiate the IRC connection.

        `timeout' is the time in seconds (fractions allowed) to wait for the
        server to respond. If the timeout expires, `TimeoutError' is raised.

        This method may also raise `socket.error' for other errors.
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("", 0))
        self.socket.connect(self.address)
        self._connected = True
        self._file = self.socket.makefile()
        self.send("CAP REQ multi-prefix")
        self.send("CAP END")
        self.nick(self._nickname)
        self.send("USER %s 0 * :%s" % (self.username, self.realname))
        self.socket.setblocking(0)
        st = time.clock()
        while not self.authed:
            time.sleep(0.1)
            self.poll()
            t = time.clock() - st
            if t >= timeout:
                raise ConnectionError("Timed out")
        for (chan, v) in self.channels:
            self.join(chan)

    def disconnect(self, reason=None):
        """Sends a `QUIT' command to the server, optionally with a reason
        message, and closes the underlying socket.

        This function also sets the `connected' attribute to false.

        Operations on a disconnected client may raise exceptions.
        """
        self._send("QUIT" if reason is None else ("QUIT :%s" % reason))
        self._connected = False
        self._quitting = True

    def quit(self, reason=None):
        """Alias for `disconnect()'."""
        self.disconnect(reason)

    def poll(self):
        """Poll the connection for incoming data.

        This method looks if there's data pending to be read from the socket,
        and if so, calls `on_received()' with the text received.
        """
        while self.connected:
            try:
                text = self.file.readline()
            except socket.error:
                break
            else:
                try:
                    text = unicode(text, self.encoding).rstrip("\n\r")
                except ValueError:
                    text = unicode(text, 'cp1252').rstrip("\n\r")
                self.on_received(text)
        while self._send_queue:
            text = self._send_queue[0]
            del self._send_queue[0]
            self._send(text)
        if self._quitting:
            if self.socket:
                self.socket.close()
            self._file = None
            self._socket = None
            self._authed = False
            self._send_queue = False

    def _send(self, text):
        self.try_call("on_raw_send", None, [ text ])
        self.file.write(text + "\r\n")
        self.file.flush()

    def send(self, text):
        """Sends raw text to the underlying socket, and flushes it."""
        text = text.encode(self.encoding)
        self._send_queue.append(text)

    def nick(self, nickname):
        """Issue a `NICK' command.

        This command requests a nickname change from the server.
        If the request is honored, the server sends back a `NICK' command. If
        it's not possible, the server may send `ERR_NICKNAMEINUSE' or another
        error.
        """
        self.send("NICK %s" % nickname)

    def join(self, channel):
        """Issue a `JOIN' command.

        The server responds either with `JOIN', or an error.
        """
        self.send("JOIN %s" % channel)

    def part(self, channel, reason=None):
        """Issue a `PART' command, optionally with a reason.

        The server responds either with `PART', or an error.
        """
        if reason is None:
            self.send("PART %s" % channel)
        else:
            self.send("PART %s :%s" % (channel, reason))

    def privmsg(self, target, text):
        """Issue a `PRIVMSG' command.

        This tells the server to send `text' as a message to `target'.

        `target' may be either a channel name, or a nickname.
        """
        for line in text.splitlines():
            self.send("PRIVMSG %s :%s" % (target, line))

    def privmsg_ctcp(self, target, text):
        """Issue a `PRIVMSG' command using Client To Client Protocol.

        This tells the server to send `text' as a message to `target',
        surrounded by '\\1' characters.

        `text' should start with a widely recognized "CTCP Query", but may be
        an arbitrary string. Common "queries" include:

          ACTION <action>
            Say <action> as if you were performing it. For example, "ACTION
            likes Python" is usually displayed as "* foo likes Python".
          VERSION
            Request client version information. There's no standard syntax for
            VERSION replies. Clients usually reply with a notice containing
            "VERSION <version>", where <version> is the client version, or
            simply ignore the request. This should only be used if `target'
            refers to a nickname.

        `target' may be either a channel name, or a nickname.
        """
        for line in text.splitlines():
            self.send("PRIVMSG %s :\1%s\1" % (target, line))

    def notice(self, target, text):
        """Issue a `NOTICE' command.

        The `NOTICE' command is almost the same as the `PRIVMSG' command,
        except that clients should *NOT* respond to notices.
        """
        for line in text.splitlines():
            self.send("NOTICE %s :%s" % (target, line))

    def notice_ctcp(self, target, text):
        """Issue a `NOTICE' command using Client To Client Protocol.

        The `NOTICE' command is almost the same as the `PRIVMSG' command,
        except that clients should *NOT* respond to notices.

        This should be used to reply to a CTCP query.
        """
        for line in text.splitlines():
            self.send("NOTICE %s :\1%s\1" % (target, line))

    def whois(self, nickname):
        """Issue a `WHOIS' command."""
        self.send("WHOIS %s" % nickname)

    def topic(self, channel, newtopic=None):
        """Issue a `TOPIC' command, optionally with a new topic.

        If `newtopic' is specified, and is not None, the topic for the
        specified channel is changed to `newtopic'.

        If `newtopic' is not specified, or None, the topic for the specified
        channel is sent by the server via a `RPL_TOPIC' message.
        """
        if newtopic is None:
            self.send("TOPIC %s" % channel)
        else:
            self.send("TOPIC %s :%s" % (channel, newtopic))

    def kick(self, channel, nickname, reason=None):
        """Issue a `KICK' command, optionally with a reason.

        This requests the server to "kick" (forced part) a nickname from a
        channel. You must have channel operator privileges for this to work.
        """
        if reason is None:
            reason = nickname
        self.send("KICK %s %s :%s" % (channel, nickname, reason))

    def mode(self, channel, mode, arg1=None, arg2=None):
        """Issue a `MODE' command.

        The `MODE' command is relatively complex. Please refer to the IRC RFCs
        for more information.
        """
        text = "MODE %s %s" % (channel, mode)
        if arg1: text += " " + arg1
        if arg2: text += " " + arg2
        self.send(text)

    def away(self, reason=None):
        """Issue an `AWAY' command.

        If `reason' is specified and not None, this tells the server that you
        are "away from keyboard" with the given reason. If not specified or
        None, tells the server that you are "back".
        """
        if reason is not None: reason = " :" + reason
        self.send("AWAY%s" % reason)

    def try_call(self, fn, who, args):
        """Call a function in the registered listeners.

        This iterates over the registered listeners, and for each that exports
        a method named `fn', it calls this method with the `who' and unpacked
        `args' arguments.

        This method is intended for internal use, but may be useful in
        specialized cases.
        """
        for l in self.listeners:
            f = None
            if hasattr(l, fn):
                f = getattr(l, fn)
            elif hasattr(l, "_"+fn):
                f = getattr(l, "_"+fn)
            if f:
                r = f(who, *args)
                if r is not None:
                    return r
            if not self.connected:
                break

    def on_received(self, text):
        """Handle a received command, reply, or error, and dispatch method
        calls to relevant listener methods. This is the workhorse of the
        `Client' class.

        IRC commands are either named commands (such as `NICK'), or numeric
        replies (001-399) or errors (400-999).

        When some data is received (typically by `poll()'), this function is
        called to parse the line into the "prefix", the "command", and the
        "arguments".

        If the line begins with a colon (':'), it's parsed as the prefix. The
        prefix specifies the entity (server or user) sending the command. The
        prefix has the format ":nickname!username@host", with "!username" and
        "@host" being optional. Items not specified are taken as None. If no
        prefix is found, a 3-tuple of None is used. The prefix is passed to the
        handler (see below) as the `who' argument.

        The second word in the line (first if there's no prefix), the lowercase
        version is used as command. If there's an alias for the command in
        `kaeirc.aliases.command_aliases', the command is replaced by this
        alias. In any case, the command, with the prefix "on_" added, is the
        "handler".

        This method calls the `try_call()' method, passing the "handler" as the
        `fn' argument, the prefix as the `who' argument, and the rest of the
        words as the `args' argument.
        """
        self.try_call("on_raw_recv", None, [ text ])
        args = text.split(" ")
        who = (None, None, None, None)
        if (len(args[0]) > 0) and (args[0][0] == ':'):
            who = parse_prefix(args[0])
            args = args[1:]
        cmd, args = args[0], args[1:]
        newargs = [ ]
        last = None
        for a in args:
            if (last is None) and (len(a) > 0) and (a[0] == ':'):
                last = [ ]
                a = a[1:]
            if last is not None:
                last.append(a)
            else:
                newargs.append(a)
        if last is not None:
            newargs.append(" ".join(last))
        args = newargs
        if cmd in kaeirc.aliases.command_aliases:
            cmd = kaeirc.aliases.command_aliases[cmd]
        cmd = cmd.lower()
        r = self.try_call("before_" + cmd, who, args)
        if r is not None:
            return r
        fn = "on_" + cmd
        f = None
        if hasattr(self, fn):
            f = getattr(self, fn)
        elif hasattr(self, "_"+fn):
            f = getattr(self, "_"+fn)
        if f:
            f(who, *args)
        self.try_call(fn, who, args)

    def _on_rpl_welcome(self, who, nickname, message):
        self._nickname = nickname
        self._authed = True

    def _on_nick(self, who, nickname):
        if nick_equals(who[0], self.nickname):
            self._nickname = nickname
        for name in self.channels:
            chan = self.channels[name]
            if who[0] in chan.nicknames:
                old = chan.nicknames[who[0]]
                del chan.nicknames[who[0]]
                chan.nicknames[who[0]] = old

    def _on_join(self, who, channel):
        if nick_equals(who[0], self.nickname):
            if not channel in self.channels:
                self.channels[channel] = Channel(channel)
                self.channels[channel].nicknames[self.nickname] = \
                  NickInfo(self.nickname, "")
        else:
            self.channels[channel].nicknames[who[0]] = NickInfo(who[0], "")

    def _on_part(self, who, channel, reason):
        if nick_equals(who[0], self.nickname):
            if channel in self.channels:
                del self.channels[channel]
        else:
            del self.channels[channel].nicknames[who[0]]

    def _on_ping(self, who, reply):
        self.send("PONG :%s" % reply)

    def _on_quit(self, who, reason=None):
        if nick_equals(who[0], self.nickname):
            self.disconnect()
        else:
            for channel in self.channels:
                chan = self.channels[channel]
                if who[0] in chan.nicknames:
                    del chan.nicknames[who[0]]

    def _on_kick(self, who, channel, nickname, reason=None):
        if channel in self.channels:
            if nick_equals(who[0], self.nickname):
                del self.channels[channel]
            else:
                del self.channels[channel].nicknames[nickname]

    def _on_mode(self, who, channel, mode, arg1=None, arg2=None):
        op = True
        chan = self.channels[channel]
        op = (mode[0] == '+')
        c = mode[1]
        if (c == 'o') or (c == 'v'):
            nickname = arg1
            if nickname is not None:
                if not c in chan.nicknames[nickname].mode:
                    if op:
                        chan.nicknames[nickname].mode += c
                    else:
                        chan.nicknames[nickname].mode = \
                          chan.nicknames[nickname].mode.replace(c, '')

    def _on_rpl_namreply(self, who, me, mode, channel, names):
        if channel in self.channels:
            names = names.strip().split(" ")
            for name in names:
                if name:
                    mode = ""
                    if name[0] == '@':
                        mode += 'o'
                        name = name[1:]
                    elif name[0] == '+':
                        mode += 'v'
                        name = name[1:]
                    self.channels[channel].nicknames[name] = \
                      NickInfo(name, mode)

    def _on_err_nicknameinuse(self, who, me, nickname, message):
        if not self.authed:
            x = len(nickname)
            if x >= 8: x = 0
            x -= 1
            nick, c = nickname[:x], nickname[x]
            if c in "12345678":
                c = str(int(c) + 1)
            elif c == '9':
                raise ConnectionError(message)
            else:
                c = '1'
            self.nick(nick + c)

#=============================================================================
