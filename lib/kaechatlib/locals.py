
"""
Constants for `kaechatlib'.

It's safe to use `from kaechatlib.locals import *'. These constants are also
available as attributes of `kaechatlib'.

Public members:

NAME
  Name of this program ("KaeChat").

VERSION
  Version as a 3-tuple, `(major, minor, patch)'.

VERSION_STR
  Version as a string, `"<major>.<minor>.<patch>"'.

FULL_VERSION_STR
  Name of program and version and as string.
  Same as `NAME + " " + VERSION_STR'.

HIGHLIGHTS_CHANNEL
SERVER_CHANNEL
NOTICES_CHANNEL
HELP_CHANNEL
ERRORS_CHANNEL
  Names of special channels.

IDLE_EV
NICK_CHANGE_EV
JOIN_EV
PART_EV
QUIT_EV
KICK_EV
MODE_CHANGE_EV
TOPIC_CHANGE_EV
MESSAGE_EV
NOTICE_EV
HIGHLIGHT_EV
  Symbolic constants for the values of the `event' parameter to the `echo()'
  method of `kaechatlib.ui.networkframe.ChannelFrame'.
"""

#=============================================================================

NAME = "KaeChat"
VERSION = (0, 1, 0)
VERSION_STR = "%d.%d.%d" % VERSION
FULL_VERSION_STR = "%s %s" % (NAME, VERSION_STR)

HIGHLIGHTS_CHANNEL = "(highlights)"
SERVER_CHANNEL = "(server)"
NOTICES_CHANNEL = "(notices)"
HELP_CHANNEL = "(help)"
ERRORS_CHANNEL = "(errors)"

IDLE_EV = 0
NICK_CHANGE_EV = 1
JOIN_EV = 2
PART_EV = 3
QUIT_EV = 4
KICK_EV = 5
MODE_CHANGE_EV = 6
TOPIC_CHANGE_EV = 7
MESSAGE_EV = 8
NOTICE_EV = 9
HIGHLIGHT_EV = 10

#=============================================================================
