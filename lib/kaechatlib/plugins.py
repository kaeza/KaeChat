
import imp
import kaechatlib.config
import os

plugins = [ ]
plugins_by_name = { }

def do_import(filename, name):
    f = open(filename, 'U')
    m = imp.load_module("kaechatlib.plugins." + name, f, filename, (".py", 'U', imp.PY_SOURCE))
    kaechatlib.echo("Loading plugin `%s' from `%s'" % (name, filename))
    if m:
        plugins.append(m)
        plugins_by_name[name] = m

def load_plugins():
    kaechatlib.echo("Loading plugins...")
    for d in kaechatlib.config.find_configs("plugins"):
        dl = os.listdir(d)
        for f in dl:
            name, ext = os.path.splitext(f)
            if (not name in plugins_by_name) and (ext == ".py"):
                do_import(os.path.join(d, f), name)

def call_plugins(func, *args, **kw):
    for plugin in plugins:
        if hasattr(plugin, func):
            f = getattr(plugin, func)
            r = f(*args, **kw)
            if r is not None:
                return r
