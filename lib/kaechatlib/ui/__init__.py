
"""
Main User Interface Module
"""

import collections

import Tkinter

import kaechatlib.config

from kaechatlib.ui.locals import *

#=============================================================================

class __unused_History(collections.deque):

    def __init__(self, maxsize=500):
        collections.deque.__init__(self, maxsize)
        self.hist_index = 0

    def get_next(self):
        self.hist_index = max(0, min(len(self) - 1, self.hist_index + 1))
        if self.hist_index < len(self):
            return self[self.hist_index]
        else:
            return None

    def get_prev(self):
        self.hist_index = max(0, min(len(self) - 1, self.hist_index - 1))
        if self.hist_index < len(self):
            return self[self.hist_index]
        else:
            return None

    def push(self, line):
        self.append(line)
        self.hist_index = len(self) - 1

#=============================================================================

def set_colors(widget, setting):
    colors = kaechatlib.config.get_list("theme", setting)
    if len(colors) < 1:
        return
    elif len(colors) == 1:
        fg, bg = colors[0], None
    else:
        fg, bg = colors[0:2]
    if fg:
        try:
            widget.configure(fg=fg)
        except Tkinter.TclError:
            pass
    if bg:
        try:
            widget.configure(bg=bg)
        except Tkinter.TclError:
            pass

#=============================================================================
