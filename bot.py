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

# pylint: disable=redefined-builtin, import-error, too-many-instance-attributes, too-many-arguments, too-many-return-statements
import discord

from utils import make_print, is_id


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Bot', *args, **kwargs)


class Bot:
    """Client object for discord.Client"""
    def __init__(self, client, store, config, embed, permissions, args):
        """Instantiate"""
        self.client = client
        self.store = store
        self.config = config
        self.embed = embed
        self.permissions = permissions
        self.args = args

        # Holds ID's to users, the bot currently awaits a key from
        # Used to prevent multiple requests, during @on_member_updated
        self.pending_users = []

        # If initial sweep has no permissions, queue up one, incase
        # the bot ever receives those permissions
        self.sweep_bans_needed = False

    def currently_validating(self, user_id):
        """Returns true, if bot is awaiting a key from the user ID"""
        try:
            self.pending_users.index(user_id)
            return True
        except ValueError:
            return False

    async def set_defaults(self):
        """Currently only sets default username"""
        if self.client.user.name != self.config.name:
            print(f'Changing bots old name - {self.client.user.name} '
                  + f'to {self.config.name} and uploading a new avatar')

            try:
                await self.client.edit_profile(username=self.config.name)
                await self.client.edit_profile(avatar=self.config.avatar)
            except discord.errors.HTTPException:
                print('Bots user update failed, skipping…')

    async def kick(self, member):
        """Shortcut for kicking, with error check

        Won't kick owner, specified in the config file
        If the bot has permissions to kick, assume it was
        intended to do so
        """
        if not self.permissions.can_kick or not self.args.kick:
            return

        try:
            if member.id != self.config.owner_id \
               and member != self.config.server.owner:
                await self.client.kick(member)
        except discord.Forbidden:
            print(f"Bot didn't have permissions to kick {member}")
        except AttributeError:
            pass  # Couldn't find the user

    async def move(self, member, to_channel):
        """Shortcut for moving members to channels

        If the bot has permissiosn to move, assume it was
        intended to do so
        """
        if not self.permissions.can_move:
            return

        try:
            self.client.move_member(member, to_channel)
        except discord.Forbidden:
            print(f"Bot didn't have permissions to move {member}")

    async def add_role(self, member, role):
        """Adds the accepted role

        If the bot has permissions to change roles,
        assume it was intended to do so
        """
        if not self.permissions.can_manage_roles:
            print("Bot didn't have enough permissions to manage roles")
            return

        if not role:
            print(f'Adding a role to {member} failed! Reference missing')

        try:
            await self.client.add_roles(member, role)
        except discord.Forbidden:
            print(f"Bot didn't have permissions to add a role to {member}")

    async def remove_role(self, member, role):
        """Removes the accepted role

        If the bot has permissions to change roles,
        assume it was intended to do so
        """
        if not self.permissions.can_manage_roles:
            print("Bot didn't have enough permissions to manage roles")
            return

        if not role:
            print(f'Removing a role from {member} failed! Reference missing')

        try:
            await self.client.remove_roles(member, role)
        except AttributeError:
            print(f'{member} had no role to remove')
        except discord.Forbidden:
            print(f"No permissions, to remove a role from {member}")

    async def validate_key(self, member, response):
        """Shortcut for validating a key"""
        if self.store.does_key_match(member, response):
            return True
        return False

    async def is_user_approved(self, message, member):
        """Shortcut for checking, if the user is already approved

        Will also print the appropriate message
        """
        try:
            user = self.store.get_user(member)

            if user['approved']:
                print(f'{message.author} tried approved an '
                      + f'already approved member {member}')

                await self.embed.nm_already_approved(
                    message.author, member, user['key'])
                return True
            return False
        except KeyError:
            return False

    async def get_user(self, name, channel=None):
        """Finds the user by its name

        If no channel specified, iterates over all users, the bot can see
        """
        if isinstance(name, (discord.User, discord.Member)):
            return name  # Don't do any lookup, if its already a member

        if isinstance(channel, discord.Channel):  # Find in channel
            member = discord.utils.find(
                lambda m: str(m) == name, channel.server.members)
            return member

        # Else find from everyone the bot can see
        for member in self.client.get_all_members():  # FIXME: Use discord.find
            if str(member) == name:
                return member

        return None

    async def get_user_by_id(self, user_id, channel=None):
        """Finds the user by its ID

        If no channel specified, iterates over all users, the bot can see
        """
        if isinstance(channel, discord.Channel):  # Find in channel
            member = discord.utils.find(
                lambda m: m.id == user_id, channel.server.members)
            return member

        # Else find from everyone the bot can see
        for member in self.client.get_all_members():  # FIXME: Use discord.find
            if member.id == user_id:
                return member

        return None

    # FIXME: Too many returns
    async def add_user(self, message, approve):
        """Shortcut for adding/approving a user"""
        target = message.content.split(' ')[1]  # 0 == command string
        channel = message.channel

        async def print_error():
            """Nested shortcut for add_user() error"""
            print(f'{message.author} tried approving {target}, '
                  + 'but the user was not found')
            await self.embed.nm_not_found(message.author, target)

        # When the user is not connected to the server, it can only be added
        # with its ID, since his name is outside of bots field of view

        # If using an ID, means the member is not in scope, so just create an
        # invalidated DB entry, which gets finished, the next time this ID
        # connects to the server
        # FIXME: First check, if the user is not in the server
        if is_id(target):
            print(f'Adding a user by ID, {target}')

            if await self.is_user_approved(message, target):
                return  # Function will send a warning message

            entry = await self.store.add_user(target, approve)
            await self.embed.nm_add(
                message.author, '<unknown>', entry['key'], approve)

            return None
        # If the bot received !approve in a private message, channel won't
        # have a server, so look trough all the servers the bot is connected to
        elif isinstance(channel, discord.PrivateChannel):
            # Iterates over all the channels the bot is connected to
            for member in self.client.get_all_members():
                if str(member) == target:
                    if await self.is_user_approved(message, member):
                        return  # Function will send a warning message

                    if approve:
                        await self.add_role(
                            member, self.config.roles['approved']['ref'])

                    # Send as a private message
                    entry = await self.store.add_user(member, approve)
                    await self.embed.nm_add(
                        message.author, member, entry['key'], approve)

                    return member
            await print_error()
            return None
        elif isinstance(channel, discord.Channel):
            # Only iterates over the message channel
            member = discord.utils.find(
                lambda m: str(m) == target, message.channel.server.members)

            if not member:
                await print_error()
                return

            if await self.is_user_approved(message, member):
                return member  # Function will send a warning message

            # Approval happens here
            entry = await self.store.add_user(member, approve)
            key = entry['key']

            # Send to the channel
            print(f'{message.author} approved {target}, key - {key}')
            await self.embed.nm_add(message.author, member, key, approve)
            return member
        else:
            print(f'{message.author} used !approve in an unsupported channel')
            return None

    async def remove_user(self, message, target):
        """Lookup user in the database and delete him

        Also dispatches messages to message.channel and target
        """
        if is_id(target):
            try:
                print(f'Removing user by ID - {target}')
                name = self.store.get_user(target)['name']

                await self.store.remove_user_by_id(target)
                await self.embed.nm_deleted(message.channel, name)
            except KeyError:
                print(f"Couldn't find a user with id {target} within the DB")
                await self.embed.nm_does_not_exist(message.channel, target)
            return  # Job done, return early

        # Looks up members only within the bots field of view
        member = await self.get_user(target)

        if not member:
            print(f"bot.remove_user() couldn't get user {target}")

            try:
                print("Falling back to DB lookup")
                user_id = self.store.get_user_id(target)
                name = self.store.get_user(user_id)['name']
                await self.store.remove_user_by_id(user_id)
                await self.embed.nm_deleted(message.channel, name)
            except KeyError:
                print("DB Lookup failed too")
                await self.embed.nm_does_not_exist(message.channel, target)
            return

        # Assume the bot was intended to remove the role and kick
        await self.kick(member)

        # Will have to lookup the username in the database and get
        # the key from there
        print(f'{message.author} deleting {target} from the database')
        success = await self.store.remove_user_by_id(member.id)

        if success:
            print(f'{message.author} deleted {target} from the store')
            print(f'Removing "Approved" role from {target}')

            await self.remove_role(
                member, self.config.roles['approved']['ref'])

            await self.embed.nm_you_were_deleted(member)
            await self.embed.nm_deleted(message.channel, member)
        else:
            print(f'{message.author} tried to delete {target} from the store')
            await self.embed.nm_does_not_exist(message.channel, member)

    async def remove_user_silent(self, target):
        """Lookup user in the database and delete him"""
        print(f'Attempting to delete {target} from the database')
        member = await self.get_user(target)
        success = await self.store.remove_user(member)

        if success:
            print(f'  {target} successfully deleted')
            await self.remove_role(
                member, self.config.roles['approved']['ref'])

            return True
        return False

    async def sweep_server(self):
        """Sweeps the server, when bot is ready

        Meant to clean up users, that slipped in, while the bot was off
        """
        count = 0

        print('Performing a sweep, to kick unapproved users')

        # list, so the generator wouldn't change, when someone is kicked
        for member in list(self.config.server.members):
            if not self.store.is_approved(member) and not member.bot:
                # If the member has a pending key, ask to validate it instead
                if self.store.get_user_key(member):
                    print(f'{member} has a pending key, validating it instead')
                    await self.request_key(member)
                    return

                print(f'Attempting to kick {member.name}')
                await self.embed.nm_not_approved(member)

                # NOTE: Removing a role + kicking
                # == on_member_update infinite loop
                if self.args.kick:
                    await self.kick(member)
                else:
                    await self.remove_role(
                        member, self.config.roles['approved']['ref'])

                count += 1

        print(f'Sweep complete, {count} members removed')
        print('Also checking banned members')
        await self.sweep_bans()

    async def sweep_bans(self):
        """Deletes members, with valid keys, from DB, if they're banned"""
        count = 0
        bans = []

        try:
            bans = await self.client.get_bans(self.config.server)
        except discord.Forbidden:
            self.sweep_bans_needed = True
            print("Bot didn't have permissions to access "
                  + f"{self.config.server.name} ban list")
            return  # Return early

        for member in bans:
            if self.store.is_approved(member) and not member.bot:
                print(f'Attempting to kick {member.name}')
                await self.kick(member)
                count += 1

                success = await self.remove_user_silent(member)

                if success:
                    print(f'Deleted {member} from the database')
        print(f'Ban sweep complete, {count} members removed')

    async def request_key(self, member):
        """Sends a message to a user, awaiting a key, else kick"""
        timeout = None  # None means no timeout

        if self.args.timeout_time > 0:
            timeout = self.args.timeout_time

        try:
            user = self.store.get_user(member)

            if not user['valid']:
                print(f'Updating an invalidated DB entry, ID - {member}')
                self.store.update_user_entry(member)

            if not user['approved']:
                if self.currently_validating(member.id):
                    return  # @on_member_update can cause redundant calls

                key = user['key']
                # self.currently_validating[member.id] = True
                self.pending_users.append(member.id)

                # First arg referes to channel
                await self.embed.nm_request_key(member, member)
                print(f'Waiting for a key from {member}, ({key})')

                response = await self.client.wait_for_message(
                    timeout=timeout, author=member, content=key)

                self.pending_users.remove(member.id)

                if not response:
                    print(f'Response from {member} was wrong')
                    await self.embed.nm_decline_key(member)

                    # Check if someone approved member, inbetween the request
                    if not self.store.is_approved(member):
                        await self.kick(member)
                    return  # Return early

                print(f'Received response: {response.content}')
                status = await self.validate_key(member, response.content)

                if status:
                    print(f'{member} responded with a correct key')

                    await self.embed.nm_accept_key(member, response.content)
                    await self.store.add_user(member, True)  # Save approval

                    # Assume the bot was intended to give the role and move
                    await self.add_role(
                        member, self.config.roles['approved']['ref'])

                    await self.move(member, self.config.server.default_channel)
                else:
                    print(f'{member} response key was invalid')
                    await self.embed.nm_decline_key(member)

                    # Check if someone approved member, inbetween the request
                    if not self.store.is_approved(member):
                        await self.kick(member)
            else:
                print(f'{member} member connecting to the server, '
                      + 'ensuring the user still has the "Approved" role')

                if not self.config.roles['approved']['ref'] in member.roles:
                    print(f'"Approved" role missing for {member}, fixing…')

                    await self.add_role(
                        member, self.config.roles['approved']['ref'])
        except KeyError:
            print(f'{member} tried joining, without a key. Kicking…')
            await self.embed.nm_unregistered_user(member)
            await self.kick(member)

    def has_role(self, member, key):
        """Returns role, if member has it"""
        for role in member.roles:
            # Dynamic role ID is a name
            if self.config.roles[key]['dynamic'] \
               and role.name == self.config.roles[key]['id']:
                return role
            elif role.id == self.config.roles[key]['id']:
                return role
        return None

    def has_bot_role(self, member):
        """Returns role, if member has it"""
        return self.has_role(member, 'bot')

    def has_approved_role(self, member):
        """Returns role, if member has it"""
        return self.has_role(member, 'approved')
