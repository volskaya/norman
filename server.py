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

import threading
import asyncio
import aiohttp

from aiohttp import web
from utils import make_print


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Server', *args, **kwargs)


class Server:
    """Socket listens for commands, meant for DB interaction"""
    def __init__(self, loop, store, config, bot):
        """Create a web server

        Register routes and attach it to the main event loop
        """
        self.store = store
        self.bot = bot

        print('Creating an API server on '
              + f'{config.server_ip}:{config.server_port}…')

        app = web.Application()
        app.add_routes([
            web.get('/user/{id}', self.get_user_by_id),
            web.get('/user/id/{id}', self.get_user_by_id),
            web.get('/user/name/{name}/{id}', self.get_user_by_name),
            web.get('/user/add/{id}', self.add_user_by_id),
            web.get('/user/approve/{id}', self.approve_user_by_id),
            web.get('/user/remove/{id}', self.invalidate_user_by_id)
        ])

        loop.run_until_complete(loop.create_server(
            app.make_handler(), config.server_ip, config.server_port))

        print('Server running')

    async def get_user_by_id(self, request):
        """Retreive users DB entry by their ID"""
        user_id = request.match_info['id']

        try:
            print(f'Responding to GET get_user_by_id({user_id})')
            return web.json_response(
                self.store.get_user(user_id))
        except KeyError:
            print(f'User - {user_id} not found!')
            return web.HTTPNotFound(reason='User does not exist')

    async def get_user_by_name(self, request):
        """Retreive users DB entry by their name"""
        name = request.match_info.get('name', 'noname')
        user_id = request.match_info.get('id', '0')
        username = name + '#' + user_id

        try:
            print(f'Responding to GET get_user_by_id({username})')
            return web.json_response(
                self.store.get_user(username))
        except KeyError:
            print(f'User - {username} not found!')
            return web.HTTPNotFound(reason='User does not exist')

    async def approve_user_by_id(self, request):
        """Generate an approved DB entry for the specified ID """
        user_id = request.match_info['id']

        print(f'Approve user GET requested for {user_id}')
        entry = await self.store.add_user(user_id, True)

        return web.json_response(entry)

    async def add_user_by_id(self, request):
        """Generates a DB entry for the specified ID"""
        user_id = request.match_info['id']

        print(f'Add user GET requested for {user_id}')
        entry = await self.store.add_user(user_id, False)
        member = await self.bot.get_user_by_id(user_id)

        if member:  # Request key, if online
            await self.bot.request_key(member)

        return web.json_response(entry)

    async def invalidate_user_by_id(self, request):
        """Invalidates a DB entry for the specified ID"""
        user_id = request.match_info['id']
        print(f'Invalidate GET requested for {user_id}')
        self.store.invalidate(user_id)

        # Kick the user/Remove role, if online
        member = await self.bot.get_user_by_id(user_id)

        if member:  # Kick, if arg doesn't block it
            await self.kick(member)
            await self.remove_role(
                member, self.config.roles['approved']['ref'])

        return web.HTTPOk()
