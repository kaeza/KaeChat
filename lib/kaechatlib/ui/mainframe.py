
import os
import time
import webbrowser

import Tix
import tkMessageBox as _tkmb

import kaeirc
import kaeirc.util

import kaechatlib as _k
import kaechatlib.config as _kc
import kaechatlib.clientthread as _kct
import kaechatlib.plugins as _kp
import kaechatlib.locals as _kl

import kaechatlib.ui as _kui
import kaechatlib.ui.networklist as _kuinl
import kaechatlib.ui.preferences as _kuipf
import kaechatlib.ui.about as _kuiab

#=============================================================================

_event_colors = {
    _k.IDLE_EV: "#000000",
    _k.NICK_CHANGE_EV: "#000080",
    _k.JOIN_EV: "#000080",
    _k.PART_EV: "#000080",
    _k.QUIT_EV: "#000080",
    _k.KICK_EV: "#008080",
    _k.MODE_CHANGE_EV: "#000080",
    _k.TOPIC_CHANGE_EV: "#808000",
    _k.MESSAGE_EV: "#808000",
    _k.NOTICE_EV: "#C0C000",
    _k.HIGHLIGHT_EV: "#0000FF",
}

#=============================================================================

class ChannelFrame(Tix.Frame):
    """Frame containing the channel-related widgets."""

    default_colors = (
        "#000000", "#000080", "#008000", "#008080",
        "#800000", "#800080", "#808000", "#808080",
    )

    @property
    def colors(self):
        """Colors used for colored nicknames."""
        return self._colors

    @colors.setter
    def colors(self, colors):
        self._colors = colors

    @colors.deleter
    def colors(self, colors):
        self._colors = None

    @property
    def frame(self):
        """The parent `NetworkFrame' of this frame."""
        return self._frame

    @property
    def channel(self):
        """The name of the channel."""
        return self._channel

    def __init__(self, frame, channel):
        """Constructs a new `ChannelFrame' instance for the given channel.

        `frame' must be an instance of `MainFrame'.
        """
        Tix.Frame.__init__(self, frame._top_frame)
        self._frame = frame
        self._channel = channel
        self._colors = None
        self._init_widgets()
        self._init_bindings()
        self._event = _k.IDLE_EV

    def reload_config(self):
        """Reload the configuration for this channel."""
        pass

    def echo(self, text, who=None, prefix=None):
        """Print a string to the text box.

        `text' is the text to output.

        `who' is the user who sent the message, or None for informational
        messages.

        `prefix' is the prefix for the text.

        The line echoed is in this format:
          [HH:MM:SS] PREFIX<WHO> TEXT

        WHO is colored based on it's hash value. The colors are taken from the
        `colors' member if it's not None, or from `default_colors'.
        """
        tb = self._textbox
        tb.configure(state=Tix.NORMAL)
        colors = self.colors or self.default_colors
        for line in text.splitlines():
            tb.insert(Tix.END, time.strftime("[%H:%M:%S] "))
            if prefix is not None:
                tb.insert(Tix.END, prefix)
            if who is not None:
                tb.insert(Tix.END, "<%s>" % who,
                  "color_%d" % (hash(who) % len(colors)))
            else:
                tb.insert(Tix.END, "***")
            tb.insert(Tix.END, " ")
            for (part, tag) in self._format_message(line):
                if tag is None:
                    tb.insert(Tix.END, part)
                else:
                    tb.insert(Tix.END, part, tag)
            tb.insert(Tix.END, "\n")
        tb.configure(state=Tix.DISABLED)
        t, b = tb.yview()
        h = b - t
        tb.yview_moveto(1 - h)

    def clear(self, line=0):
        """Clear the text box.

        If `line' is zero (the default), the whole text box is cleared. If it's
        positive, the text from line `line' to the end of the text is cleared.
        If it's negative, the text from line `line' to the beginning of the
        text is cleared.
        """
        tb = self.textbox.text
        tb.configure(state=Tix.NORMAL)
        if line == 0:
            tb.delete("0.0", Tix.END)
        elif line > 0:
            tb.delete("%d.0" % (line + 1), Tix.END)
        else: # line < 0
            lines = tb.get("0.0", Tix.END).splitlines()
            count = len(lines)
            tb.delete("0.0", "%d.0" % (count + -(-line)))
        tb.configure(state=Tix.DISABLED)

    def refresh_userlist(self):
        """Update the user list.

        Should be called when the users for this channel are received, or when
        somebody joins/parts.
        """
        if self._userlist is not None:
            self._userlist.delete(0, Tix.END)
            if self._channel in self._frame.client.channels:
                ops = [ ]
                voices = [ ]
                users = [ ]
                l = self._frame.client.channels[self._channel].nicknames
                for name in l:
                    ni = l[name]
                    mode = l[name].mode
                    if 'o' in mode:
                        ops.append("@" + ni.nickname)
                    elif 'v' in mode:
                        voices.append("+" + ni.nickname)
                    else:
                        users.append(ni.nickname)
                l = (sorted(ops, key=unicode.lower)
                   + sorted(voices, key=unicode.lower)
                   + sorted(users, key=unicode.lower))
                for name in l:
                    self._userlist.insert(Tix.END, name)
                self._userlistlabel.configure(
                  text="%d Users, %d OPs" % (len(l), len(ops)))

    def _init_widgets(self):
        f = Tix.Frame(self)
        f.pack(side=Tix.TOP, fill=Tix.BOTH, expand=True)
        ff = Tix.Frame(f)
        ff.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
        if self._channel[0] in kaeirc.CHANNEL_PREFIXES:
            self._topicvar = Tix.StringVar()
            self._topicbox = Tix.Entry(ff, textvariable=self._topicvar)
            self._topicbox.pack(side=Tix.TOP, fill=Tix.X)
        else:
            self._topicbox = None
        self._textbox_ = Tix.ScrolledText(ff)
        self._textbox_.pack(side=Tix.BOTTOM, fill=Tix.BOTH, expand=True)
        self._textbox = self._textbox_.text
        self._textbox.configure(state=Tix.DISABLED)
        if self._channel[0] in kaeirc.CHANNEL_PREFIXES:
            ff = Tix.Frame(f)
            ff.pack(side=Tix.RIGHT, fill=Tix.BOTH)
            self._userlistlabel = Tix.Label(ff)
            self._userlistlabel.pack(side=Tix.TOP, fill=Tix.X)
            self._userlist_ = Tix.ScrolledListBox(ff)
            self._userlist_.pack(side=Tix.BOTTOM, fill=Tix.BOTH, expand=True)
            self._userlist = self._userlist_.listbox
            self._userlist.configure(selectmode=Tix.BROWSE, bg="white")
            colors = self._colors or self.default_colors
            for i in range(len(colors)):
                c = colors[i]
                self._textbox.tag_configure("color_%d" % i, foreground=c)
            self._textbox.tag_configure(_kui.WEB_LINK_TAG,
              foreground="#0000FF")
            m = Tix.Menu(self._userlist, tearoff=False)
            m.add_command(label="Who is this?", command=self._whois_ul)
            m.add_command(label="Start conversation",
              command=self._start_query_ul)
            self._userlist.menu = m
            _kui.set_colors(self._userlistlabel, "window")
            _kui.set_colors(self._userlist, "user_list")
        else:
            self._userlist = None
        _kui.set_colors(self, "window")
        _kui.set_colors(self._textbox, "textbox")
        _kp.call_plugins("on_channelframe_create", self)

    def _init_bindings(self):
        if self._userlist is not None:
            self._userlist.bind("<Double-Button-1>", self._start_query_ul)
            self._userlist.bind("<Button-3>", self._userlist_rclick)
        if self._topicbox is not None:
            self._topicbox.bind("<Return>", self._set_topic)
        self._textbox.tag_bind(_kui.WEB_LINK_TAG, "<Double-Button-1>",
          self._invoke_url)

    def _userlist_rclick(self, event):
        self._userlist.menu.post(event.x_root, event.y_root)

    def _invoke_url(self, event):
        # TODO: This needs better handling.
        x = event.widget.tag_prevrange(_kui.WEB_LINK_TAG,
          event.widget.index(Tix.CURRENT))
        if x:
            start, end = x
            url = event.widget.get(start, end)
            webbrowser.open(url)

    def _start_query_ul(self, event=None):
        sel = self._userlist.get(Tix.ANCHOR)
        if sel:
            if (sel[0] == '@') or (sel[0] == '+'):
                sel = sel[1:]
            self._frame.select_channel(sel)

    def _whois_ul(self):
        sel = self.userlist.get(Tix.ANCHOR)
        self._frame.client.whois(sel)

    def _set_topic(self, event):
        self._frame.client.topic(self.channel, self.topicvar.get())

    def _format_message(self, line):
        m = _kui.HTTPS_RE.search(line)
        if m:
            yield line[:m.start()], _kui.TEXT_TAG
            yield m.group(), _kui.WEB_LINK_TAG
            yield line[m.end():], _kui.TEXT_TAG
        else:
            yield line, _kui.TEXT_TAG

#=============================================================================

class NetworkFrame(Tix.Frame):

    _event_colors = _event_colors

    @property
    def frame(self):
        """The parent `MainFrame' of this frame."""
        return self._frame

    @property
    def network(self):
        """Instance of `kaechatlib.NetworkConfig' passed to constructor."""
        return self._network

    @property
    def client(self):
        """Instance of `kaeirc.Client' used for communication."""
        return self._thread._client

    @property
    def cur_channel(self):
        """Currently selected channel."""
        return self._cur_channel

    @property
    def active(self):
        """Boolean indicating whether this frame is still active (i.e.
        connected)."""
        return self._active

    def __init__(self, frame=None, pagename=None, network=None, netid=None):
        Tix.Frame.__init__(self, frame)
        self._frame = frame
        self._pagename = pagename
        self._network = network
        self._netid = netid
        self._cur_channel = None
        self._history = [ "" ]
        self._hist_index = 0
        self._active = True
        self._init_widgets()
        self._init_bindings()
        self._thread = _kct.ClientThread(self)
        self._thread.start()

    def reload_config(self):
        """Reload the configuration for this network.

        This also calls `reload_config()' on each channel frame.
        """
        for channel in self.channel_frames:
            self._channel_frames[channel].reload_config()

    def get_channel_frame(self, channel=None, create=True):
        """Returns a `ChannelFrame' instance for the specified channel.

        `create' specifies whether to create a new `ChannelFrame' instance if
        no such instance exists for the given channel.

        Returns the instance for the specified channel if it exists, a new
        one if it doesn't and `create' is true (default), or None if no
        instance exists and `create' is false.
        """
        if channel is None:
            if self._cur_channel is None:
                channel = _k.SERVER_CHANNEL
            else:
                channel = self._cur_channel
        if channel in self._channel_frames:
            f = self._channel_frames[channel]
        elif create:
            f = ChannelFrame(self, channel)
            self._channel_frames[channel] = f
            self.refresh_chanlist()
        else:
            f = self.get_channel_frame(_k.SERVER_CHANNEL)
        if self._cur_channel is None:
            self._cur_channel = channel
            f.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
        return f

    def echo(self, text, who=None, channel=None, prefix="", event=None):
        """Print a string to a channel text box.

        Shortcut for `get_channel_frame(channel).echo(text, ...)'.
        """
        self.get_channel_frame(channel).echo(text, who=who, prefix=prefix)
        if (event is not None) and (channel != self._cur_channel):
            self.set_channel_event(channel, event)

    def clear(self, channel=None, lines=0):
        """Clear a channel text box.

        Roughly equivalent to `get_channel_frame(channel).clear(lines)', except
        that the channel frame is not created if it does not already exist.
        """
        f = self.get_channel_frame(channel, create=False)
        if f:
            f.clear(lines)

    def refresh_userlist(self, channel):
        """Update the user list of a channel.

        Roughly equivalent to `get_channel_frame(channel).refresh_userlist()',
        except that the channel frame is not created if it does not already
        exist.
        """
        f = self.get_channel_frame(channel, create=False)
        if f:
            f.refresh_userlist()

    def refresh_chanlist(self):
        """Update the channel list.

        Should be called whenever the client joins or parts a channel.
        """
        self._chanlist.delete(0, Tix.END)
        for name in sorted(self._channel_frames.keys(), _k.cmp_channels):
            self._chanlist.insert(Tix.END, name)

    def select_channel(self, channel):
        """Select a channel and show it's frame."""
        if not channel in self._channel_frames:
            self.get_channel_frame(channel)
        self._cur_channel = channel
        for name in self._channel_frames:
            f = self._channel_frames[name]
            if name == channel:
                f.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
            else:
                f.forget()
        self.set_channel_event(channel, _k.IDLE_EV, True)
        for i in range(self._chanlist.size()):
            name = self._chanlist.get(i)
            if kaeirc.util.strlower(name) == channel:
                self._chanlist.selection_anchor(i)
        self._chatbox.focus()

    def set_channel_event(self, channel, event, override=False):
        """Sets the current event for the specified channel.

        The event is an integer designating what kind of action happened on
        that channel. This is only used to change the channel name color in the
        channel list.

        Events have a priority equal to it's value. Events are only set if the
        new event is greater than the current one. This is done so e.g.
        somebody joining a channel (`JOIN_EV') does not "obscure" somebody
        sending a message (`MESSAGE_EV').
        """
        if event < _k.IDLE_EV:
            event=_k.IDLE_EV
        elif event > _k.HIGHLIGHT_EV:
            event = _k.HIGHLIGHT_EV
        if (not override) and (self._channel_frames[channel]._event >= event):
            return
        l = self._chanlist.size()
        for x in range(l):
            name = self._chanlist.get(x)
            if name == channel:
                self._chanlist.itemconfigure(x, fg=self._event_colors[event])
                break
        self._channel_frames[channel]._event = event

    def _init_widgets(self):
        self._top_frame = Tix.Frame(self)
        self._top_frame.pack(side=Tix.TOP, fill=Tix.BOTH, expand=True)
        self._chanlist_ = Tix.ScrolledListBox(self._top_frame)
        self._chanlist_.pack(side=Tix.LEFT, fill=Tix.Y)
        self._chanlist = self._chanlist_.listbox
        self._chanlist.configure(selectmode=Tix.BROWSE)
        # XXX: ScrolledListBox sucks in this respect.
        self._chanlist.configure(bg="white")
        self._channel_frames = { }
        f = Tix.Frame(self)
        f.pack(side=Tix.BOTTOM, fill=Tix.X)
        self._nicklabel = Tix.Label(f, text="(unnamed)")
        self._nicklabel.pack(side=Tix.LEFT)
        self._chatvar = Tix.StringVar()
        self._chatbox = Tix.Entry(f, textvariable=self._chatvar)
        self._chatbox.pack(side=Tix.LEFT, fill=Tix.X, expand=True)
        self._chatbox.focus()
        Tix.Button(f, text="Send", command=self._do_send).pack(side=Tix.RIGHT)
        _kui.set_colors(self, "window")
        _kui.set_colors(self._nicklabel, "window")
        _kui.set_colors(self._chatbox, "chatbox")
        _kui.set_colors(self._chanlist, "channel_list")

    def _init_bindings(self):
        self.bind("<Destroy>", self._quit)
        self._chatbox.bind("<Return>", self._do_send)
        self._chatbox.bind("<Up>", self._prev_hist)
        self._chatbox.bind("<Down>", self._next_hist)
        self._chatbox.unbind_all("<Tab>")
        self._chatbox.bind("<Tab>", self._autocomplete)
        self._chanlist.bind("<<ListboxSelect>>", self._sel_chan)

    def _quit(self, event):
        self._thread.stop()

    def _autocomplete(self, event):
        text = self._chatvar.get()
        end = self._chatbox.index(Tix.INSERT)
        start = end - 1
        atstart = False
        while (start >= 0) and (text[start] != ' '):
            start -= 1
        if start <= 0:
            atstart = True
        start += 1
        prefix = text[start:end].lower()
        if not prefix:
            return
        suffix = " "
        if prefix[0] == '/':
            l = sorted([("/" + x) for x in _k.chat_commands.keys()])
        elif prefix[0] in kaeirc.CHANNEL_PREFIXES:
            l = sorted(self._client.channels.keys(), _k.cmp_channels)
        elif self._cur_channel and (self._cur_channel[0] != '('):
            nl = self._client.channels[self._cur_channel].nicknames
            l = [ nl[x].nickname for x in nl.keys() ]
            l.sort(key=unicode.lower)
            if atstart:
                suffix = _kc.nick_complete_suffix
                if suffix is None:
                    suffix = ""
                suffix += " "
        else:
            return
        matches = [ ]
        for x in range(len(l)):
            item = l[x]
            if item.startswith(prefix):
                matches.append(item)
        if len(matches) == 0:
            self.echo("No matches.")
            return
        elif len(matches) == 1:
            match = matches[0]
            partial = False
        else:
            # Note: Even though it's supposed to work on paths, `commonprefix'
            #       works char-by-char, so it's useful in this case.
            match = os.path.commonprefix(matches)
            self.echo("Possible matches: %s" % " ".join(matches))
            partial = True
        if partial:
            repl = text[:start] + match + text[end:]
            rlen = len(match) - len(prefix)
        else:
            repl = text[:start] + match + suffix + text[end:]
            rlen = len(match) - len(prefix) + len(suffix)
        self._chatvar.set(repl)
        self._chatbox.icursor(end + rlen)

    def _sel_chan(self, event):
        sel = self._chanlist.get(Tix.ANCHOR)
        self.select_channel(sel)

    # TODO: These two should be replaced by `kaechatlib.ui.History'.

    def _prev_hist(self, event):
        if len(self._history) == 0:
            return
        if self._hist_index > 0:
            self._hist_index -= 1
            self._chatvar.set(self._history[self._hist_index])

    def _next_hist(self, event):
        if len(self._history) == 0:
            return
        if self._hist_index < len(self._history) - 1:
            self._hist_index += 1
            self._chatvar.set(self._history[self._hist_index])

    def _do_send(self, event=None):
        text = self._chatvar.get()
        if text != "":
            if len(self._history) == 500:
                self._history.remove(0)
            self._history.insert(-1, text)
            self._hist_index = len(self._history) - 1
            if (text[0] == '/') and (len(text) >= 2) and (text[1] != '/'):
                try:
                    _k.run_command(self, text[1:])
                except NotImplementedError as e:
                    self.echo(e.message, channel=self._cur_channel)
            elif self.cur_channel[0] != '(':
                if text[0] == '/':
                    text = text[1:]
                self.client.privmsg(self.cur_channel, text)
                self.echo(text, who=self._client.nickname)
            else:
                self.echo("Cannot send to special channel")
            self._chatvar.set("")

#=============================================================================

class MainFrame(Tix.Frame):
    """Main application frame.

    This frame contains the network selector (a `Tix.NoteBook'), and
    initializes the menu of it's toplevel.
    """

    def __init__(self, master=None, *args, **kw):
        """Construct a new `MainFrame' instance.

        All arguments are passed as-is to the `Tix.Frame' constructor.
        """
        Tix.Frame.__init__(self, master, *args, **kw)
        self._init_widgets()
        self._init_bindings()
        self._root().title("KaeChat")
        self._page_serial = 0

    def connect(self, netid):
        """Connect to a given network ID."""
        if netid in _k.networks:
            pagename = "network%d" % self._page_serial
            self._page_serial += 1
            net = _k.networks[netid]
            page = self._notebook.add(pagename, label=net.name)
            page.netframe = NetworkFrame(page, pagename=pagename, network=net,
              netid=netid)
            page.netframe.pack(fill=Tix.BOTH, expand=True)

    def reload_config(self):
        """Calls `reload_config()' on each open `NetworkFrame'."""
        for page in self._notebook.pages():
            page.netframe.reload_config()

    def echo(self, text):
        """Echo something to the global "echo box"."""
        tb = self._echobox
        tb.configure(state=Tix.NORMAL)
        tb.insert(Tix.END, text + "\n")
        tb.configure(state=Tix.DISABLED)

    def _init_widgets(self):
        self._init_menu()
        self._notebook = Tix.NoteBook(self)
        self._notebook.pack(fill=Tix.BOTH, expand=True)
        f = self._notebook.add("@messages", label="(KaeChat)")
        self._echobox_ = Tix.ScrolledText(f)
        self._echobox_.pack(fill=Tix.BOTH, expand=True)
        self._echobox = self._echobox_.text
        self._echobox.configure(state=Tix.DISABLED)

    def _init_bindings(self):
        pass

    def _init_menu(self):
        win = self._root()
        m = Tix.Menu(win, tearoff=False)
        netmenu = Tix.Menu(m, tearoff=False)
        netmenu.add_command(label="Connect...", command=self._net_connect)
        netmenu.add_command(label="Disconnect", command=self._net_disconnect)
        netmenu.add_separator()
        netmenu.add_command(label="Quit", command=self._root().destroy)
        m.add_cascade(label="Network", menu=netmenu)
        editmenu = Tix.Menu(m, tearoff=False)
        editmenu.add_command(label="Preferences...", command=self._edit_prefs)
        m.add_cascade(label="Edit", menu=editmenu)
        helpmenu = Tix.Menu(m, tearoff=False)
        helpmenu.add_command(label="Chat commands",
          command=self._help_chatcommands)
        helpmenu.add_separator()
        helpmenu.add_command(label="About...", command=self._help_about)
        m.add_cascade(label="Help", menu=helpmenu)
        win.configure(menu=m)

    def _net_connect(self):
        nl = _kuinl.NetworkListWindow(self)

    def _net_disconnect(self, event=None):
        pagename = self._notebook.raised()
        if pagename[0] != '@':
            f = self._notebook.page(pagename).netframe
            if f.active:
                f._thread._client.disconnect()
            self._notebook.delete(pagename)

    def _edit_prefs(self):
        _kuipf.PreferencesWindow(self._root())

    def _help_chatcommands(self):
        for name in sorted(_k.chat_commands.keys()):
            c = _k.chat_commands[name]
            _k.echo(c[1] + "\n\n" + c[2])

    def _help_about(self):
        _kuiab.AboutDialog(self._root())

#=============================================================================
