from util import hook
import sys
sys.path += [".."] # heh

import buttifier
import prob
import random
import time

@hook.command
def butt(msg, me=None):
    try:
        return buttifier.buttify(msg, min_words=1)
    except:
        me("can't butt the unbuttable!")
        raise

class ChannelState(object):
    def __init__(self, next_time = 0, lines_left = 0):
        self.next_time = next_time
        self.lines_left = lines_left

channel_states = {}

# TODO: don't fire this when someone ran .butt!
@hook.singlethread
@hook.event("PRIVMSG")
def autobutt(_, chan=None, msg=None, bot=None, say=None):
    butt_config = bot.config["butt"] or {}
    rate_mean  = butt_config.get("rate_mean", 300)
    rate_sigma = butt_config.get("rate_sigma", 60)
    lines_mean = butt_config.get("lines_mean", 20)
    now = time.time()

    if chan[0] == '#': # public channel
        if chan in channel_states:
            state = channel_states[chan]
            state.lines_left -= 1
            print state

            if state.next_time > now:
                return

            sent, score = buttifier.score_sentence(msg)

            if score.sentence() == 0 or score.sentence() < state.lines_left:
                return

            say(buttifier.buttify_sentence(sent, score))

        channel_states[chan] = ChannelState(
            random.normalvariate(rate_mean, rate_sigma) + now,
            prob.poissonvariate(lines_mean)
        )
    else: # private message
        try:
            say(buttifier.buttify(msg))
        except:
            pass
