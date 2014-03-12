
import Tix
import tkMessageBox
import tkSimpleDialog

import kaechatlib.config as _kc
import kaechatlib as _k

#=============================================================================

class NetworkEditWindow(tkSimpleDialog.Dialog):

    def __init__(self, netlistwin, netid=None, network=None):
        self.netlistwin = netlistwin
        self.netid = netid
        self.network = network
        if network is None:
            title = "New Network"
        else:
            title = "Edit Network %s" % network.name
        tkSimpleDialog.Dialog.__init__(self, netlistwin, title)

    def _add_entry(self, master, label, var, state=None):
        line = self._line
        self._line += 1
        l = Tix.Label(master, text=label)
        l.grid(column=0, row=line, sticky=Tix.W)
        e = Tix.Entry(master, textvariable=var)
        e.grid(column=1, row=line, sticky=Tix.W+Tix.E)
        if state:
            e.configure(state=state)
        return e

    def body(self, master):
        self.resizable(False, False)
        master.configure(width=400)
        self.name_var = Tix.StringVar(self,
            self.network.name if self.network is not None else "New Network")
        self.addr_var = Tix.StringVar(self,
          (("%s/%d" % self.network.address) if self.network is not None
          else "server/6667"))
        self.nicks_var = Tix.StringVar(self,
          ", ".join(self.network.nicks) if self.network is not None else "")
        self.user_var = Tix.StringVar(self,
          self.network.username if self.network is not None else "")
        self.realname_var = Tix.StringVar(self,
           self.network.realname if self.network is not None else "")
        self.chans_var = Tix.StringVar(self,
          ", ".join(self.network.channels) if self.network is not None else "")
        self.auto_var = Tix.BooleanVar(self,
          self.network.autoconnect if self.network is not None else False)
        self._line = 0
        name_state = Tix.DISABLED if self.network is not None else None
        nameentry = self._add_entry(master, "Name", self.name_var, name_state)
        addrentry = self._add_entry(master, "Address", self.addr_var)
        self._add_entry(master, "Nicknames", self.nicks_var)
        self._add_entry(master, "Username", self.user_var)
        self._add_entry(master, "Real name", self.realname_var)
        self._add_entry(master, "Channels to join", self.chans_var)
        Tix.Checkbutton(master, text="Connect to this network at startup",
            variable=self.auto_var).grid(
              column=0, row=self._line, columnspan=2, sticky=Tix.W)
        return nameentry if self.network is not None else addrentry

    def validate(self):
        name = self.name_var.get()
        addr = self.addr_var.get().split('/', 1)
        if len(addr) == 2:
            try:
                addr = (addr[0].strip(), int(addr[1]))
            except ValueError:
                tkMessageBox.showerror("Error", "Port must be a number.")
                return False
        else:
            addr = (addr[0].strip(), 6667)
        if len(addr[0]) == 0:
            tkMessageBox.showerror("Error", "You must specify an address.")
            return False
        username = self.user_var.get()
        realname = self.realname_var.get()
        nicks = [ ]
        for x in self.nicks_var.get().split():
            x = x.strip()
            if x:
                nicks.append(x)
        channels = [ ]
        for x in self.chans_var.get().split():
            x = x.strip()
            if x:
                channels.append(x)
        autoconnect = bool(self.auto_var.get())
        if self.network is not None:
            netid = self.netid
        else:
            netid = name.replace('.', '_').replace(' ', '_').lower()
            if netid in kaechatlib.networks:
                r = tkMessageBox.askyesno("Warning", """\
Network with ID `%s' already exists.
Overwrite?""")
                if not r:
                    return False
        self.netid = netid
        self.network = _k.NetworkConfig(
            name=name,
            address=addr,
            username=username if username else None,
            realname=realname if realname else None,
            nicks=nicks if nicks else None,
            autoconnect=autoconnect,
            channels=channels if channels else None
        )
        return True

    def apply(self):
        _k.networks[self.netid] = self.network
        self.netlistwin.refresh_netlist()
        _k.save_networks()
        _kc.save()

#=============================================================================

class NetworkListWindow(tkSimpleDialog.Dialog):

    def __init__(self, master):
        tkSimpleDialog.Dialog.__init__(self, master, "Network List")
        #self.resizable(False, False)

    def body(self, master):
        self.resizable(False, False)
        topf = Tix.Frame(master)
        topf.pack(side=Tix.TOP)
        self.netlist_ = Tix.ScrolledListBox(topf)
        self.netlist_.pack(side=Tix.LEFT, fill=Tix.BOTH, expand=True)
        self.netlist = self.netlist_.listbox
        self.netlist.configure(selectmode=Tix.BROWSE)
        btnf = Tix.Frame(topf)
        btnf.pack(side=Tix.RIGHT, fill=Tix.Y, expand=True)
        Tix.Button(btnf, text="Add", command=self._add_net).pack(
          side=Tix.TOP, fill=Tix.X)
        Tix.Button(btnf, text="Delete", command=self._del_net).pack(
          side=Tix.TOP, fill=Tix.X)
        Tix.Button(btnf, text="Edit", command=self._edit_net).pack(
          side=Tix.TOP, fill=Tix.X)
        #botf = Tix.Frame(master)
        #botf.pack(side=Tix.BOTTOM, fill=Tix.X)
        Tix.Button(btnf, text="Close", command=self.cancel).pack(
          side=Tix.BOTTOM, fill=Tix.X)
        self.netlist.bind("<Double-Button-1>", self.ok)
        #_k.load_networks()
        self.refresh_netlist()

    def buttonbox(self):
        pass

    def refresh_netlist(self):
        self.netlist.delete(0, Tix.END)
        for netid in sorted(_k.networks.keys()):
            net = _k.networks[netid]
            self.netlist.insert(Tix.END, "%s [%s]" % (net.name, netid))

    def _add_net(self):
        w = NetworkEditWindow(self)

    def _del_net(self):
        sel = self.netlist.get(Tix.ANCHOR)
        if not sel: return
        netid = sel.split('[', 1)[1].split(']', 1)[0]
        net = _k.networks[netid]
        r = tkMessageBox.askyesno("Warning", """\
Deleting a network configuration cannot be undone.
Are you sure you want to delete %s?""" % net.name)
        if r:
            del _k.networks[netid]
            _k.save_networks()
            _kc.save()
            self.refresh_netlist()

    def _edit_net(self):
        sel = self.netlist.get(Tix.ANCHOR)
        if not sel: return
        netid = sel.split('[', 1)[1].split(']', 1)[0]
        net = _k.networks[netid]
        w = NetworkEditWindow(self, netid=netid, network=net)

    def apply(self, event=None):
        sel = self.netlist.get(Tix.ANCHOR)
        netid = sel.split('[', 1)[1].split(']', 1)[0]
        _k.connect(netid)
        self.destroy()

#=============================================================================
