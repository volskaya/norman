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
import argparse

from pathlib import Path
from utils import NAME, DESCRIPTION, make_print


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Args', *args, **kwargs)


class Arguments:
    """Process and store arguments"""
    def __init__(self, argv):
        print('Instantiating Arguments')

        self.instantiated = False
        self.print_stats_only = False
        self.kick = True
        self.config_path = None
        self.db_backend = None  # TODO
        self.timeout_time = 60
        self.prevent_admin_role = False
        self.server_ip = None
        self.server_port = None

        self.argv = argv
        self.args = self.create_arguments()

        self.process_arguments()

    def create_arguments(self):
        """Prepare the arg structure"""
        prog = NAME
        description = DESCRIPTION
        arg = argparse.ArgumentParser(
            prog=prog, description=description)

        arg.add_argument('-c', '--config', metavar='./config_2.txt',
                         help='Override default config location')

        arg.add_argument('-b', '--backend', metavar='file',
                         help='Currently the only supported backend is "file"')

        arg.add_argument('-i', '--info', action='store_true',
                         help='Logs into the bot and prints out servers, roles'
                         + ' or any other info you\'d need to set up the bot')

        arg.add_argument('-t', '--timeout', metavar='60',
                         help='Seconds before kick. 0 means no kick')

        arg.add_argument('-k', '--no-kick', action='store_true',
                         help='Disable kick on invalid keys')

        arg.add_argument('--no-admin-role', action='store_true',
                         help='Ignore admin role permissions')

        arg.add_argument('--ip', metavar='127.0.0.1',
                         help='API server ip')

        arg.add_argument('--port', metavar='8080',
                         help='API server port')

        return arg.parse_args(self.argv)

    def process_arguments(self):
        """Assigns arguments to class variables"""
        errors = 0

        if self.args.config:
            self.config_path = Path(self.args.config)
            print(f'Config path changed to {str(self.config_path)}')

        if self.args.backend:
            if self.args.backend != 'file':
                print(f'Backend "{self.args.backend}" is not supported')
                errors += 1
            else:
                self.db_backend = self.args.backend

        if self.args.info:
            self.print_stats_only = True

        if self.args.timeout:
            self.timeout_time = int(self.args.timeout)
            print(f'Timeout set to {self.timeout_time}')

        if self.args.no_kick:
            self.kick = False
            print('Kick disabled')

        if self.args.no_admin_role:
            self.prevent_admin_role = True
            print("Admin role won't be able to interact with the bot")

        if self.args.ip:
            self.server_ip = self.args.ip
            print('API IP changed to ' + self.server_ip)

        if self.args.port:
            self.server_port = self.args.port
            print('API port changed to ' + self.server_port)

        if errors == 0:
            self.instantiated = True
            print('Arguments instantiated\n')
        else:
            print(f'There were errors, while instantiating arguments\n')
