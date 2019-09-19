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

# pylint: disable=redefined-builtin
from utils import make_print


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Permissions', *args, **kwargs)


class Permissions:
    """Methods for permission checks around Discord client"""
    def __init__(self):
        """Copies over some booleans from discord.Roles.Permissiosn"""
        self.permissions = None
        self.can_kick = False
        self.can_ban = False
        self.can_move = False
        self.can_manage_roles = False

    def add_role(self, role):
        """When the bot role is added, evalute its permissions"""
        print(f'Parsing permissions for the role - {role.name}')

        self.permissions = role.permissions
        self.can_kick = role.permissions.kick_members
        self.can_ban = role.permissions.ban_members
        self.can_move = role.permissions.move_members
        self.can_manage_roles = role.permissions.manage_roles

        print('Permissions locked')
        print(f'  Can kick - {self.can_kick}')
        print(f'  Can ban - {self.can_ban}')
        print(f'  Can move - {self.can_move}')
        print(f'  Can manage roles - {self.can_manage_roles}')

    def update_role(self, role):
        """When bot role is updated, recalculate its permissiosn"""
        self.add_role(role)
