[//]: #tech "Python, Asyncio, Aiohttp, Discord.py"
[anim]: https://github.com/volskaya/norman/raw/master/data/norman_0.gif

Norman is a house keeping bot, intended for private servers, that stores keys of
users and requests the user to validate them, upon login.

The bot has an API interface for setting those keys from your web server or
just accessing regular DB info via json.

![][anim]

_Currently the bot only supports a local file DB_

## Behavior

Bot holds its own DB of members. Every user will have an empty entry created,
under their ID, whenever they join the server.

If the user has an unapproved key, bot will send out a private message,
requesting that key to be provided within `--timeout` or 60 seconds.
After the key is validated, user will receive `approved` role, if not, kicked.

###### DB entry consists of:

- ID <String>
- Name <String>, _username, not nickname_
- avatar_url <String>
- key <String>
- approved <Boolean>
- valid <Boolean>

## Commands

| Command                  | Description                                                                                                                                                                                                                                               |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| nm!add username / ID     | Prepare a DB entry and generate a key. If user is not online, ID will be used and the DB entry will be invalidated to force an update, the next time bot meets the user. If user is online, the bot will send a message to validate users key right away. |
| nm!approve username / ID | Same as nm!add, except the user will be approved automatically.                                                                                                                                                                                           |
| nm!remove username / ID  | Zero DB entry, remove `approved` role, kick from the server.                                                                                                                                                                                              |
| nm!am                    | Returns your account status.                                                                                                                                                                                                                              |
| nm!hey                   | Bot will say hay to you, if you have permissions to interact with it.                                                                                                                                                                                     |

_Note:_ Server owner has access to the bot by default.

## Arguments

| Arg                     | Description                                                                   |
| ----------------------- | ----------------------------------------------------------------------------- |
| -h, --help              | show help message and exit                                                    |
| -c, --config ./config_2 | override default config location                                              |
| -b, --backend name      | which backend to use _(Currently only supports "file")_                       |
| -i, --info              | log into the bot and print out servers, roles or any other info the bot needs |
| -t, --timeout 60        | seconds before kick at key validation. 0 means _off_                          |
| -k, --no-kick           | disable kicks                                                                 |
| --no-admin-role         | ignore admin role permissions                                                 |
| --ip 127.0.0.1          | API server address                                                            |
| --port 8080             | API server port                                                               |

## Config Format

Your `token` and `server` need to be specified in `config.json`, along with role
id's for `admin`, `bot`, `approved` roles. It is _important_, that id's are
declared as _integers_, meaning no `""` around the numbers, because that's how
the bot differentiates between discord.Objects and regular ID references.

`server_ip` and `server_port` refer to the inbuilt API for fetching or setting
user info from your web page.

`owner` refers to the person, hosting the bot, not to the server owner.

- `admin` role can be left blank, if you don't want to give them any permissions.
- `bot` is the only role, the bot is gonna track for permissions. If this is
  blank, its gonna emit error messages.
- `approved` is the role, that's assigned, after a member has validated its
  assigned key with the bot. Your servers default role should forbid anyone from
  seeing, talking or accessing other channels or server info in any way, if
  you're using this bot.

###### Template

```json
{
  "name": "Norman",
  "avatar": "./data/norman.jpg",
  "server_ip": "127.0.0.1",
  "server_port": "8080",
  "token": "",
  "owner": 111111111111111111,
  "server": 222222222222222222,
  "role": {
    "admin": 333333333333333333,
    "bot": 444444444444444444,
    "approved": 555555555555555555
  }
}
```

## Server Setup

###### You need to make a few changes to your server, to make use of the bot.

Your servers `@everyone` role should have all its permissions revoked. Create a
new role for `approved`, name it whatever you want and mimic roles from
`@everyone`. Also disable `Display role members separately from online members`.

Remove every permission from `@everyone` so new players can't do anything
without the `approved` role.

Create a role `bot`, name it whatever you want. Give it permissions to:

- Kick Members
- Ban Members _(For swiping the ban list and revoke keys for banned players,
  while the bot was offline)_
- Manage Roles
- Move Members

Write down its id's in `config.json` as _integers_.

## Api

Besides manual chat commands, you can also access the bot from your back-end.
By default the server is listening on `127.0.0.1:8080`, but you can change this with
`--ip` and `--port`

All of the routes return a json object for that user, except `/user/remove/`

| Route                  | Type | Response                                                                    |
| ---------------------- | ---- | --------------------------------------------------------------------------- |
| /user/{id}             | GET  | Retrieve user DB entry by their ID                                          |
| /user/id/{id}          | GET  | Same as /user/{id}                                                          |
| /user/name/{name}/{id} | GET  | Retrieve user by their discord username, eg. Nani#1234                      |
| /user/add/{id}         | GET  | Generate a DB entry for ID. If user is on, it will ask it to verify the key |
| /user/approve/{id}     | GET  | Same as `add`, but also approves the user                                   |
| /user/remove/{id}      | GET  | Zero out the users DB entry, but don't completely delete it                 |

## Installation

1. Clone the repository

```sh
git clone https://github.com/volskaya/norman
```

2. Cd into `norman` folder and edit `config.json`
3. Launch with

```sh
python norman.py

# --help for help
python norman.py --help
```
