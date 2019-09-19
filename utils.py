#!/usr/bin/env python

""" Copyright (C) 2018 github.com/volskaya

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# pylint: disable=import-error
from __future__ import print_function
import builtins as __builtin__

from pathlib import Path
from random import getrandbits

import discord

NAME = 'Norman'
DESCRIPTION = 'Example: ./__main__.py -v --config ./config_2.txt --print-only'

PWD = Path(__file__).parent
CONFIG_PATH = PWD / 'config.json'
SHELVE_PATH = PWD / 'users'

N = '\n'
RED = discord.Colour.red()
YELLOW = discord.Colour.orange()
GREEN = discord.Colour.green()


def make_print(prefix, *args, **kwargs):
    """Prefixes will let more easily differentiate the debug logs"""
    return __builtin__.print(prefix + ':', *args, **kwargs)


def new_line():
    """Defining newline, because print is getting overridden above"""
    return print('')


def make_key():
    """Returns a random key"""
    key = getrandbits(128)

    print(f'Random key generated - {key}')
    return str(key)


def is_id(numbers):
    """Tries to parse string to
    If it succeeds, assume its an ID and return True
    """
    try:
        int(numbers)
        return True
    except ValueError:
        pass
    except TypeError:
        pass

    return False

def get_avatar_url(member):
    """Safely gets avatars url from member"""
    if member.avatar_url:
        return member.avatar_url
    return member.default_avatar_url
