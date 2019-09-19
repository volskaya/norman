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

# pylint: disable=redefined-builtin, too-many-locals, import-error, too-many-branches, unused-variable
import sys
import asyncio
import aiohttp
import discord
import func_strings as f

from store import Store
from config import Config
from permissions import Permissions
from utils import make_print, new_line
from arguments import Arguments
from embed import Embed
from bot import Bot
from server import Server


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Main', *args, **kwargs)


def exit_bot():
    """Print exit and close the program"""
    print('Exitting…')
    sys.exit(0)


async def main(client, store, args, config, embed, bot):
    """Instantiate classes and run the bot"""
    @client.event
    async def on_member_update(before, after):
        """Validates new users
        Tracks and updates name changes
        Kicks unauthorized users
        Removes / adds roles as needed
        """
        if not before or not after:
            return  # Probably called, before the bot is ready

        if before.bot or after.bot:
            return

        # Create a DB entry for every new user
        if store.make_user_blank_entry(after):
            print(f'Created an empty DB entry for {after}')

        if str(before) != str(after) or \
                store.is_new_name(after.id, str(after)):
            print(f'Name update detected, {before.name} > {after.name}')
            print(f'Updating DB entry name of {after.id} to {after}')
            store.update_user_entry(after)

        if not store.is_valid(after):
            print(f'Updating an invalidated DB entry, ID - {after}')
            store.update_user_entry(after)

        # Avoid unnecessary calculations below
        if before.status == after.status:
            return

        # Check if a new bot role received
        # This is only supported in dynamic roles, so only check name
        if before.id == config.client.user.id:  # bot's id
            old_status = bot.has_bot_role(before)
            new_status = bot.has_bot_role(after)

            # If old false, new true, means bot role recently added
            if not old_status and new_status:
                print('Bot received the "Bot" role')
                try:
                    # new_status will return the bot role
                    await embed.nm_first_msg(config.server.owner, new_status)
                except discord.errors.HTTPException:
                    print("Couldn't send out nm_first_msg embed")
            elif old_status and not new_status:
                print('Bot lost its "Bot" role')

        if before.server.id != config.server_id \
           and after.server.id == config.server_id:
            await bot.request_key(after)
            return

        is_approved = store.is_approved(after)

        # Handle a real user
        if not is_approved and store.get_user_key(after):
            print(f'Unapproved {after} connected, requesting the key')
            await bot.request_key(after)
        elif not is_approved and not after.bot:
            print(f'{after} does not have a valid key, kicking…')
            await embed.nm_not_approved(after)

            # NOTE: Removing a role + kicking == on_member_update infinite loop
            if args.kick:
                await bot.kick(after)
            else:
                await bot.remove_role(after, config.roles['approved']['ref'])
        elif is_approved:
            # Ensure the user has "Approved role"
            if not bot.has_approved_role(after):
                print(f'{after} is missing "Approved" role, fixing…')
                await bot.add_role(after, config.roles['approved']['ref'])

    @client.event
    async def on_member_remove(member):
        """Invalidate members DB entry, when it leaves the server"""
        print(f'{member} removed from the server')
        if store.is_approved(member) or store.get_user_key(member):
            store.invalidate(member, True)  # True = keep the key

    @client.event
    async def on_member_ban(member):
        """Delete the user from the database"""
        print(f'{member} got banned, deleting from the database')
        success = await store.remove_user_by_id(member.id)

        if success:
            print(f'{member} deleted successfully')

    @client.event
    async def on_ready():
        """Sets default username and picture"""
        new_line()
        print('Connection successful')
        print('Bot logged in as ' + client.user.name + '\n')

        config.client = client

        await bot.set_defaults()

        if args.print_stats_only:
            await client.close()
        else:  # Continue
            await bot.sweep_server()

    @client.event
    async def on_message(message):
        """Listens for bot commands"""
        if isinstance(message, discord.Channel):
            if message.server != config.server:
                print('Message received from an unauthorized channel')
                print('  ' + message.content)
                return  # Don't process anyone outside the config server

        # !add
        if message.content.startswith(f.ADD):
            if not config.is_admin(message.author):
                print(f'{message.author} tried to execute {f.ADD}')
                return

            # User will have a key, but won't be approved
            # Returns user reference, if added succesfully and available
            member = await bot.add_user(message, False)

            # Also request the key right away, incase the user is sitting
            # in the server and --no-kick is on
            if member and member.status != discord.Status.offline \
               and not store.is_approved(member):
                print(f'{member} is online, requesting key right away')
                await bot.request_key(member)

        # !approve
        elif message.content.startswith(f.APPROVE):
            if not config.is_admin(message.author):
                print(f'{message.author} tried executing {f.APPROVE}')
                return

            # Approves user name like "!approve Test#1234"
            # Passing in True will automatically approve the user
            await bot.add_user(message, True)

        # !remove
        elif message.content.startswith(f.REMOVE):
            if not config.is_admin(message.author):
                print(f'{message.author} tried to execute {f.REMOVE}')
                return

            target = message.content.split(' ')[1]
            await bot.remove_user(message, target)

        # !am
        elif message.content.startswith(f.AM):
            print(f'Checking if {message.author} is approved')
            print(f'Member id {message.author.id}')

            await embed.nm_approved(
                message.channel,
                message.author,
                store.is_approved(message.author))

        # Returns a response, if the message.author has permissions
        # to use the bot
        elif message.content.startswith(f.HEY):
            status = config.is_admin(message.author)
            print(f'{message.author} checked for bot permissions ({status})')

            config.has_admin_role(message.author)

            if status:
                await embed.hey(message)

    @client.event
    async def on_server_role_update(old, new):
        """Maintain references to roles, as they change"""
        if old.server.id != config.server_id:
            return

        print(f'Role update! {old.name} -> {new.name}')
        await config.on_update_role(old, new)

        if bot.sweep_bans_needed and new.permissions.ban_members:
            print('Bot now has permissions to sweep the ban list, proceeding…')
            await bot.sweep_bans()

    @client.event
    async def on_server_role_delete(role):
        """Pause the bot, if a reference to a role is lost"""
        if role.server.id != config.server_id:
            return

        print(f'Role {role.name} deleted')
        await config.on_delete_role(role)

    @client.event
    async def on_server_role_create(role):
        """Server role added"""
        print(f'New role detected - {role.name}')
        config.lock_role(role)

    @client.event
    async def on_server_unavailable(server):
        """Pause the bot, when the target server becomes unavailable"""
        if server.id == config.server_id:
            print(f'Target server, {server.name} has become unavailable')
            print(f'Exitting…')
            await client.close()
            exit_bot()

    @client.event
    async def on_server_available(server):
        """Resume the bot, when the target server becomes available"""
        main_server_found = False

        if server.id == config.server_id:
            main_server_found = True
            config.server = server

            print(f'Target server, {server.name} has become available')

            new_line()
            await config.lock_roles(server)

            for i in config.roles:
                if config.roles[i]['enabled'] and \
                   not config.roles[i]['ref']:
                    print(f'Still waiting for "{i}" role')

        if not main_server_found:
            print('Still waiting for the server specified in the config file…')

    # Callbacks end
    connected = False

    while not connected:
        try:
            connected = True
            print('Connecting to discord…')
            await client.start(config.token)
        except aiohttp.errors.ClientOSError:
            connected = False
            print('Failed to connect to discord, restarting…')


def init():
    """Handle discord.Client() with care"""
    client = discord.Client()
    loop = asyncio.get_event_loop()

    # Local classes
    args = Arguments(sys.argv[1:])
    permissions = Permissions()
    config = Config(args, permissions)
    store = Store()
    embed = Embed(client, config, args)
    bot = Bot(client, store, config, embed, permissions, args)
    server = Server(loop, store, config, bot)  # Server goes live on init

    if not args.instantiated or not config.instantiated:
        loop.run_until_complete(client.close())
        exit_bot()

    try:
        loop.run_until_complete(
            main(client, store, args, config, embed, bot))
    except KeyboardInterrupt:
        loop.run_until_complete(client.close())
    finally:
        loop.close()


if __name__ == '__main__':
    init()
elif __name__ == 'norman':
    init()
