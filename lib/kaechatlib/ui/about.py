
import Tix
import tkSimpleDialog

import kaechatlib as _k
import kaechatlib.license
import kaechatlib.authors

#=============================================================================

class AboutDialog(tkSimpleDialog.Dialog):

    def __init__(self, master):
        tkSimpleDialog.Dialog.__init__(self, master, "About KaeChat")

    def body(self, master):
        self.resizable(False, False)
        Tix.Label(master, text=_k.FULL_VERSION_STR).pack(side=Tix.TOP)
        self.notebook = Tix.NoteBook(master)
        self.notebook.pack(side=Tix.TOP, fill=Tix.BOTH, expand=True)
        f = self.notebook.add("license", label="License")
        f.tb = Tix.ScrolledText(f)
        f.tb.pack(fill=Tix.BOTH, expand=True)
        tb = f.tb.text
        tb.insert(Tix.END, kaechatlib.license.__doc__)
        tb.configure(state=Tix.DISABLED, width=80, height=10)
        f = self.notebook.add("authors", label="Authors")
        for a in kaechatlib.authors.AUTHORS:
            Tix.Label(f, text=a).pack(side=Tix.TOP, anchor=Tix.W)
        Tix.Button(master, text="OK", command=self.destroy).pack(side=Tix.TOP,
          anchor=Tix.E)

    def buttonbox(self):
        pass

#=============================================================================
