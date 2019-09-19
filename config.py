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

# pylint: disable=redefined-builtin, too-many-instance-attributes
import json

from pathlib import Path
from utils import CONFIG_PATH, make_print


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Config', *args, **kwargs)


def print_assigned(key, value):
    """Forma a string"""
    print(f'{key} - {value}')


def is_str(var):
    """Returns True, if int"""
    return isinstance(var, str)


class Config:
    """Parser for ./config file"""
    def __init__(self, args, permissions):
        """Does the parse already on init"""
        self.instantiated = False
        self.args = args
        self.permissions = permissions

        # Override config trough args
        if args.config_path:
            self.config = args.config_path
            print(f'Config path overridden to {self.config.absolute()}')
        else:
            self.config = CONFIG_PATH

        try:
            self.json = json.loads(Path(self.config).read_text())
        except FileNotFoundError:
            raise FileNotFoundError('Config file does not exist!')

        # Bots user profile
        self.name = self.json.get('name', 'Norman')  # Name of the bot user
        self.his_color = 0xffffff
        self.repo = 'https://github.com/volskaya/norman'
        avatar_path = self.json.get('avatar', './data/norman.jpg')

        try:
            self.avatar = Path(avatar_path).read_bytes()
        except FileNotFoundError:
            raise FileNotFoundError(f'{avatar_path} not found, check your config.js')

        # Server address, TODO: Have args change this
        self.server_ip = self.json.get('server_ip', '127.0.0.1')
        self.server_port = self.json.get('server_port', '8080')

        if args.server_ip:
            self.server_ip = args.server_ip
        if args.server_port:
            self.server_port = args.server_port

        # Roles
        self.roles = {
            'approved': {
                'enabled': True,
                'id': None,
                'dynamic': False,
                'ref': None
            },
            'bot': {
                'enabled': True,
                'id': None,
                'dynamic': False,
                'ref': None
            },
            'admin': {
                'enabled': False,
                'id': None,
                'dynamic': False,
                'ref': None
            }
        }

        # Values from config file
        self.token = None
        self.owner_id = None
        self.server_id = None

        try:
            self.token = self.json['token']
            self.owner_id = str(self.json['owner'])
            self.server_id = str(self.json['server'])

            # Accept int for roles
            self.roles['approved']['id'] = self.json['role']['approved']
            self.roles['bot']['id'] = self.json['role']['bot']
            self.roles['admin']['id'] = self.json['role']['admin']
        except KeyError as error:
            print(f'{error} expected in the config.json')

        # Holds references to discord objects
        self.client = None  # Discord client
        self.owner = None  # User reference from the ID in the config
        self.server = None  # Server reference, after matching its ID

        self.check_for_missing()
        self.parse_config()

    def parse_config(self):
        """If a role ID, from the config, is a string, interpret it
        as a name and when a name is provided, support dynamic role look
        up, even when  references to roles are lost

        Else turn int settings back into strings and keep dynamic False
        """
        for i in self.roles:
            if self.roles[i]['enabled'] and is_str(self.roles[i]['id']):
                self.roles[i]['dynamic']: True
            else:
                # Turn the int ID into a string
                self.roles[i]['id'] = str(self.roles[i]['id'])

    def check_for_missing(self):
        """Throws, if any field is missing"""
        if not self.token:
            raise RuntimeError('Token missing from the config')
        elif not self.owner_id:
            raise RuntimeError('Owner ID missing from the config')
        elif not self.server_id:
            raise RuntimeError('Server ID missing from the config')

        for i in self.roles:
            name = str(self.roles[i]['id'])

            if self.roles[i]['enabled'] and not self.roles[i]['id']:
                raise RuntimeError(
                    f'"{name} role ID/Name is missing from the config file"')
            elif not self.roles[i]['enabled'] and not self.roles[i]['id']:
                print(f'{name} missing, disabling its functions…')

        self.instantiated = True

    def get_avatar(self):
        """Safely get bots avatar"""
        if self.client.user.avatar_url:
            return self.client.user.avatar_url
        return self.client.user.default_avatar_url

    def safe_get_user_avatar(self, member):
        """Returns user avatar
        Fallsback to bots avatar, if user doesn't have it
        """
        try:
            return member.avatar_url
        except AttributeError:
            return self.get_avatar()

    def has_admin_role(self, member):
        """Returns true, if @member has admin role"""
        if not self.roles['admin']['enabled']:
            return False

        for role in member.roles:
            if role.id == self.roles['admin']['id'] \
               or role.name == self.roles['admin']['id']:
                return True
        return False

    def is_admin(self, member):
        """Returns true if member is the bot / server owner
        Returns true if member is server owner, bot owner/host, has admin role
        """
        if member.id == self.server.owner.id \
           or member.id == self.owner_id or self.has_admin_role(member):
            return True
        return False

    async def lock_server(self, servers):
        """Returns the server, specified in the config file"""
        print('Connected to: ')

        for server in servers:
            print(f'  {server.name} - {server.id}')
            print(f'    owner ID - {server.owner.id}')

            if server.id == self.server_id:
                print(f'Found {server.name}')
                self.server = server
                self.owner = server.owner

                return server
        return None

    async def lock_roles(self, server):
        """Finds the reference to the approved role"""
        print('Server roles:')

        for role in server.roles:
            print(f'  {role.name}, id - {role.id}')

            for i in self.roles:
                if not self.roles[i]['enabled']:
                    continue

                if role.id == self.roles[i]['id'] \
                        or role.name == self.roles[i]['id']:
                    print(f'Found "{i}" role - {role.name}, {role.id}')
                    self.roles[i]['ref'] = role

                    # Parse bot role permissions
                    if i == 'bot':
                        self.permissions.add_role(role)

    async def on_update_role(self, old, new):
        """Keep a reference to a dynamic role, if it ever changes"""
        for i in self.roles:
            if self.roles[i]['enabled'] and self.roles[i]['dynamic'] \
               and old.name == self.roles[i]['name']:
                self.roles[i]['id'] = new.name
                self.roles[i]['ref'] = new
                print(f'Updated {i} role with {new.name}')

                if i == 'bot':
                    self.permissions.update_role(new)

    async def on_delete_role(self, role):
        """Delete reference to a role, so it could be checked easier"""
        for i in self.roles:
            if self.roles[i]['enabled'] and self.roles[i]['dynamic'] \
               and role.name == self.roles[i]['name']:
                self.roles[i]['ref'] = None
                print(f'Lost reference to {i} role')

                if i == 'bot':
                    self.permissions.update_role(role)

    def lock_role(self, role):
        """Assign a reference to an existing role"""
        for i in self.roles:
            if role.id == self.roles[i]['id']:
                print(f'Reassigning a reference to {i} role')
                self.roles[i]['ref'] = role

                # Parse bot role permissions
                if i == 'bot':
                    self.permissions.add_role(role)
