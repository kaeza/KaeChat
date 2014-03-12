
from Tix import *
from tkSimpleDialog import Dialog
import tkMessageBox

from kaechatlib.locals import FULL_VERSION_STR
import kaechatlib.config
import kaechatlib.plugins

class Page(Frame):

    id = None
    label = "(no label)"
    title = "(no title)"

    def __init__(self, master=None, *args, **kw):
        Frame.__init__(self, master, *args, **kw)
        self.init_widgets()
        self.init_bindings()

    def init_widgets(self):
        pass

    def init_bindings(self):
        pass

    def commit(self):
        pass

    def validate(self):
        return True

class GeneralPage(Page):

    id = "kaechat_general"
    label = "General"
    title = "Configure general options."

    def init_widgets(self):
        pass

    def commit(self):
        pass

class ConversationPage(Page):

    id = "kaechat_chat"
    label = "Conversation"
    title = "Chat-related options."

    def init_widgets(self):
        self.nickomplete_var = StringVar(self, kaechatlib.config.nick_complete_suffix)
        self.notice_chan_var = IntVar(self, int(kaechatlib.config.notices_to_chan))
        self.hilite_chan_var = IntVar(self, int(kaechatlib.config.highlights_to_chan))
        e = LabelEntry(self)
        e.label.configure(text="Nick completion suffix")
        e.entry.configure(textvariable=self.nickomplete_var)
        e.pack(fill=X)
        Checkbutton(self, text="Send NOTICEs to special channel.",
            variable=self.notice_chan_var, anchor=W).pack(fill=X)
        Checkbutton(self, text="Echo highlights to special channel.",
            variable=self.hilite_chan_var, anchor=W).pack(fill=X)

    def commit(self):
        kaechatlib.config.set_bool("chat", "notices_to_chan", self.notice_chan_var.get())
        kaechatlib.config.set_bool("chat", "highlights_to_chan", self.hilite_chan_var.get())
        kaechatlib.config.set("chat", "nick_complete_suffix", self.nickomplete_var.get())

class CTCPPage(Page):

    id = "kaechat_ctcp"
    label = "CTCP Replies"
    title = "Configure CTCP replies."

    def init_widgets(self):
        l = Label(self, text="""\
Fill in replies to CTCP queries. One item per line.
Each line starts with query type, followed by a space, and the message.""")
        l.pack(side=TOP)
        self.textbox = ScrolledText(self, width=200, height=100)
        f = Frame(self)
        f.pack(side=BOTTOM, fill=X)
        b = Button(f, text="Help on replacements", command=self._repl_help)
        self.textbox.pack(side=BOTTOM, fill=BOTH, expand=True)
        b.pack(side=LEFT)
        cfg = kaechatlib.config.config
        if cfg.has_section("ctcp"):
            for opt in cfg.options("ctcp"):
                val = cfg.get("ctcp", opt)
                self.textbox.text.insert(END, opt.upper() + " " + val + "\n")

    def _repl_help(self):
        tkMessageBox.showinfo("Help", """\
Replies may contain "replacements", in the form {name}. The following \
replacements are available:

  {version} - Program Version ('"""+FULL_VERSION_STR+"""')
  {time} - Current time, in HH:MM:SS format.
  {date} - Current date, in YYYY-MM-DD format.
  {nick} - Current nickname for current network.
  {source} - Nickname sending the query.

Example:
  Hello {source}! My time is {time}, and I'm using {version}.
""")

    def commit(self):
        text = self.textbox.text.get('0.0', END)
        cfg = kaechatlib.config.config
        if not cfg.has_section("ctcp"):
            cfg.add_section("ctcp")
        for line in text.splitlines():
            line = line.strip()
            if line:
                l = line.split(' ', 1)
                if len(l) == 2:
                    query, reply = l
                else:
                    query, reply = l[0], ""
                query, reply = query.rstrip().lower(), reply.lstrip()
                kaechatlib.config.set("ctcp", query, reply)

class ThemePage(Page):

    id = "kaechat_theme"
    label = "Theme"
    title = "Configure colors, fonts, etc."

    def init_widgets(self):
        pass

    def commit(self):
        pass

_pages = ( GeneralPage, ConversationPage, CTCPPage, ThemePage )

class PreferencesWindow(Dialog):

    def __init__(self, master):
        Dialog.__init__(self, master, "KaeChat Preferences")

    def body(self, master):
        self.resizable(False, False)
        self.notebook = NoteBook(master)
        self.notebook.pack(side=TOP, fill=BOTH, expand=True)
        Label(master, text="\
NOTE: Items marked with an asterisk ('*') will take effect on restart.").pack(side=TOP, fill=X)
        self.btnbox = Frame(master)
        self.btnbox.pack(side=BOTTOM, fill=X)
        Button(self.btnbox, text="Cancel", command=self.cancel).pack(side=RIGHT)
        Button(self.btnbox, text="OK", command=self.ok).pack(side=RIGHT)
        self.pages = [ ]
        for page in _pages:
            self.add_page(page)
        kaechatlib.plugins.call_plugins("on_prefswindow_create", self)

    def buttonbox(self):
        pass

    def validate(self):
        r = True
        for page in self.pages:
            rr = page.validate()
            if not rr:
                r = False
                break
        return r

    def apply(self):
        for page in self.pages:
            page.commit()
        kaechatlib.config.save()
        kaechatlib.config.update_config()
        kaechatlib.mainframe.reload_config()

    def add_page(self, page):
        f = self.notebook.add(page.id or page.__name__.lower(), label=page.label)
        f.title = Label(f, text=page.title)
        f.title.pack(side=TOP)
        f.child = page(f)
        f.child.pack(side=BOTTOM, fill=BOTH, expand=True)
        self.pages.append(f.child)
        return f.child
