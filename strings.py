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

INDENT = '  '  # 2 space indent

# Strings dispatched to discord
###############################################################################
# ALREADY_APPROVED = "{} is already approved"
COULD_NOT_FIND = "Could not find {}"
# APPROVED = "{} **added** and **approved**\n\nkey - **{}**"
# ADDED = "{} **added**\n\nkey - **{}**"
DELETE_SUCCESS = "**{}** succesfully deleted"
NOT_FOUND = "**{}** was not found in the database"
DISCONNECTING_YOU_LOWER = 'disconnecting you…'
DISCONNECTING_YOU_UPPER = 'Disconnecting you…'

APPROVED = "**{}:** Added and Approved\n**Key:** {}"
ADDED = "**{}:** Added, not Approved\n**Key:** {}"
WRONG_CHANNEL = "Command used in the wrong channel"
ALREADY_APPROVED = "**{}**: Already Approved\n**Key:** {}"
YOU_WERE_DELETED = "Your key was deleted from the server"
HEY = "Hey, **<@{}>** :flushed:"
GOT_BOT_ROLE = "Okay, received the bot role"
BOT_ROLE_LACKS_PERMS = ", tho its missing {} permissions. I kinda need them" \
    + ", to do my work…"
BOT_ROLE_HAS_PERMS = ". Permissions look okay  :heart:"

# on_member_join
MJ_INTRO = "Welcome, {}, to {}"
MJ_RESTRICTED = "This is a restricted server"
MJ_INFO = "Please replay with the key linked with {}"
MJ_WARNING = "Note: There's a bug in Discord, which won't update the user" \
    + "panel, until you relog"
MJ_SECONDS = "You have {} seconds, before being disconnected"
MJ_IDLE = "You need a valid **key**, to access this server"
MJ_ACCEPTED = "Key accepted"
MJ_DECLINED = "The key was **incorrect**"
MJ_WHAT_KEY = "The key was {}"
MJ_KEY_ACCEPTED = "Key approved!"
MJ_DISCONNECTED_NOW = ", disconnecting you from the server"

# Key verification
KV_TITLE = "Key Verification"
KV_USER = "User"
KV_KEY = "Key"
KV_STATUS = "Status"
KV_APPROVED = "Approved"
KV_ADDED = "Assigned key, not approved"
KV_NOT_APPROVED = "No key"
KV_DECLINED = "Declined"
KV_TIMEOUT = "Timeout"
KV_KICK_NOTICE = "You have {} seconds, before being disconnected"
KV_WARNING = "Note: There's a bug in Discord, which won't update the user" \
    + "panel, until you relog"
KV_KEY_HIDDEN = "Hidden"

# Key declined
KD_TITLE = "Key Declined"

# sweep_server
SW_START = "Performing a sweep, to kick unapproved members"
SW_NOT_APPROVED = "You're not approved in **{}**"
SW_ATTEMPT_K = "Attempting to kick {}"
SW_COMPLETE = "Sweep complete"
