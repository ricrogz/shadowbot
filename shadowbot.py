#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import json
import time
import logging
import _thread
import irc.client as client

ENEMY_STATS_REGEX = re.compile(r'\(([\-\.\d]+)m\)\(L(\d+)\((\d+)\)\)')
HP_REGEX = re.compile(r'\d+-(.+?)\((.+?)/(.+?)\)')
WE_REGEX = re.compile(r'\d+-(.+?)\((.+?)kg/(.+?)kg\)')
QUIT_SIGNAL = False

authlist = set()
enemies = []
task = None


def on_whoisuser_reply(cli, event):
    if event.arguments[0] == config['nickserv'] and \
            event.arguments[2].startswith("anope.irc.wechall.net"):
        authlist.add(event.arguments[0])
        check_auth(cli, event)


def on_registerednick(cli, event):
    if event.arguments[0] == config['gamebot'] and \
            event.arguments[1].startswith("is a registered nick"):
        authlist.add(event.arguments[0])
        check_auth(cli, event)


def on_serverconnected(cli, _):
    cli.send('away :{0}'.format(config['msg_away']))


def on_privnotice(cli, event):
    if event.target.lower() == config['nickserv'].lower() and \
       event.arguments[0].startswith("This nickname is registered and protected."):
        cli.whois(config['nickserv'])
        cli.whois(config['gamebot'])
        return
    elif event.target != config['gamebot']:
        return


def on_privmsg(cli, event):
    global task

    msg = event.arguments[0].replace('\x02', '')

    # Always autofight
    if event.target == config['gamebot']:
        if "You ENCOUNTER" in msg:
            fight_start(cli, event)
            return
        elif " and killed them with " in msg:
            fight_next(cli, event)
            return
    # Pass user commands to the processing function
    elif event.target == config['admin']:
        process_user_input(cli, msg, True)

    # If autoplay is enabled and input comes from bot, process it
    if config['autoplay'] and event.target == config['gamebot']:

        if msg.startswith("Your parties HP"):
            for jug in HP_REGEX.findall(msg):

                # This one is absolute!
                # totes = (float(jug[1])/float(jug[2]))*100

                # Si alguien en la party tiene poco HP,
                # y no hay ya un destino, volvemos al hotel
                if float(jug[1]) < config['hp_sleep'] and goto_destination('hotel', cli, event):
                    cli.privmsg(config['gamebot'], "Yendo al hotel por que {0} está muriendose".format(jug[0]))
                    return

            # Si todos están enteros, exploramos.
            goto_mission(cli, event)

        elif msg.startswith("Your party carries"):
            for jug in WE_REGEX.findall(msg):
                totes = (float(jug[1])/float(jug[2]))*100.

                # Si alguien es muy gordo,
                # y no hay ya un destino, vamos al banco
                if totes > config['we_bank'] and goto_destination('bank', cli, event):
                    cli.privmsg(config['gamebot'], "Yendo al banco por que {0} está muy gordo/a".format(jug[0]))
                    return

            # Si el peso está bien, comprobamos la salud
            cli.privmsg(config['gamebot'], "#hp")

        elif msg.endswith("but it seems you know every single corner of it."):
            cli.privmsg(config['gamebot'], "#we")
        elif msg.startswith("You are ready to go."):
            cli.privmsg(config['gamebot'], "#we")
        elif msg.startswith("You meet"):
            cli.privmsg(config['gamebot'], config['say_to_folks'])
        elif msg.startswith("You are already in") or msg.startswith("You enter the"):

            # Reset task
            if task in msg.lower():
                task = None

            if "Hotel" in msg:
                got_to_hotel(cli, event)
            elif "Bank" in msg:
                got_to_bank(cli, event)


def parse_config(cli, cfg, value, cast):
    try:
        config[cfg] = cast(value)
    except ValueError:
        pass
    json.dump(config, open('config.json', 'w'), indent=2, sort_keys=True)
    cli.privmsg(config['gamebot'], "{0} set to '{1}'".format(cfg.upper(), config[cfg]))


def split_cmdline(cmd):
    ret = cmd.split()
    return (ret[0], ret[1:]) if len(ret) > 1 else (ret[0], [''])


def check_auth(cli, _):

    def make_auth():
        cli.privmsg(config['nickserv'], "IDENTIFY {0}".format(config['password']))
        cli.privmsg(config['gamebot'], ".login {0}".format(config['password']))

    if config['gamebot'] in authlist and config['nickserv'] in authlist:
        hira.removehandler("whoisuser", on_whoisuser_reply)
        hira.removehandler("registerednick", on_registerednick)

        hira.addhandler("privmsg", on_privmsg)

        make_auth()

        cli.privmsg(config['gamebot'], "#we")


def goto_destination(destination, cli, _, forced=False):
    global task
    if task is None or forced:
        task = destination.lower()
        if config['teleport']:
            cli.privmsg(config['gamebot'], "#cast teleport {0}".format(task))
            cli.privmsg(config['gamebot'], "#enter")
        else:
            cli.privmsg(config['gamebot'], "#goto {0}".format(task))
        return True
    return False


def goto_mission(cli, _):
    global task
    if task is None:
        cli.privmsg(config['gamebot'], "#explore")
        return True
    else:
        cli.privmsg(config['gamebot'], '#goto {0}'.format(task))
    return False


def got_to_hotel(cli, _):
    cli.privmsg(config['gamebot'], "#sleep")


def got_to_bank(cli, _):
    push_items(cli)
    cli.privmsg(config['gamebot'], "#we")


def push_items(cli, num_items=30, start_index=None):
    pos = config['bank_store_index'] if start_index is None else start_index
    for _ in range(num_items):
        cli.privmsg(config['gamebot'], "#pushall {0}".format(pos))
    if config['autoplay']:
        wait_time = num_items if num_items > 5 else 5
        time.sleep(wait_time)


def pop_items(cli, num_items=30, start_index=None):
    pos = 1 if start_index is None else start_index
    cli.privmsg(config['gamebot'], "#popall {0}-{1}".format(pos, pos + num_items - 1))


def fight_start(cli, event):
    global enemies
    enemies = []
    gang = event.arguments[0].replace('\x02', '')

    for enemy in gang.split(" ")[2:]:
        lvls = ENEMY_STATS_REGEX.search(enemy)
        if lvls:
            enemy_num = int(enemy.split("-", 1)[0])
            # First order parameter: armouring; 2nd: level; 3rd: distance
            item = (int(lvls.group(3)), int(lvls.group(2)), abs(float(lvls.group(1))), int(enemy_num), enemy)
            enemies.append(item)
    enemies.sort()
    cli.privmsg(config['gamebot'], "Luchando contra:")
    for enemy in enemies:
        cli.privmsg(config['gamebot'], "    {0}".format(str(enemy)))
    fight_next(cli, event)


def fight_next(cli, _):
    global enemies
    if len(enemies):
        enemy = enemies.pop(0)
        cli.privmsg(config['gamebot'], "#attack {0}".format(enemy[3]))
        cli.privmsg(config['gamebot'], "#use scanner {0}".format(enemy[3]))
    else:
        cli.privmsg(config['gamebot'], "#we")


def process_user_input(cli, cmdline, priv=False):
    global task

    cmd, args = split_cmdline(cmdline)
    l_cmd = cmd.lower()
    l_args = list(map(lambda l: l.lower(), args))

    # Check if we gave a bot command. If not, issue PRIVMSG with content
    if l_cmd == '$help':
        msg = "\n\n" \
              "$go (text):                     Force going to given destination.\n" \
              "$show_task:                     Show current detination.\n" \
              "$reset_task:                    Reset current detination.\n" \
              "$autoplay [off/on/0/1]:         Switch/enable/disable autoplay bot.\n" \
              "$set_bank_store_index (int):    Set index from which to store in bank.\n" \
              "$set_say_to_folks (text):       Set words to say to npcs on meeting.\n" \
              "$set_gamebot (text):            Set nick of game bot.\n" \
              "$set_hp_sleep (int):            Set hp value to return to hotel.\n" \
              "$set_we_bank (int):             Set weight % to store items in bank.\n" \
              "$push_items [num] [inv_index]:  Store 'num' items starting from 'inv_index'" \
              " or bank_store_index as default.\n" \
              "$pop_items [num] [bank_index]:  Retrieve 'num' items starting from 'bank_index'" \
              " or first as default.\n" \
              "$raw (text):                    Send raw command to server.\n\n" \
              "$quit:                          Disconnect from irc and exit program.\n\n" \
              "Any other command will be sent to {0} as PRIVMSG.\n\n".format(config['gamebot'])

        if priv:
            cli.privmsg(config['admin'], msg)
        else:
            print(msg)

    elif l_cmd == '$go':
        try:
            goto_destination(args[0], cli, None, True)
        except IndexError:
            pass

    elif l_cmd == '$show_task':
        if task is None:
            cli.privmsg(config['gamebot'], "Currently going nowhere.")
        else:
            cli.privmsg(config['gamebot'], "Currently going to '{0}'.".format(task))

    elif l_cmd == '$reset_task':
        task = None
        cli.privmsg(config['gamebot'], 'Destination has been reset.')

    elif l_cmd in ['$autoplay', '$teleport', ]:
        if l_args[0] in ['off', '0', ]:
            config[l_cmd[1:]] = False
        elif l_args[0] in ['on', '1', ]:
            config[l_cmd[1:]] = True
        else:
            config[l_cmd[1:]] = not config[l_cmd[1:]]
        json.dump(config, open('config.json', 'w'), indent=2, sort_keys=True)
        cli.privmsg(config['gamebot'], "{0} is {1}".format(l_cmd[1:].upper(), "ON" if config['autoplay'] else "OFF"))

    elif l_cmd in ['$set_bank_store_index', '$set_hp_sleep', '$set_we_bank', ]:
        parse_config(cli, l_cmd[5:], args[0], int)

    elif l_cmd in ['$set_say_to_folks', ]:
        parse_config(cli, l_cmd[5:], " ".join(args), str)

    elif l_cmd in ['$set_gamebot', ]:
        parse_config(cli, l_cmd[5:], args[0], str)

    elif l_cmd == '$push_items':
        num = 30
        idx = config['bank_store_index']
        try:
            num = int(args[0])
            idx = int(args[1])
        except ValueError:
            pass
        push_items(cli, num, idx)

    elif l_cmd == '$pop_items':
        num = 30
        idx = 1
        try:
            num = int(args[0])
            idx = int(args[1])
        except ValueError:
            pass
        pop_items(cli, num, idx)

    elif l_cmd == '$raw' and args[0] != '':
        cli.send(" ".join(args), urgent=True)

    elif l_cmd == '$quit':
        raise KeyboardInterrupt

    elif cmdline:
        cli.privmsg(config['gamebot'], cmdline)


def connection_check():
    while not QUIT_SIGNAL:
        if not hira.connected:
            hira.connect()
        time.sleep(1)


if __name__ == '__main__':

    # Prepare logger
    logging.getLogger(None).setLevel(logging.INFO)
    logging.basicConfig()

    # Load configuration file
    config = json.load(open('config.json'))

    # Create irc connection
    hira = client.IRCClient('')
    hira.configure(server=config['server'],
                   port=config['port'],
                   nick=config['nick'],
                   ident=config['nick'],
                   # gecos="Butts."
                   )

    # Register basic event processing
    hira.addhandler("privnotice", on_privnotice)
    hira.addhandler("whoisuser", on_whoisuser_reply)
    hira.addhandler("registerednick", on_registerednick)
    hira.addhandler("youruuid", on_serverconnected)

    # Start a backgroudn thread checking that the connection is alive
    _thread.start_new_thread(connection_check, ())

    # Console reading loop
    while True:

        # Check for Ctrl-C; clean up and exit if found
        try:

            line = sys.stdin.readline().strip()

            # Pass inputo to handler function (only if not empy)
            if line:
                process_user_input(hira, line)

        except KeyboardInterrupt:
            QUIT_SIGNAL = True
            hira.disconnect(config['msg_quit'])
            break
