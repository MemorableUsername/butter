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
def autobutt(args, bot=None, say=None):
    channel, msg = args
    rate = bot.config.get("butt_rate", 30)

    if channel not in next_butts:
        next_butts[channel] = prob.poissonvariate(rate)
        return

    next_butts[channel] -= 1
    print next_butts[channel]

    try:
        sent, score = buttifier.score_sentence(msg)

        if next_butts[channel] <= score.sentence():
            result = buttifier.buttify_sentence(sent, score)
            if result:
                next_butts[channel] = prob.poissonvariate(rate)
                say(result)
    except:
        pass
