from util import hook
import sys
sys.path += [".."] # heh

import buttifier
import prob

@hook.command
def butt(msg):
    return buttifier.buttify(msg, allow_single=True)

next_butts = {}

@hook.singlethread
@hook.event("PRIVMSG")
def autobutt(_, chan=None, msg=None, bot=None, say=None):
    rate = bot.config.get("butt_rate", 30)

    if chan not in next_butts:
        next_butts[chan] = prob.poissonvariate(rate)
        return

    next_butts[chan] -= 1

    try:
        sent, score = buttifier.score_sentence(msg)

        if next_butts[chan] <= score.sentence():
            result = buttifier.buttify_sentence(sent, score)
            if result:
                next_butts[chan] = prob.poissonvariate(rate)
                say(result)
    except:
        pass
