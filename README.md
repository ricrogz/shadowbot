# ShadowBot 2.0

Project forked from https://github.com/Polsaker/shadowbot, and merged to my own bot, which was just an Xchat plugin. I find this implementation better, as it does not require a 'base' program (just Python 3), and neither an X server. I ported back several features from my plugin:

- Autofight: enemies will be attacked and scanned in order of increasing ¿armouring?.
- Option to disable 'autoplay'.
- Command parsing through the command line or through PRIVMSGs from the 'admin' nick. Issue '$help' to see available commands.
- Increased '#we' checks to improve decision making.
- Store items in bank starting from a programmable index (bank_store_index).
- 'hp_sleep' is now an absolute value (number of HP).
- Reduced screen output (changed main logging command in irc/client.py to 'info'.
- Added functions for massive item pushing and popping in the bank.
- Updating game-bot nick from in-game.
- Major code rewrites.

# Installation & configuration

Just fork the repository and tweak the config.json file to your liking. Most of the values can be changed from the program, so their values are not important.

# Documentation

Run the script and let it play for you. It will keep exploring until your character's HP falls under the indicated 'hp_sleep' value, or the weight you carry goes over 'we_bank' per cent of your max_weight attribute (advice: set it over 100%!, i.e. 120%).

Commands can be given through the command line or throught a PRIVMSG from the nick configured as 'admin'. Issue '$help' to see available commands and their description.

The autoplay loop starts with checking the carried weight. If too much, then the autoplayer goes to the bank and stores 30 items, starting at configured inventory index 'bank_store_index'. Then, weight is checked again, until weight is under the limit.

At this point, HP is checked. If under the configured value, autoplayer will go to the hotel and go to sleep. After sleeping, weight is checked again, restarting the loop.

If neither weight nor HP trigger, then autoplayer goes to explore, and keeps doing this until some trigger goes off. When any of these triggers goes off, autoplayer keeps this plan until reaching the proper destination (i.e. it won't start exploring once overload has been detected, not until player has been to the bank and unloaded).

While walking, if "meeting" someone, the autoplayer will issue the "say_to_folks" action. In fact, it does *not* just say it, it must be a command. This allows to issue, i.e., the '#bye' command to end the conversation.

As mentiones, whene 'encounters' trigger, the autoplayer engages in 'autofight' mode (even when autoplay is disabled), attacking and trying to scan (works only if a scanner is available) enemies ordered by 'armouring', 'level' and relative position (enemies are sorted according to these three parameters).

When using the '$go' command, if the user gives a destination different than 'bank' or 'hotel', the autoplayer will go there and do nothing (i.e. it will stay there until a different command is received), as the only supported events are those happening in these two places. To resume normal operation, just issue any command resulting in autoplayer operation (i.e. '#we', '#hp', '#explore', '#goto hotel', etc).

Everything else is quite straightforward, so that much more documentation is not required.

# TO DO:
- Functions for easier inventory & bank managing.

