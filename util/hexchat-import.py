#! /usr/bin/env python2.7

# hexchat-import.py: Import configuration options from HexChat.

# This script is quite hacky due to the wacky HexChat config file format(s),
# and lack of support on Python Standard Library.

# So far, this can import the following options:
#   - Some main options (from `hexchat.conf', see supported_options below).
#   - Network List (from `servlist_.conf'). Note that only the first server
#     listed in each network is used!
#   - CTCP Replies (from `ctcpreply.conf'). Note that only entries beginning
#     with "nctcp %s" followed by the query are imported. PING is never
#     imported as it's not configurable in KaeChat.

import os
import sys

import argparse

def conv_bool(x):
    return "true" if int(x) else "false"

supported_options = {
    # <input option>: (<output section>, <output option>, <conv>)
    "completion_suffix": ("chat", "nick_complete_suffix", str),
    "gui_tab_notices": ("chat", "notices_to_chan", conv_bool),
    "irc_nick1": ("networks", "nicks", str),
    "irc_nick2": ("networks", "nicks", str),
    "irc_nick3": ("networks", "nicks", str),
    "irc_user_name": ("networks", "username", str),
    "irc_real_name": ("networks", "realname", str),
}

from ConfigParser import RawConfigParser

# Huh? *ConfigParser does not support a "root" section?
def read_config(filenames):
    options = { }
    filenames_read = [ ]
    for filename in filenames:
        if os.path.isfile(filename):
            with open(filename, 'U') as f:
                for line in f:
                    line = line.lstrip()
                    eq = line.find('=')
                    if eq != -1:
                        key, value = [ x.strip() for x in line.split('=', 1) ]
                        options[key] = value
                filenames_read.append(filename)
    return options, filenames_read

# XXX: Better name?
def read_blanksep_config(filename, sep='='):
    if os.path.isfile(filename):
        sections = [ ]
        options = None
        with open(filename, 'U') as f:
            for line in f:
                line = line.lstrip()
                if not line:
                    if options:
                        sections.append(options)
                        options = None
                    continue
                if not options:
                    options = { }
                eq = line.find(sep)
                if eq != -1:
                    key, value = [ x.strip() for x in line.split(sep, 1) ]
                    options[key] = value
        if options:
            sections.append(options)
    return sections

def set_opt(section, option, value):
    if not kc_conf.has_section(section):
        kc_conf.add_section(section)
    if kc_conf.has_option(section, option):
        value = kc_conf.get(section, option) + ", " + value
    kc_conf.set(section, option, value)

def parse_hexchat_conf(dir):
    if dir:
        hc_conf_files = (os.path.join(dir, "hexchat.conf"),)
    else:
        HOME = os.path.expanduser("~")
        hc_conf_files = (
            os.path.join(HOME, ".hexchat", "hexchat.conf"),
            os.path.join(HOME, ".config", "hexchat", "hexchat.conf"),
        )

    hc_conf, hc_conf_files = read_config(hc_conf_files)

    if not hc_conf_files:
        print >>sys.stderr, "Could not find suitable `hexchat.conf' file."

    for k in hc_conf:
        if k in supported_options:
            v = hc_conf[k]
            sect, opt, conv = supported_options[k]
            set_opt(sect, opt, conv(v))

def parse_servlist_conf(dir):
    if dir:
        filenames = (os.path.join(dir, "servlist_.conf"),)
    else:
        HOME = os.path.expanduser("~")
        filenames = (
            os.path.join(HOME, ".hexchat", "servlist_.conf"),
            os.path.join(HOME, ".config", "hexchat", "servlist_.conf"),
        )
    for filename in filenames:
        if os.path.isfile(filename):
            conf = read_blanksep_config(filename)
            for options in conf:
                if ("N" in options) and ("S" in options):
                    name = options["N"]
                    addr = options["S"]
                    chans = filter(None, [ x.strip() for x in options.get("J", "").split(",") ])
                    sect = "networks/" + name.replace(" ", "_").replace("/", "_").lower()
                    def set_conf(opt, val, sect=sect):
                        if not kc_conf.has_section(sect):
                            kc_conf.add_section(sect)
                        kc_conf.set(sect, opt, val)
                    set_conf("name", name)
                    set_conf("address", addr.split(",")[0].strip())
                    if chans:
                        set_conf("channels", ", ".join(chans))
            break

def parse_ctcpreply_conf(dir):
    if dir:
        filenames = (os.path.join(dir, "ctcpreply.conf"),)
    else:
        HOME = os.path.expanduser("~")
        filenames = (
            os.path.join(HOME, ".hexchat", "ctcpreply.conf"),
            os.path.join(HOME, ".config", "hexchat", "ctcpreply.conf"),
        )
    for filename in filenames:
        if os.path.isfile(filename):
            conf = read_blanksep_config(filename, sep=" ")
            def set_conf(opt, val):
                if not kc_conf.has_section("ctcp"):
                    kc_conf.add_section("ctcp")
                kc_conf.set("ctcp", opt, val)
            for options in conf:
                if ("NAME" in options) and ("CMD" in options):
                    name = options["NAME"].lower()
                    if name == "ping":
                        continue
                    cmd = options["CMD"]
                    pfx = "nctcp %s " + name + " "
                    if cmd.lower().startswith(pfx):
                        cmd = cmd[len(pfx):]
                        if cmd:
                            set_conf(name, cmd)
            break

def main(argv=sys.argv, stdout=sys.stdout, stderr=sys.stderr):
    prog, args = argv[0], argv[1:]
    argp = argparse.ArgumentParser(
        prog=prog,
        description="Convert HexChat configuration to KaeChat configuration."
    )
    argp.add_argument("-d", "--dir", help="Specify directory containing HexChat configuration.")
    argp.add_argument("-o", "--output", help="Set output file (default: stdout).")
    argp.add_argument("-l", "--list-options", help="List supported options.", action="store_true")
    argp.add_argument("-e", "--extend", help="Extend specified (KaeChat) config file.")
    try:
        old_files = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = (stdout, stderr)
        opts = argp.parse_args(args)
        sys.stdout, sys.stderr = old_files
    except SystemExit as e:
        return e.code

    if opts.list_options:
        for k in sorted(supported_options.keys()):
            o = supported_options[k]
            print "%s -> [%s] %s" % (k, o[0], o[1])
        return 0

    global kc_conf
    kc_conf = RawConfigParser()

    parse_hexchat_conf(opts.dir)
    parse_servlist_conf(opts.dir)
    parse_ctcpreply_conf(opts.dir)

    try:
        f = open(opts.output, 'w') if (opts.output and (opts.output != "-")) else stdout
        kc_conf.write(f)
    except IOError as e:
        print >>stderr, e
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
