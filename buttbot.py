import buttifier
import ircbot
import prob
import sys
from collections import deque

class buttbot(ircbot.ircbot):
    def __init__(self, config_file="config"):
        config = self.load_config(config_file)
        ircbot.ircbot.__init__(self, config)

        settings = config['settings']

        self.command = settings['command']
        self.rate = settings.get('rate', 30)
        self.max_log = settings.get('max_log', 100)

        self.next_butt = {}
        self.log = deque()

        self.local_commands = {
            "butt":   self.buttify,
            "log":    self.get_log,
            "rebutt": self.rebuttify,
            }
        self.global_commands = {
            self.command: self.buttify,
            }
        self.default_local_command = self.buttify
        self.default_global_command = self.auto_buttify

    def _log_buttification(self, i, o):
        self.log.appendleft({"in": i, "out": o})
        if len(self.log) > self.max_log:
            self.log.pop()

    def auto_buttify(self, conn, channel, msg, **kwargs):
        """Listen for all chat and randomly buttify lines"""
        if channel not in self.next_butt:
            self.next_butt[channel] = prob.poissonvariate(self.rate)
            return

        try:
            sent, score = buttifier.score_sentence(msg)

            if self.next_butt[channel] <= score.sentence():
                result = buttifier.buttify_sentence(sent, score)
                if result:
                    self._log_buttification(msg, result)
                    self.next_butt[channel] = prob.poissonvariate(self.rate)
                    return { "msg": result, "to_user": False }
        except:
            pass

        self.next_butt[channel] -= 1

    def buttify(self, conn, channel, msg, **kwargs):
        try:
            result = buttifier.buttify(msg, allow_single=True)
            if result:
                self._log_buttification(msg, result)
                return result
        except Exception as e:
            return { "msg": "can't butt the unbuttable!", "action": True }

    def get_log(self, conn, channel, msg, **kwargs):
        try:
            i = int(msg)-1
        except:
            return "syntax: log [message]"

        try:
            return self.log[i]["out"]
        except:
            return "couldn't find message!"

    def rebuttify(self, conn, channel, msg, **kwargs):
        try:
            i = int(msg)-1
        except:
            return "syntax: rebutt [message]"

        try:
            return self.buttify(conn, channel, msg=self.log[i]["in"])
        except:
            return "couldn't find message!"


if __name__ == "__main__":
    if len(sys.argv) == 2:
        bot = buttbot(config_file=sys.argv[1])
    else:
        bot = buttbot()
    bot.start()
