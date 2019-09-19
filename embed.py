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

# pylint: disable=redefined-builtin, import-error
import discord
import icons
import strings as st

from utils import RED, YELLOW, GREEN, make_print


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Embed', *args, **kwargs)


def get_avatar(member):
    """Returns default avatar, if custom doesn't exist"""
    if member.avatar_url:
        return member.avatar_url
    return member.default_avatar_url


class Embed:
    """Methods for sending embed messages to client"""
    def __init__(self, client, config, args):
        """Instantiate"""
        self.client = client
        self.config = config
        self.args = args
        self.timeout = ''
        self.kick_message = ''

        if args.timeout_time > 0 and args.kick:
            self.timeout = '\n\n' + st.MJ_SECONDS.format(args.timeout_time)
            self.kick_message = st.MJ_DISCONNECTED_NOW

    async def nm_first_msg(self, channel, role):
        """First hey message.

        Dispatched after attaining Bot role
        Message will notify of missing permissions for kick, ban, manage roles
        """
        perms = role.permissions
        complete_message = st.GOT_BOT_ROLE
        missing_perms = ''

        def add(add_to, string):
            """Append to string with comma, if first string is not empty"""
            if add_to != '':
                return f', {string}'
            return string

        # Check roles
        if not perms.kick_members:
            missing_perms += add(missing_perms, 'kick')
        if not perms.ban_members:
            missing_perms += add(missing_perms, 'ban')
        if not perms.manage_roles:
            missing_perms += add(missing_perms, 'manage roles')

        if missing_perms == '':
            complete_message += st.BOT_ROLE_HAS_PERMS
        else:
            complete_message += st.BOT_ROLE_LACKS_PERMS.format(missing_perms)

        embed = discord.Embed(
            title=self.client.user.name,
            description=complete_message,
            colour=self.config.his_color
        )

        embed.set_thumbnail(url=self.config.get_avatar())
        embed.set_footer(
            text=self.config.repo,
            icon_url=self.config.get_avatar()
        )

        await self.client.send_message(channel, embed=embed)

    async def nm_unregistered_user(self, member):
        """Sends a message to member, pointing that it needs a key"""
        embed = discord.Embed(
            title=self.config.server.name,
            description=st.MJ_IDLE,
            colour=YELLOW
        )

        embed.set_thumbnail(url=self.config.get_avatar())
        await self.client.send_message(member, embed=embed)

    async def nm_request_key(self, channel, member):
        """Sends 2 line message, asking for a member key"""
        try:
            embed = discord.Embed(
                title=self.config.server.name + ' - ' + st.KV_TITLE,
                description=icons.EXCALAMTION + '  **'
                + st.MJ_INFO.format(member) + '**',
                colour=YELLOW
            )

            if self.args.timeout_time > 0 and self.args.kick:
                embed.add_field(
                    name=st.KV_TIMEOUT,
                    value=st.KV_KICK_NOTICE.format(
                        self.args.timeout_time)
                )

            await self.client.send_message(channel, embed=embed)
        except AttributeError:
            await self.sent_from_wrong_channel(channel)

    async def nm_accept_key(self, member, key):
        """Sends an acceptance message, with an included discord bug warning"""
        embed = discord.Embed(
            title=self.config.server.name + ' -  ' + st.KV_TITLE,
            colour=GREEN
        )

        embed.add_field(
            name=st.KV_USER,
            value=f'{member}, {member.name}',
            inline=False
        )

        embed.add_field(
            name=st.KV_KEY,
            value=str(key),
            inline=False
        )

        embed.add_field(
            name=st.KV_STATUS,
            value=st.KV_APPROVED + '  ' + icons.GREEN_CHECKMARK,
            inline=False
        )

        embed.set_thumbnail(
            url=self.config.safe_get_user_avatar(member))

        embed.set_footer(text=st.MJ_WARNING)
        await self.client.send_message(member, embed=embed)

    async def nm_decline_key(self, member):
        """Sends a message, that the key was invalid"""
        embed = discord.Embed(
            title=self.config.server.name + ' - ' + st.KD_TITLE,
            colour=RED
        )

        embed.add_field(
            name=st.KV_USER,
            value=f'{member}, {member.name}',
            inline=False
        )

        embed.add_field(
            name=st.KV_KEY,
            value=f'*{st.KV_KEY_HIDDEN}*',
            inline=False
        )

        embed.add_field(
            name=st.KV_STATUS,
            value=st.KV_DECLINED + '  ' + icons.CROSS,
            inline=False
        )

        embed.set_thumbnail(
            url=self.config.safe_get_user_avatar(member))

        await self.client.send_message(member, embed=embed)

    async def nm_approved(self, channel, member, status):
        """Sends the profile status of the member"""
        colour = RED

        if status:
            colour = GREEN

        try:
            # Member colour not available, if sent from a regular channel
            if isinstance(channel, discord.Channel):
                colour = member.colour
        except AttributeError:
            pass  # Use default color

        embed = discord.Embed(
            title=self.config.server.name + ' - ' + str(member),
            colour=colour
        )

        embed.add_field(
            name=st.KV_USER,
            value=f'{member}, {member.name}',
            inline=False
        )

        embed.add_field(
            name=st.KV_KEY,
            value=f'*{st.KV_KEY_HIDDEN}*',
            inline=False
        )

        if status:
            embed.add_field(
                name=st.KV_STATUS,
                value=st.KV_APPROVED + '  ' + icons.GREEN_CHECKMARK,
                inline=False
            )
        else:
            embed.add_field(
                name=st.KV_STATUS,
                value=st.KV_NOT_APPROVED + '  ' + icons.CROSS,
                inline=False
            )

        embed.set_thumbnail(url=get_avatar(member))

        # After embed is ready, send it to the channel
        print(f'Sending am_approved embed to {member}')
        await self.client.send_message(channel, embed=embed)

    async def nm_does_not_exist(self, channel, who):
        """User does not exist message"""
        await self.send_basic_template(
            channel,
            st.NOT_FOUND.format(str(who)),
            RED
        )

    async def nm_not_found(self, channel, who):
        """User not found message"""
        await self.send_basic_template(
            channel,
            st.COULD_NOT_FIND.format(str(who)),
            RED
        )

    async def nm_you_were_deleted(self, who):
        """Send message to a user, that he was deleted"""
        message = st.YOU_WERE_DELETED

        if self.args.kick:
            message += ', ' + st.DISCONNECTING_YOU_LOWER

        await self.send_basic_template(who, message, YELLOW)

    async def nm_deleted(self, channel, who):
        """Sends deleted succesfully"""
        await self.send_basic_template(
            channel,
            st.DELETE_SUCCESS.format(str(who)),
            GREEN
        )

    async def nm_add(self, channel, member, key, approved=False):
        """Sends an added message, with the key"""
        action = 'Adding'
        color = YELLOW
        status = st.KV_ADDED

        if approved:
            action = 'Approving'
            color = GREEN
            status = st.KV_APPROVED + '  ' + icons.GREEN_CHECKMARK

        embed = discord.Embed(
            title=self.config.server.name,
            description=action + f' {member}',
            colour=color
        )

        embed.add_field(
            name=st.KV_USER,
            value=f'{member}, {member.name}',
            inline=False
        )

        embed.add_field(
            name=st.KV_KEY,
            value=str(key),
            inline=False
        )

        embed.add_field(
            name=st.KV_STATUS,
            value=status,
            inline=False
        )

        embed.set_thumbnail(
            url=self.config.safe_get_user_avatar(member))

        await self.client.send_message(channel, embed=embed)

    async def nm_approve(self, channel, who, key):
        """Sends an added message, with the key"""
        await self.send_basic_template(
            channel,
            st.ADDED.format(str(who), key),
            GREEN
        )

    async def nm_already_approved(self, channel, who, key):
        """Sends user already approved message"""
        await self.send_basic_template(
            channel,
            st.ALREADY_APPROVED.format(str(who), key),
            YELLOW
        )

    async def nm_not_approved(self, channel):
        """Sends a kick message, when not approved"""
        message = st.SW_NOT_APPROVED.format(self.config.server.name)

        if self.args.kick:
            message += '\n' + st.DISCONNECTING_YOU_UPPER

        await self.send_basic_template(channel, message, RED)

    async def sent_from_wrong_channel(self, channel):
        """Send wrong channel message"""
        await self.send_basic_template(
            channel, st.WRONG_CHANNEL, YELLOW)

    async def hey(self, message):
        """Replays a Hey! message"""
        colour = GREEN

        try:
            colour = self.config.roles['bot']['ref'].colour
        except AttributeError:
            pass  # Use default color

        await self.send_basic_template(
            message.channel, st.HEY.format(message.author.id), colour)

    async def send_basic_template(self, channel, message, colour=None):
        """Basic template for repetative messages"""
        if not colour:
            colour = RED

        embed = discord.Embed(
            title=self.config.server.name,
            description=message,
            colour=colour
        )

        await self.client.send_message(channel, embed=embed)
