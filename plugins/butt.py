from util import hook
import sys
sys.path += [".."] # heh

import buttifier
import prob

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
    rate = bot.config.get("butt_rate", 30)

    if chan[0] == '#':
        if chan not in next_butts:
            next_butts[chan] = prob.poissonvariate(rate)
            return
        next_butts[chan] -= 1

    sent, score = buttifier.score_sentence(msg)

    if score.sentence() == 0:
        return

    if chan[0] != '#' or next_butts[chan] <= score.sentence():
        result = buttifier.buttify_sentence(sent, score)
        next_butts[chan] = prob.poissonvariate(rate)
        say(result)
