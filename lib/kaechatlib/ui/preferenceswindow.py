
import kaechatlib.config
import kaechatlib.plugins

from Tkinter import *
from Tix import *

class Page(Frame):

    label = "(no label)"
    title = "(no title)"

    def __init__(self, master=None, *args, **kw):
        Frame.__init__(self, master, *args, **kw)
        self._init_widgets()
        self._init_bindings()

    def _init_widgets(self):
        pass

    def _init_bindings(self):
        pass

    def commit(self):
        pass

class GeneralPage(Page):

    label = "General"
    title = "Configure general options."

    def _init_widgets(self):
        pass

    def commit(self):
        pass

class ConversationPage(Page):

    label = "Conversation"
    title = "Chat-related options."

    def _init_widgets(self):
        self.notice_chan_var = IntVar(self, 0)
        Checkbutton(self, text="Send NOTICEs to special channel.",
            variable=self.notice_chan_var, anchor=W).pack(fill=X)
        self.hilite_chan_var = IntVar(self, 1)
        Checkbutton(self, text="Echo highlights to special channel.",
            variable=self.hilite_chan_var, anchor=W).pack(fill=X)

    def commit(self):
        kaechatlib.config.set_bool("chat", "notices_to_chan", self.notice_chan_var.get())
        kaechatlib.config.set_bool("chat", "highlights_to_chan", self.hilite_chan_var.get())

class CTCPPage(Page):

    label = "CTCP Replies"
    title = "Configure CTCP replies."

    def _init_widgets(self):
        l = Label(self, text="""\
Fill in replies to CTCP queries. One item per line.
Each line starts with query type, followed by a space, and the message.""")
        l.pack(side=TOP)
        self.textbox = ScrolledText(self, width=200, height=100)
        self.textbox.pack(side=BOTTOM, fill=BOTH, expand=True)
        cfg = kaechatlib.config.config
        if cfg.has_section("ctcp"):
            for opt in cfg.options("ctcp"):
                val = cfg.get("ctcp", opt)
                self.textbox.text.insert(END, opt.upper() + " " + val + "\n")

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

    label = "Theme"
    title = "Configure colors, fonts, etc."

    def _init_widgets(self):
        pass

    def commit(self):
        pass

_pages = ( GeneralPage, ConversationPage, CTCPPage, ThemePage )

class PreferencesWindow(Toplevel):

    def __init__(self, master=None, *args, **kw):
        Toplevel.__init__(self, master, *args, **kw)
        self._init_widgets()
        self._init_bindings()
        self.title("KaeChat Preferences")
        self.pages = [ ]
        for page in _pages:
            self.add_page(page)
        kaechatlib.plugins.call_plugins("on_prefswindow_create", self)

    def _init_widgets(self):
        self.notebook = NoteBook(self)
        self.notebook.pack(side=TOP, fill=BOTH, expand=True)
        self.buttonbox = ButtonBox(self)
        self.buttonbox.pack(side=BOTTOM, fill=X)
        Button(self.buttonbox, text="OK", command=self._ok).pack(side=LEFT)
        Button(self.buttonbox, text="Cancel", command=self.destroy).pack(side=RIGHT)

    def _init_bindings(self):
        pass

    def _ok(self):
        r = None
        for page in self.pages:
            r = page.commit()
            if r is not None:
                break
        if not r:
            self.destroy()
            kaechatlib.config.save()
            #kaechatlib.mainframe.reload_config()

    def add_page(self, page):
        f = self.notebook.add(page.__name__.lower(), label=page.label)
        f.title = Label(f, text=page.title)
        f.title.pack(side=TOP)
        f.child = page(f)
        f.child.pack(side=BOTTOM, fill=BOTH, expand=True)
        self.pages.append(f.child)
        return f.child
