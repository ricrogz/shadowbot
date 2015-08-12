import irc.client as client
import logging
import json
import time
import _thread
import re

logging.getLogger(None).setLevel(logging.DEBUG)
logging.basicConfig()

config = json.load(open('config.json'))

hira = client.IRCClient('client')

hira.configure(server = config['server'], port=config['port'],
                           nick = config['nick'],
                           ident = config['nick'],
                           gecos = "Butts.")

hira.send("PASS " + config['password'])

def on_hWelcome(cli, event):
    cli.privmsg("Lamb3", "#we")
    
def gotoHotel(cli, event):
    cli.privmsg("Lamb3", "#goto hotel")

def gotoBank(cli, event):
    cli.privmsg("Lamb3", "#goto bank")

def gotToTheHotel(cli, event):
    cli.privmsg("Lamb3", "#sleep")

def say(cli, msg):
    cli.privmsg("Lamb3", "[Mr. Roboto] {0}".format(msg))

def gotToTheBank(cli, event):
    for _ in range(30):
        cli.privmsg("Lamb3", "#push 3")

HP_REGEX = re.compile("\002\d+\002-(.+?)\((.+?)\/(.+?)\)")
WE_REGEX = re.compile("\002\d+\002-(.+?)\((.+?)kg\/(.+?)kg\)")

def on_privnotice(cli, event):
    if event.target != "Lamb3":
        return
    
    if event.arguments[0].endswith("but it seems you know every single corner of it."):
        cli.privmsg("Lamb3", "#we")
    elif event.arguments[0].startswith("You enter the"):
        if "Hotel" in event.arguments[0]:
            gotToTheHotel(cli, event)
        elif "Bank" in event.arguments[0]:
            gotToTheBank(cli, event)
    elif event.arguments[0].startswith("You are ready to go."):
        cli.privmsg("Lamb3", "#exp")
    elif event.arguments[0].startswith("You meet"):
        cli.privmsg("Lamb3", config['sayToFolks'])
    
    
def on_privmsg(cli, event):
    if event.target != "Lamb3":
        return
    
    if event.arguments[0].startswith("Your parties HP"):
        tx = HP_REGEX.findall(event.arguments[0].replace('Your parties HP: ',''))
        for jug in tx:
            totes = (float(jug[1])/float(jug[2]))*100
            if totes < 40:
                say(cli, "Yendo al hotel por que {0} está muriendose".format(jug[0]))
                # Si alguien en la party tiene menos del 40% del HP, volvemos al hotel
                gotoHotel(cli, event)
                return
        
        # Si todos están enteros, exploramos.
        cli.privmsg("Lamb3", "#explore")
    if event.arguments[0].startswith("Your party carries"):
        tx = WE_REGEX.findall(event.arguments[0].replace('Your party carries',''))
        for jug in tx:
            totes = (float(jug[1])/float(jug[2]))*100
            if totes > 100:
                say(cli, "Yendo al banco por que {0} está muy gordo/a".format(jug[0]))
                # Si alguien es muy gordo, vamos al banco
                gotoBank(cli, event)
                return
        cli.privmsg("Lamb3", "#hp")
    elif event.arguments[0].startswith("You are already in"):
        if "Hotel" in event.arguments[0]:
            gotToTheHotel(cli, event)
        elif "Bank" in event.arguments[0]:
            gotToTheBank(cli,event)

hira.addhandler("welcome", on_hWelcome)
hira.addhandler("privmsg", on_privmsg)
hira.addhandler("privnotice", on_privnotice)
hira.connect()

while True:
    if hira.connected is False:
        hira.send("PASS " + config['password'])
        hira.connect()
        
    time.sleep(1)
