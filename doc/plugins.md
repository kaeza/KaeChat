
# Plugin API

Plugins are loaded from `~/.kaechat/plugins` and `<kaechatroot>/plugins`.
Only Python scripts in source form (`*.py`) are supported at the moment.

Plugins are loaded as if they were modules. Plugin initialization (if needed)
should be done in the main body of the module.

## Events

In order to receive events from the program, you need to define specially named
functions in the main body of the module. These are currently supported events:

Note: each of the functions is called through `kaechatlib.plugins.call_plugins`
in turn in a FIFO manner, and if one returns a value other than None that
function returns this value. Unless otherwise noted, the return value is
unused.

### on_networkframe_create

`on_networkframe_create(frame) -> None`

Called when a new `NetworkFrame` is created. Plugins can add widgets to it if
desired, or add a new listener for IRC commands with
`frame.client.add_listener()`. See `irc.Client` for details.

### on_channelframe_create

`on_channelframe_create(frame) -> None`

Called when a new `ChannelFrame` is created. Plugins can add widgets to it if
desired. Please note that `frame.channel` starts with `(`, it's a "special"
channel (like `(server)`). Such channels don't have user lists. If you need
to know which network this channel is in, use `frame.master`; it's the parent
`NetworkFrame`.

### on_prefswindow_create

`on_prefswindow_create(window) -> None`

Called when the "Preferences" window is created. Can be used by plugins to add
new configuration pages (as pages of `window.notebook`). See `Tix.NoteBook` for
details.

### on_kaechat_quit

`on_kaechat_quit() -> None`

Called when the program is about to quit. Can be used by plugins to stop other
threads, close files, free other resources, etc.

## Chat Commands

Chat commands (invoked as `/name`) are registered with the
`kaechatlib.chat_command` decorator.

The name of the command is derived from the function name. If the name begins
with `_`, that character is stripped, and the rest is used as the name. This is
to allow names like `if`, `else`, etc, to be registered, (you can't name a
function `if` in Python since `if` is a reserved word) or simply to mark the
function as module-private ("importing" plugins from other plugins is not
supported at the moment, but may be implemented in the future if the need
arises).

The documentation string of the function is used as the command documentation.
The first line is used as the "usage" line, and should be of the form
`/name PARAM PARAM ...`. The second line should be blank, and the rest is used
for the long description (shown with `/help name`).

See `plugins/core.py` for an example.
