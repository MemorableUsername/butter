from util import hook
import sys
sys.path += [".."] # heh

import buttifier
import random
import time

@hook.command
def butt(msg, me=None):
    try:
        return buttifier.buttify(msg, min_words=1)
    except:
        me("can't butt the unbuttable!")
        raise

next_butts = {}

# TODO: don't fire this when someone ran .butt!
@hook.singlethread
@hook.event("PRIVMSG")
def autobutt(_, chan=None, msg=None, bot=None, say=None):
    butt_config = bot.config["butt"] or {}
    mean      = butt_config.get("rate_mean", 300)
    sigma     = butt_config.get("rate_sigma", 60)
    min_score = butt_config.get("min_score",   4)
    now = time.time()

    if chan[0] == '#':
        # public channel
        if chan not in next_butts or next_butts[chan] < now:
            sent, score = buttifier.score_sentence(msg)
            if score.sentence() < min_score:
                return

            say(buttifier.buttify_sentence(sent, score))
            next_butts[chan] = random.normalvariate(mean, sigma) + now
    else:
        # private message
        try:
            say(buttifier.buttify(msg))
        except:
            pass
