#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-

from distutils.core import setup

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__) or ".", "lib"))
import kaechatlib.locals

setup(name='KaeChat',
    description="A simple Internet Relay Chat client using Python/Tkinter.",
    version="%s.%s.%s" % kaechatlib.locals.VERSION,
    packages=["kaeirc", "kaechatlib", "kaechatlib.ui"],
    author="Diego Martínez",
    author_email="lkaezadl3@gmail.no.spam.com",
    package_dir={"": "lib"},
    scripts=["bin/kaechat", "bin/kaechat.py"],
)
