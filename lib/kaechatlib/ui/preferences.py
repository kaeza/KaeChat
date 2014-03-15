
"""
KaeChat Preferences Dialog
"""

import Tix
import tkSimpleDialog
import tkMessageBox

import kaechatlib as _k
import kaechatlib.locals as _kl
import kaechatlib.config as _kc
import kaechatlib.plugins as _kp

#=============================================================================

class Page(Tix.Frame):
    """Base class for widgets implementing configuration "pages"."""

    label = None
    title = None

    def __init__(self, master=None, label=None, title=None):
        """Construct a new `Page' instance.

        `master' is the containing frame (a notebook page).

        `label' is the text used for the notebook page label.

        `title' is used as the text for a `Tix.Label' added above the frame.
        """
        Tix.Frame.__init__(self, master)
        self.init_widgets()

    def init_widgets(self):
        """Called by the constructor to initialize the widgets for this page.

        The default implementation does nothing.
        """
        pass

    def commit(self):
        """Called when the user clicks the "OK" button in the preferences
        dialog to actually apply the configuration.

        This method is only called if no `validate()' method returns a false
        value.

        The default implementation does nothing.
        """
        pass

    def validate(self):
        """Called when the user clicks the "OK" button in the preferences
        dialog to do self-checks on the input data.

        Should return a true value if everything is OK, or a false value if
        something is not right.

        If all `validate()' methods return a true value, the preferences
        dialog proceeds to call `commit()'.

        The default implementation always returns true.
        """
        return True

    def raise_page(self):
        """Instructs the containing notebook to make this page visible.

        Use this e.g. when `validate()' reports an error to show the page and
        focus the relevant widget.

        NOTE: Don't use this from a page's constructor!
        """
        self._notebook.raise_page(self._pagename)

#=============================================================================

class GeneralPage(Page):

    label = "General"
    title = "Configure general options."

    def init_widgets(self):
        """Called by the constructor to initialize the widgets for this page.
        """
        pass

    def commit(self):
        """Called when the user clicks the "OK" button in the preferences
        dialog to actually apply the configuration.

        This method is only called if no `validate()' method returns a false
        value.
        """
        pass

#=============================================================================

class ConversationPage(Page):

    label = "Conversation"
    title = "Chat-related options."

    def init_widgets(self):
        """Called by the constructor to initialize the widgets for this page.
        """
        self._nickomplete_var = Tix.StringVar(self, _kc.nick_complete_suffix)
        self._notice_chan_var = Tix.BooleanVar(self, _kc.notices_to_chan)
        self._hilite_chan_var = Tix.BooleanVar(self, _kc.highlights_to_chan)
        e = Tix.LabelEntry(self)
        e.label.configure(text="Nick completion suffix")
        e.entry.configure(textvariable=self._nickomplete_var)
        e.pack(fill=Tix.X)
        Tix.Checkbutton(self, text="Send NOTICEs to special channel.",
          variable=self._notice_chan_var, anchor=Tix.W).pack(fill=Tix.X)
        Tix.Checkbutton(self, text="Echo highlights to special channel.",
          variable=self._hilite_chan_var, anchor=Tix.W).pack(fill=Tix.X)

    def commit(self):
        """Called when the user clicks the "OK" button in the preferences
        dialog to actually apply the configuration.

        This method is only called if no `validate()' method returns a false
        value.
        """
        _kc.set_bool("chat", "notices_to_chan", self._notice_chan_var.get())
        _kc.set_bool("chat", "highlights_to_chan", self._hilite_chan_var.get())
        _kc.set("chat", "nick_complete_suffix", self._nickomplete_var.get())

#=============================================================================

class CTCPPage(Page):

    label = "CTCP Replies"
    title = "Configure CTCP replies."

    def init_widgets(self):
        """Called by the constructor to initialize the widgets for this page.
        """
        l = Tix.Label(self, text="""\
Fill in replies to CTCP queries. One item per line.
Each line starts with query type, followed by a space, and the message.""")
        l.pack(side=Tix.TOP)
        self._textbox_ = Tix.ScrolledText(self, width=200, height=100)
        self._textbox_.pack(side=Tix.BOTTOM, fill=Tix.BOTH, expand=True)
        self._textbox = self._textbox_.text
        self._textbox.configure(width=40, height=8)
        f = Tix.Frame(self)
        f.pack(side=Tix.BOTTOM, fill=Tix.X)
        b = Tix.Button(f, text="Help on replacements", command=self._repl_help)
        b.pack(side=Tix.LEFT)
        cfg = _kc.config
        if cfg.has_section("ctcp"):
            for opt in cfg.options("ctcp"):
                val = cfg.get("ctcp", opt)
                self._textbox.insert(Tix.END, opt.upper() + " " + val + "\n")

    def _repl_help(self):
        tkMessageBox.showinfo("Help", """\
Replies may contain "replacements", in the form {name}. The following \
replacements are available:

  {version} - Program Version ('"""+_kl.FULL_VERSION_STR+"""')
  {time} - Current time, in HH:MM:SS format.
  {date} - Current date, in YYYY-MM-DD format.
  {nick} - Current nickname for current network.
  {source} - Nickname sending the query.

Example:
  Hello {source}! My time is {time}, and I'm using {version}.
""")

    def commit(self):
        """Called when the user clicks the "OK" button in the preferences
        dialog to actually apply the configuration.

        This method is only called if no `validate()' method returns a false
        value.
        """
        text = self._textbox.get('0.0', Tix.END)
        cfg = _kc.config
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
                _kc.set("ctcp", query, reply)

#=============================================================================

class ThemePage(Page):

    label = "Theme"
    title = "Configure colors, fonts, etc."

    def init_widgets(self):
        """Called by the constructor to initialize the widgets for this page.
        """
        pass

    def commit(self):
        """Called when the user clicks the "OK" button in the preferences
        dialog to actually apply the configuration.

        This method is only called if no `validate()' method returns a false
        value.
        """
        pass

#=============================================================================

_pages = ( GeneralPage, ConversationPage, CTCPPage, ThemePage )

#=============================================================================

class PreferencesWindow(tkSimpleDialog.Dialog):
    """KaeChat preferences dialog."""

    def __init__(self, master):
        """Construct a new `PreferencesWindow' instance."""
        self._page_index = 0
        tkSimpleDialog.Dialog.__init__(self, master, "KaeChat Preferences")

    def add_page(self, page):
        """Add a new page to the notebook.

        `page' must be a subclass (not an instance!) of `Page'.
        """
        pagename = "page%d" % self._page_index
        self._page_index += 1
        f = self._notebook.add(pagename, label=page.label)
        f._titlelabel = Tix.Label(f, text=page.title)
        f._titlelabel.pack(side=Tix.TOP)
        f._childframe = page(f)
        f._childframe._notebook = self._notebook
        f._childframe._pagename = pagename
        f._childframe.pack(side=Tix.BOTTOM, fill=Tix.BOTH, expand=True)
        self.pages.append(f._childframe)
        return f._childframe

    def body(self, master):
        self.resizable(False, False)
        self._notebook = Tix.NoteBook(master)
        self._notebook.pack(side=Tix.TOP, fill=Tix.BOTH, expand=True)
        self._btnbox = Tix.Frame(master)
        self._btnbox.pack(side=Tix.BOTTOM, fill=Tix.X)
        Tix.Button(self._btnbox, text="Cancel",
          command=self.cancel).pack(side=Tix.RIGHT)
        Tix.Button(self._btnbox, text="OK",
          command=self.ok).pack(side=Tix.RIGHT)
        self.pages = [ ]
        for page in _pages:
            self.add_page(page)
        _kp.call_plugins("on_prefswindow_create", self)

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
        _kc.save()
        _kc.update_config()
        _k.mainframe.reload_config()

#=============================================================================
