import irc.client as client
import logging
import http.server
import time
import _thread
import re

logging.getLogger(None).setLevel(logging.DEBUG)
logging.basicConfig()

hira = client.IRCClient('hira')
freenode = client.IRCClient('freenode')

hira.configure(server = "irc.gizmore.org", port=6668,
                           nick = "Polsaker",
                           ident = "polsaker",
                           gecos = "Butts.")

freenode.configure(server = "irc.freenode.net",
                           nick = "PolsakerClanBot",
                           ident = "PolsakerClanBot",
                           gecos = "BUTTS!")

def on_hWelcome(cli, event):
    #cli.privmsg("NickServ", "ID ivnxfonfymvr")
    cli.privmsg("Lamb3", "#hp")
    
def on_hFelcome(cli, event):
    cli.join("#cobot,##prodigygirl")

def gotoHotel(cli, event):
    cli.privmsg("Lamb3", "#goto hotel")

def gotToTheHotel(cli, event):
    cli.privmsg("Lamb3", "#sleep")

HP_REGEX = re.compile("\002\d+\002-(.+?)\((.+?)\/(.+?)\)")

def on_privnotice(cli, event):
    if event.target != "Lamb3":
        return
    
    if event.arguments[0].endswith("but it seems you know every single corner of it."):
        cli.privmsg("Lamb3", "#hp")
    elif event.arguments[0].startswith("You enter the"):
        if "Hotel" in event.arguments[0]:
            gotToTheHotel(cli, event)
    elif event.arguments[0].startswith("You are ready to go."):
        cli.privmsg("Lamb3", "#exp")
    
    
def on_privmsg(cli, event):
    if event.target != "Lamb3":
        return
    
    if event.arguments[0].startswith("Your parties HP"):
        tx = HP_REGEX.findall(event.arguments[0].replace('Your parties HP: ',''))
        for jug in tx:
            totes = (float(jug[1])/float(jug[2]))*100
            if totes < 40:
                # Si alguien en la party tiene menos del 40% del HP, volvemos al hotel
                gotoHotel(cli, event)
                return
        
        # Si todos están enteros, exploramos.
        cli.privmsg("Lamb3", "#explore")
    elif event.arguments[0].startswith("You are already in"):
        if "Hotel" in event.arguments[0]:
            gotToTheHotel(cli, event)

hira.addhandler("welcome", on_hWelcome)
hira.addhandler("privmsg", on_privmsg)
hira.addhandler("privnotice", on_privnotice)
freenode.addhandler("welcome", on_hFelcome)
hira.connect()
#freenode.connect()

while True:
    if hira.connected is False:
        hira.connect()
    
    if freenode.connected is False:
        pass
        #freenode.connect()
        
    time.sleep(1)
