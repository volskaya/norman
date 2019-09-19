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
import shelve
import discord

from utils import (
    SHELVE_PATH,
    make_print,
    make_key,
    is_id,
    get_avatar_url
)


def print(*args, **kwargs):
    """Prefix builtin print"""
    return make_print('Store', *args, **kwargs)


def make_entry(
        user_id=None,
        name=None,
        avatar_url=None,
        key=None,
        approved=False,
        valid=False
):
    """Template for the DB entry"""
    return {
        'id': user_id,
        'name': name,
        'avatar_url': avatar_url,
        'key': key,
        'approved': approved,
        'valid': valid
    }


class Store:
    """Store type class around self.shelve

    Approve new users with "!approve Someone#1245" from discord with admin
    permissions everytime a user joins, DB is queried to check if the
    user.id.approved == True

    Dictionary follows the format of key<Long>: {
                                            name: String,
                                            approved: Boolean,
                                            key: String
                                          }
    """
    def __init__(self):
        self.shelve = shelve.open(str(SHELVE_PATH))
        print(f'shelve opened at {str(SHELVE_PATH)}, size: {len(self.shelve)}')

    def sync(self):
        """Sync shortcut"""
        self.shelve.sync()

    async def remove_user(self, target):
        """Removes user from the shelf"""
        try:
            for key in self.shelve:
                if self.shelve[key]['name'] == str(target):
                    print(f'Invalidating DB entry, ID - {key}')
                    self.shelve[key] = make_entry()
                    self.sync()
                    return True
        except KeyError:
            pass
        return False

    async def remove_user_by_id(self, user_id):
        """Removes user, using their ID"""
        try:
            self.shelve[str(user_id)] = make_entry()  # Empty entry
            self.sync()
            return True
        except KeyError:
            pass
        return False

    async def add_user(self, user, approve=False):
        """Stores user in the shelf """
        using_id_only = False
        name = None
        user_id = None
        avatar_url = None

        try:
            int(user)
            user_id = str(user)
            using_id_only = True
        except ValueError:  # Not an ID
            user_id = user.id
            name = str(user)
            avatar_url = get_avatar_url(user)
            str(user)
        except TypeError:
            user_id = user.id
            name = str(user)
            avatar_url = get_avatar_url(user)
            str(user)

        # Check if the ID already exists, if true, don't rebuild anything,
        # just assign $approve
        try:
            entry = self.get_user(user)  # NOTE: User can also be an ID
            entry['approved'] = approve
            print(f'An entry for {user} already exists, '
                  + f'switching approved to {approve}')

            # Somethimes DB entry is invalidated, regenerate its key
            if not entry['key']:
                print(f'User does not have a key, assigning it now')
                entry['key'] = make_key()

            if not using_id_only:
                try:
                    print(f'Also forcing an update for {name}…')
                    entry = self.update_user_entry(user, entry)
                except AttributeError:
                    pass  # Update later

            self.shelve[user_id] = entry
            self.sync()
            return self.shelve[user_id]
        except KeyError:
            pass

        self.shelve[user_id] = make_entry(
            user_id, name, avatar_url, make_key(), approve)

        print(f'Manually approved user {name}, ID - {user_id}')

        self.shelve.sync()
        return self.shelve[user_id]

    def make_user_blank_entry(self, member):
        """Creates an empty entry for a new user"""
        try:
            if self.shelve[member.id]:
                return False
            return True
        except KeyError:  # If it doesn't create a new entry
            self.shelve[member.id] = make_entry(
                member.id, member.name, get_avatar_url(member))
            return True

    def get_user_key(self, member):
        """Returns true, if user has key"""
        try:
            entry = self.shelve[member.id]

            return entry['key']  # Will be NoneType, if no key
        except KeyError:
            pass
        return None

    def is_valid(self, member):
        """Returns true if DB entry is valid"""
        try:
            return self.get_user(member)['valid']
        except KeyError:
            return False

    def is_approved(self, member):
        """Returns approved bool associated with member.id"""
        user_id = str(member)

        if isinstance(member, (discord.User, discord.Member)):
            user_id = member.id

        try:
            entry = self.shelve[user_id]

            if entry['approved']:
                return True
        except KeyError:  # Unknown member - not approved
            pass
        return False

    def get_user(self, user):
        """Fetches shelve key by user.id"""
        user_id = None

        # If a user object provided, pull the ID from that
        if isinstance(user, (discord.Member, discord.User)):  # Lookup by obj
            user_id = user.id
        elif is_id(user):  # Lookup by ID
            user_id = str(user)
        elif isinstance(user, str):  # Lookup by name
            for key in self.shelve:
                if self.shelve[key]['name'] == user:
                    return self.shelve[key]

        try:
            return self.shelve[user_id]
        except KeyError:
            raise

    def get_user_id(self, name):
        """Iterates over the DB and returns ID of matched name"""
        for i in self.shelve:
            if self.shelve[i]['name'] == name:
                return i
        # Else raise a KeyError
        raise KeyError('Name not found in the database')

    def does_key_match(self, user, key):
        """Compares the strings of key and entry['key']"""
        try:
            entry = self.get_user(user)

            if key == entry['key']:
                return True
        except KeyError:
            pass
        return False

    def invalidate(self, member, keep_key=False):
        """Invalidate members DB entry"""
        print(f'Invalidating {member} DB entry')

        using_id_only = True
        user_id = member

        if isinstance(member, (discord.Member, discord.User)):
            using_id_only = False
            user_id = member.id

        key = None

        if keep_key:
            key = self.shelve[user_id]['key']
            print(f'    Keeping the key - {key}')

        # id, name, key, approved, valid
        if using_id_only:
            self.shelve[user_id] = make_entry(
                user_id, None, None, key, False)
        else:
            self.shelve[user_id] = make_entry(
                member.id,
                member.name,
                get_avatar_url(member),
                key,
                False
            )

        self.sync()

    def update_name(self, user_id, new_name):
        """Updates the name of ID entry

        Return success True/False
        """
        try:
            entry = self.shelve[user_id]
            entry['name'] = new_name
            self.shelve[user_id] = entry
            self.sync()

            return True
        except KeyError:
            print(f'Tried to update a nonexistent user - {user_id}')

        return False

    def is_new_name(self, user_id, current_name):
        """Returns true, if current user ID name does
        not match with the one in the DB"""
        try:
            return self.shelve[user_id]['name'] != current_name
        except KeyError:
            print(f'Tried to compare a nonexistent ID entry - {user_id}')
        return True

    def get_user_by_id(self, user_id):
        """Fetches DB entry by ID"""
        try:
            return self.shelve[user_id]
        except KeyError:
            return None

    def update_user_entry(self, member, entry=None):
        """Updates an invalidated user entry

        Currently updates only id, name, avatar_url
        """
        if not isinstance(member, (discord.Member, discord.User)):
            raise AttributeError('store.update_user_entry() expected '
                                 + 'discord.Member or discord.User')

        entry_provided = True

        print(f'Updating entry ID - {member.id}')

        # Support passing in an entry, to avoid useless query
        if not entry:
            entry = self.get_user(member)
            entry_provided = False

        entry['id'] = member.id
        entry['name'] = str(member)
        entry['avatar_url'] = get_avatar_url(member)
        entry['valid'] = True

        # If an entry provided from an outter scope, leave the
        # update duty to that
        if entry_provided:
            self.shelve[member.id] = entry
            self.sync()

        return entry
