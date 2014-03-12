
"""
Main module for `kaechatlib'.

Public members:

chat_commands
  Mapping from lower-cased command names to 3-tuples, `(callback, usage, doc)'.

networks
  Mapping from lower-cased network IDs to `NetworkConfig' objects.

mainframe
  The main application frame.

root
  The main `Tkinter.Tk' toplevel.

In addition to the members mentioned above, all the members of the
`kaechatlib.locals' module are available here.
"""

import sys
import os
import collections
import random

import Tix

import irc

import kaechatlib.config as _kc
import kaechatlib.plugins as _kp

from kaechatlib.locals import *

#=============================================================================

chat_commands = { }
root = None
mainframe = None
networks = { }

#=============================================================================

_filters = [ ]

#=============================================================================

def usage(frame, cmd, message=None, full=False, prefix="Usage: "):
    cmd = cmd.lower()
    if cmd in chat_commands:
        text = prefix + chat_commands[cmd][1]
        if full:
            text += "\n\n" + chat_commands[cmd][2]
        if message is not None:
            text = message + "\n" + text
        frame.echo(text)

#=============================================================================

def chat_command(callback, name=None, doc=None):
    """Register a new chat command.

    `name' is the name of the new command. If not specified or None, it's
    inferred from `callback.__name__'.

    `doc' is the description of the chat command. The description should be a
    first line describing command usage, optionally followed by a blank line
    and the description of the command. If not specified or None, it's taken
    from `callback.__doc__'.

    The default parameters allows to use this function as a decorator.
    """
    name = name or callback.__name__.lower()
    if name[0] == '_':
        name = name[1:]
    doclines = (doc or callback.__doc__ or "/"+name).splitlines()
    usage = doclines[0]
    if len(doclines) >= 3:
        pfxlen = len(doclines[2]) - len(doclines[2].lstrip())
        d = [ line[pfxlen:] for line in doclines[2:] ]
        doc = "\n".join(d)
    else:
        doc = ""
    chat_commands[name] = (callback, usage, doc)
    return callback

#=============================================================================

def chat_command_alias(newname, oldname):
    """Register a new alias for a command.

    Please note that aliases and commands share the same namespace.
    """
    newname = newname.lower()
    oldname = oldname.lower()
    chat_commands[newname] = (
        chat_commands[oldname][0],
        chat_commands[oldname][1].replace("/"+oldname, "/"+newname, 1),
        "Alias for %s" % oldname,
    )

#=============================================================================

def macro(name, cmdline, params=None, doc=None, minargs=0, maxargs=sys.maxint):
    """Define a macro.

    A macro is a regular chat command that executes another command, optionally
    passing some parameters. It is provided to define simple macros in the
    configuration file or from plugins. It's recommended to define a regular
    chat command in plugins.

    `name' is the name of the macro. Note that this uses the same namespace as
    regular chat commands.

    `cmdline' is the command to run. This is passed to `run_command()', along
    with extra arguments, when the command is invoked.

    `params' specifies the first (usage) line. If None, it's generated.

    `doc' is the description of the command. If None, it's generated.

    The `minargs' and `maxargs' specify the minimum and maximum number of
    required arguments for the macro.
    """
    def _cb(frame, cmd, args, args_eol, cmdline=cmdline, minargs=minargs,
      maxargs=maxargs):
        if len(args) < minargs:
            usage(frame, cmd, "Missing parameter.")
            return
        elif len(args) > maxargs:
            usage(frame, cmd, "Too many parameters.")
            return
        if len(args) > 0:
            text = " " + args_eol[0]
        else:
            text = ""
        return run_command(frame, cmdline + text)
    usage_text = params or ("/%s [ARGS]" % name)
    usage_text += "\n\n" + (doc or "Shortcut for `/%s ...'." % cmdline)
    chat_command(_cb, name, usage_text)

#=============================================================================

def command(frame, name, args, args_eol):
    """Invoke a command by name.

    This is a low level function for invoking a command given it's name and
    arguments.

    `frame' must be an instance of `kaechatlib.ui.NetworkFrame' for the current
    network.

    This is meant for internal use, but may be useful in specialized cases.
    """
    name = name.lower()
    if name in chat_commands:
        return chat_commands[name][0](frame, name, args, args_eol)
    else:
        raise NotImplementedError("Unknown command `%s'" % name)

#=============================================================================

def parse_command(line):
    """Parse a command line.

    This function returns a 3-tuple: `(command, args, args_eol)'. The first
    word in the line is returned as `command'; the rest of the words are
    returned as `args'. `args_eol' is a list of strings. Each item in
    `args_eol' is a string from the beginning of the (N+1)th word (where N is
    the index into the list) to the end of the string.

    For example, passing "cmd a b c" as `line' returns "cmd" as command, the
    list `["a", "b", "c"]' as `args', and the list `["a b c", "b c", "c"]' as
    `args_eol'.

    The return values are suitable for a call to the `command()' function.
    """
    args = [ ]
    args_eol = [ ]
    p = 0
    while p < len(line):
        spc = line.find(' ', p)
        if spc == -1:
            args.append(line[p:])
            args_eol.append(line[p:])
            break
        else:
            args.append(line[p:spc])
            args_eol.append(line[p:])
            p = spc + 1
            while (p < len(line)) and (line[p] == ' '):
                p += 1
    cmd = args[0]
    args, args_eol = args[1:], args_eol[1:]
    return (cmd, args, args_eol)

#=============================================================================

def run_command(frame, line):
    """Parses a line as a chat command and executes the command.

    This is the same as `command(frame, *parse_command(line))'.
    """
    return command(frame, *parse_command(line))

#=============================================================================

def add_message_filter(filter):
    _filters.append(filter)

#=============================================================================

def filter_message(who, channel, message):
    for flt in _filters:
        r = flt(who, channel, message)
        if r is not None:
            message = r
    return message

#=============================================================================

class NetworkConfig(object):
    """Configuration about a network."""

    @property
    def name(self):
        """Display name of this network."""
        return self._name

    @property
    def address(self):
        """Address of this network.

        This is a 2-tuple, `(host, port)'. `host' is the hostname or IP address
        (a string), and `port' is the port number (an integer).
        """
        return self._address

    @property
    def username(self):
        """User name used when connecting to the network."""
        return self._username

    @property
    def realname(self):
        """Real name used when connecting to the network."""
        return self._username

    @property
    def nicks(self):
        """List of nicknames for this network."""
        return self._nicks

    @property
    def autoconnect(self):
        """Boolean specifying if the client should connect to this network at
        startup."""
        return self._autoconnect

    @property
    def channels(self):
        """List of channels to join automatically on connection."""
        return self._channels

    def __init__(self, name, address, username=None, realname=None, nicks=None,
      autoconnect=False, channels=None):
        """Construct a new `NetworkConfig' object with the given parameters."""
        self._name = name
        self._address = address
        self._username = username
        self._realname = realname
        self._nicks = nicks
        self._autoconnect = autoconnect
        self._channels = channels

#=============================================================================

def load_networks():
    """Load the network list.

    This function updates the `networks' mapping with values taken from the
    (in-memory) configuration file.
    """
    cfg = _kc.config
    for sect in cfg.sections():
        if sect.startswith("networks/"):
            netid = sect[9:]
            name = _kc.get(sect, "name", netid)
            address = _kc.get(sect, "address", netid).split('/', 1)
            if len(address) >= 2:
                host, port = address
            else:
                host, port = address[0], 6667
            try:
                port = int(port)
            except ValueError:
                port = 6667
            address = (host, port)
            logname = os.getenv("LOGNAME") or os.getenv("USER") or "KaeChat"
            username = _kc.get(sect, "username")
            realname = _kc.get(sect, "realname")
            nicks = _kc.get_list(sect, "nicks")
            autoconnect = _kc.get_bool(sect, "autoconnect", False)
            channels = _kc.get_list(sect, "channels")
            networks[netid] = NetworkConfig(name, address, username, realname,
              nicks, autoconnect, channels)

#=============================================================================

def save_networks():
    """Save the network list.

    This function stores the `networks' mapping to the (in-memory)
    configuration file.
    """
    for netid in networks:
        sect = "networks/" + netid
        net = networks[netid]
        _kc.set(sect, "name", net.name)
        _kc.set(sect, "address", "%s/%d" % net.address)
        if net.username:
            _kc.set(sect, "username", net.username)
        if net.realname:
            _kc.set(sect, "realname", net.realname)
        if net.nicks:
            _kc.set_list(sect, "nicks", net.nicks)
        _kc.set_bool(sect, "autoconnect", net.autoconnect)
        if net.channels:
            _kc.set_list(sect, "channels", net.channels)
    _kc.save()

#=============================================================================

def connect(netid):
    """Connect to a given network ID.

    Shortcut for `mainframe.connect(netid)'.
    """
    mainframe.connect(netid)

#=============================================================================

def cmp_channels(c1, c2):
    """Compare two channel names.

    Used as `cmp' parameter to `sorted()' to sort the channel list.

    The channels are ordered by their prefix character (in the order specified
    by `irc.CHANNEL_PREFIXES'). "Special channels" (those starting with an open
    parentheses) are put after normal channels, followed by query channels.
    """
    pfx = irc.CHANNEL_PREFIXES + "("
    i1 = pfx.find(c1[0])
    if i1 == -1: i1 = sys.maxint
    i2 = pfx.find(c2[0])
    if i2 == -1: i2 = sys.maxint
    return i1 - i2

#=============================================================================

def random_nick():
    """Generate a random nickname.

    Used when all the selected nicks are unavailable.
    """
    return "KaeChat%06d" % randint(0, 999999)

#=============================================================================

def echo(text):
    """Print a string to the "echo box".

    This is a shortcut for `mainframe.echo(text)'.
    """
    mainframe.echo(text)

#=============================================================================

def main(argv=sys.argv):
    """Run KaeChat."""
    global root, mainframe
    import kaechatlib.ui.mainframe
    _kc.reload_config(os.path.join(os.path.dirname(__file__), "..", ".."))
    root = Tix.Tk()
    mainframe = kaechatlib.ui.mainframe.MainFrame(root)
    mainframe.pack(fill=Tix.BOTH, expand=True)
    load_networks()
    _kp.load_plugins()
    for netid in networks:
        if networks[netid].autoconnect:
            connect(netid)
    root.mainloop()

if __name__ == "__main__":
    main()

#=============================================================================
