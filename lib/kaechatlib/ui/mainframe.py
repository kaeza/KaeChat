
import time
import webbrowser

import Tix
import tkMessageBox as _tkmb

import irc

import kaechatlib as _k
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

    colors = (
        "#000000", "#000080", "#008000", "#008080",
        "#800000", "#800080", "#808000", "#808080",
    )

    def __init__(self, frame, client, channel):
        Tix.Frame.__init__(self, frame.top_frame)
        self.frame = frame
        self.client = client
        self.channel = channel
        self._init_widgets()
        self._init_bindings()
        self.event = _k.IDLE_EV

    def _init_widgets(self):
        f = Tix.Frame(self)
        f.pack(side=Tix.TOP, fill=Tix.BOTH, expand=True)
        ff = Tix.Frame(f)
        ff.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
        if self.channel[0] in irc.CHANNEL_PREFIXES:
            self.topicvar = Tix.StringVar()
            self.topicbox = Tix.Entry(ff, textvariable=self.topicvar)
            self.topicbox.pack(side=Tix.TOP, fill=Tix.X)
        else:
            self.topicbox = None
        self.textbox = Tix.ScrolledText(ff)
        self.textbox.pack(side=Tix.BOTTOM, fill=Tix.BOTH, expand=True)
        self.textbox.text.configure(state=Tix.DISABLED)
        if self.channel[0] in irc.CHANNEL_PREFIXES:
            ff = Tix.Frame(f)
            ff.pack(side=Tix.RIGHT, fill=Tix.BOTH)
            self.userlistlabel = Tix.Label(ff)
            self.userlistlabel.pack(side=Tix.TOP, fill=Tix.X)
            self.userlist_ = Tix.ScrolledListBox(ff)
            self.userlist_.pack(side=Tix.BOTTOM, fill=Tix.BOTH, expand=True)
            self.userlist = self.userlist_.listbox
            self.userlist.configure(selectmode=Tix.BROWSE, bg="white")
            for i in range(len(self.colors)):
                c = self.colors[i]
                self.textbox.text.tag_configure("color_%d" % i, foreground=c)
            self.textbox.text.tag_configure(_kui.WEB_LINK_TAG,
              foreground="#0000FF")
            m = Tix.Menu(self.userlist, tearoff=False)
            m.add_command(label="Who is this?", command=self._whois_ul)
            m.add_command(label="Start conversation",
              command=self._start_query_ul)
            self.userlist.menu = m
            _kui.set_colors(self.userlistlabel, "window")
            _kui.set_colors(self.userlist, "user_list")
        else:
            self.userlist = None
        _kui.set_colors(self, "window")
        _kui.set_colors(self.textbox, "textbox")
        _kp.call_plugins("on_channelframe_create", self)

    def _init_bindings(self):
        if self.userlist is not None:
            self.userlist.bind("<Double-Button-1>", self._start_query_ul)
            self.userlist.bind("<Button-3>", self._userlist_rclick)
        if self.topicbox is not None:
            self.topicbox.bind("<Return>", self._set_topic)
        self.textbox.text.tag_bind(_kui.WEB_LINK_TAG, "<Double-Button-1>",
          self._invoke_url)

    def _userlist_rclick(self, event):
        self.userlist.menu.post(event.x_root, event.y_root)

    def _invoke_url(self, event):
        # TODO: This needs better handling.
        x = event.widget.tag_prevrange(_kui.WEB_LINK_TAG,
          event.widget.index(Tix.CURRENT))
        if x:
            start, end = x
            url = event.widget.get(start, end)
            webbrowser.open(url)

    def reload_config(self):
        pass

    def _start_query_ul(self, event=None):
        sel = self.userlist.get(Tix.ANCHOR)
        if sel:
            if (sel[0] == '@') or (sel[0] == '+'):
                sel = sel[1:]
            self.frame.select_channel(sel)

    def _whois_ul(self):
        sel = self.userlist.get(Tix.ANCHOR)
        self.client.whois(sel)

    def _set_topic(self, event):
        self.client.topic(self.channel, self.topicvar.get())

    def format_message(self, line):
        m = _kui.HTTPS_RE.search(line)
        if m:
            yield line[:m.start()], _kui.TEXT_TAG
            yield m.group(), _kui.WEB_LINK_TAG
            yield line[m.end():], _kui.TEXT_TAG
        else:
            yield line, _kui.TEXT_TAG

    def echo(self, text, who=None, prefix=None):
        tb = self.textbox.text
        tb.configure(state=Tix.NORMAL)
        for line in text.splitlines():
            tb.insert(Tix.END, time.strftime("[%H:%M:%S] "))
            if prefix is not None:
                tb.insert(Tix.END, prefix)
            if who is not None:
                tb.insert(Tix.END, "<%s>" % who,
                  "color_%d" % (hash(who) % len(self.colors)))
            else:
                tb.insert(Tix.END, "***")
            tb.insert(Tix.END, " ")
            for (part, tag) in self.format_message(line):
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
        if self.userlist is not None:
            self.userlist.delete(0, Tix.END)
            if self.channel in self.client.channels:
                ops = [ ]
                voices = [ ]
                users = [ ]
                l = self.client.channels[self.channel].nicknames
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
                    self.userlist.insert(Tix.END, name)
                self.userlistlabel.configure(
                  text="%d Users, %d OPs" % (len(l), len(ops)))

#=============================================================================

class NetworkFrame(Tix.Frame):

    _event_colors = _event_colors

    def __init__(self, master=None, pagename=None, net=None, netid=None):
        Tix.Frame.__init__(self, master)
        self.pagename = pagename
        self.net = net
        self.netid = netid
        self.cur_channel = None
        self.history = [ "" ]
        self.hist_index = 0
        self.active = True
        self._init_widgets()
        self._init_bindings()
        self.thread = _kct.ClientThread(self)
        self.client = self.thread.client
        self.thread.start()

    def _init_widgets(self):
        self.top_frame = Tix.Frame(self)
        self.top_frame.pack(side=Tix.TOP, fill=Tix.BOTH, expand=True)
        self.chanlist = Tix.Listbox(self.top_frame, selectmode=Tix.BROWSE)
        self.chanlist.pack(side=Tix.LEFT, fill=Tix.Y)
        self.channel_frames = { }
        f = Tix.Frame(self)
        f.pack(side=Tix.BOTTOM, fill=Tix.X)
        self.nicklabel = Tix.Label(f, text="(unnamed)")
        self.nicklabel.pack(side=Tix.LEFT)
        self.chatvar = Tix.StringVar()
        self.chatbox = Tix.Entry(f, textvariable=self.chatvar)
        self.chatbox.pack(side=Tix.LEFT, fill=Tix.X, expand=True)
        self.chatbox.focus()
        self.sendbutton = Tix.Button(f, text="Send", command=self._do_send)
        self.sendbutton.pack(side=Tix.RIGHT)
        _kui.set_colors(self, "window")
        _kui.set_colors(self.nicklabel, "window")
        _kui.set_colors(self.chatbox, "chatbox")
        _kui.set_colors(self.chanlist, "channel_list")

    def _init_bindings(self):
        self.bind("<Destroy>", self._quit)
        self.chatbox.bind("<Return>", self._do_send)
        self.chatbox.bind("<Up>", self._prev_hist)
        self.chatbox.bind("<Down>", self._next_hist)
        self.chatbox.unbind_all("<Tab>")
        self.chatbox.bind("<Tab>", self._autocomplete)
        self.chanlist.bind("<<ListboxSelect>>", self._sel_chan)

    def reload_config(self):
        for channel in self.channel_frames:
            self.channel_frames[channel].reload_config()

    def _quit(self, event):
        self.thread.stop()

    def _autocomplete(self, event):
        text = self.chatvar.get()
        end = self.chatbox.index(Tix.INSERT)
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
            l = sorted([("/" + x) for x in kaechatlib.chat_commands.keys()])
        elif prefix[0] in irc.CHANNEL_PREFIXES:
            l = sorted(self.client.channels.keys(), kaechatlib.cmp_channels)
        elif self.cur_channel and (self.cur_channel[0] != '('):
            nl = self.client.channels[self.cur_channel].nicknames
            l = [ nl[x].nickname for x in nl.keys() ]
            l.sort(key=unicode.lower)
            if atstart:
                suffix = kaechatlib.config.nick_complete_suffix
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
        self.chatvar.set(repl)
        self.chatbox.icursor(end + rlen)

    def _sel_chan(self, event):
        sel = self.chanlist.get(Tix.ANCHOR)
        self.select_channel(sel)

    def _prev_hist(self, event):
        if len(self.history) == 0:
            return
        if self.hist_index > 0:
            self.hist_index -= 1
            self.chatvar.set(self.history[self.hist_index])

    def _next_hist(self, event):
        if len(self.history) == 0:
            return
        if self.hist_index < len(self.history) - 1:
            self.hist_index += 1
            self.chatvar.set(self.history[self.hist_index])

    def _do_send(self, event=None):
        text = self.chatvar.get()
        if text != "":
            if len(self.history) == 500:
                self.history.remove(0)
            self.history.insert(-1, text)
            self.hist_index = len(self.history) - 1
            if (text[0] == '/') and (len(text) >= 2) and (text[1] != '/'):
                try:
                    _k.run_command(self, text[1:])
                except NotImplementedError as e:
                    self.echo(e.message, channel=self.cur_channel)
            elif self.cur_channel[0] != '(':
                if text[0] == '/':
                    text = text[1:]
                self.client.privmsg(self.cur_channel, text)
                self.echo(who=self.client.nickname, text=text)
            else:
                self.echo("Cannot send to special channel")
            self.chatvar.set("")

    def get_channel_frame(self, channel=None, create=True):
        if channel is None:
            if self.cur_channel is None:
                channel = _k.SERVER_CHANNEL
            else:
                channel = self.cur_channel
        if channel in self.channel_frames:
            f = self.channel_frames[channel]
        elif create:
            f = ChannelFrame(self, self.client, channel)
            self.channel_frames[channel] = f
            self.refresh_chanlist()
        else:
            f = self.get_channel_frame(_k.ERRORS_CHANNEL)
        if self.cur_channel is None:
            self.cur_channel = channel
            f.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
        return f

    def echo(self, text, who=None, channel=None, prefix="", event=None):
        self.get_channel_frame(channel).echo(text, who=who, prefix=prefix)
        if (event is not None) and (channel != self.cur_channel):
            self.set_channel_event(channel, event)

    def clear(self, channel=None, lines=0):
        f = self.get_channel_frame(channel, create=False)
        if f:
            f.clear(lines)

    def refresh_userlist(self, channel):
        f = self.get_channel_frame(channel, create=False)
        if f:
            f.refresh_userlist()

    def refresh_chanlist(self):
        self.chanlist.delete(0, Tix.END)
        for name in sorted(self.channel_frames.keys(), _k.cmp_channels):
            self.chanlist.insert(Tix.END, name)

    def select_channel(self, channel):
        if not channel in self.channel_frames:
            self.get_channel_frame(channel)
        self.cur_channel = channel
        for name in self.channel_frames:
            f = self.channel_frames[name]
            if name == channel:
                f.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
            else:
                f.forget()
        self.set_channel_event(channel, _k.IDLE_EV, True)
        for i in range(self.chanlist.size()):
            name = self.chanlist.get(i)
            if irc.util.strlower(name) == channel:
                self.chanlist.selection_anchor(i)
        self.chatbox.focus()

    def set_channel_event(self, channel, event, override=False):
        if event < _k.IDLE_EV:
            event=_k.IDLE_EV
        elif event > _k.HIGHLIGHT_EV:
            event = _k.HIGHLIGHT_EV
        if (not override) and (self.channel_frames[channel].event >= event):
            return
        l = self.chanlist.size()
        for x in range(l):
            name = self.chanlist.get(x)
            if name == channel:
                self.chanlist.itemconfigure(x, fg=self._event_colors[event])
                break
        self.channel_frames[channel].event = event

#=============================================================================

class MainFrame(Tix.Frame):

    def __init__(self, master=None, *args, **kw):
        Tix.Frame.__init__(self, master, *args, **kw)
        self._init_widgets()
        self._init_bindings()
        self._root().title("KaeChat")
        self.open_nets = { }
        self._page_serial = 0

    def _init_widgets(self):
        self._init_menu()
        self.notebook = Tix.NoteBook(self)
        self.notebook.pack(fill=Tix.BOTH, expand=True)
        f = self.notebook.add("@messages", label="(KaeChat)")
        self.echobox = Tix.ScrolledText(f)
        self.echobox.pack(fill=Tix.BOTH, expand=True)
        self.echobox.text.configure(state=Tix.DISABLED)

    def _init_bindings(self):
        self.bind("<Destroy>", self._quit)

    def _quit(self, event):
        _kp.call_plugins("on_kaechat_quit")

    def _init_menu(self):
        win = self._root()
        m = Tix.Menu(win, tearoff=False)
        netmenu = Tix.Menu(m, tearoff=False)
        netmenu.add_command(label="Connect...", command=self._net_connect)
        netmenu.add_command(label="Disconnect", command=self._net_disconnect)
        netmenu.add_separator()
        netmenu.add_command(label="Quit", command=self._net_quit)
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

    def echo(self, text):
        tb = self.echobox.text
        tb.configure(state=Tix.NORMAL)
        tb.insert(Tix.END, text + "\n")
        tb.configure(state=Tix.DISABLED)

    def connect(self, netid):
        if netid in _k.networks:
            pagename = "network%d" % self._page_serial
            self._page_serial += 1
            net = _k.networks[netid]
            page = self.notebook.add(pagename, label=net.name)
            page.netframe = NetworkFrame(page, pagename=pagename, net=net,
              netid=netid)
            page.netframe.pack(fill=Tix.BOTH, expand=True)
            self.open_nets[netid] = page.netframe

    def reload_config(self):
        for netid in self.open_nets:
            self.open_nets[netid].reload_config()

    def _net_connect(self):
        nl = _kuinl.NetworkListWindow(self)

    def _net_disconnect(self, event=None):
        pagename = self.notebook.raised()
        if pagename[0] != '@':
            f = self.notebook.page(pagename).netframe
            if f.active:
                f.client.disconnect()
                f.client = None
            self.notebook.delete(pagename)
            del self.open_nets[f.netid]

    def _net_quit(self):
        if len(self.open_nets) > 0:
            r = _tkmb.showquestion("Warning", "There are networks still open. \
Are you sure you want to quit?")
            if not r:
                return
        self._quit()

    def _edit_prefs(self):
        _kuipf.PreferencesWindow(self._root())

    def _help_chatcommands(self):
        for name in sorted(_k.chat_commands.keys()):
            c = _k.chat_commands[name]
            _k.echo(c[1] + "\n\n" + c[2])

    def _help_about(self):
        d = _kuiab.AboutDialog(self._root())

#=============================================================================
