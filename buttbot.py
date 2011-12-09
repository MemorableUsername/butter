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

    def _buttify(self, conn, channel, user, msg, explicit):
        try:
            result = buttifier.buttify(msg, allow_single=explicit)
            self.log.appendleft({"in": msg, "out": result})
            if len(self.log) > self.max_log:
                self.log.pop()
            return {"msg": result, "to_user": explicit}
        except:
            if explicit:
                conn.action(channel, "can't butt the unbuttable!")
            return None

    def auto_buttify(self, conn, channel, msg, **kwargs):
        if channel in self.next_butt:
            if self.next_butt[channel] == 0:
                result = self._buttify(conn, channel, None, msg, False)
                if result:
                    self.next_butt[channel] = prob.poissonvariate(self.rate)
                    return result
            self.next_butt[channel] -= 1
        else:
            self.next_butt[channel] = prob.poissonvariate(self.rate)
        
        return None

    def buttify(self, conn, channel, msg, **kwargs):
        return self._buttify(conn, channel, None, msg, True)

    def get_log(self, conn, channel, msg, **kwargs):
        try:
            i = int(msg)-1
        except:
            return {"msg": "syntax: log [message]", "to_user": True}
        try:
            return {"msg": self.log[i]["out"], "to_user": True}
        except:
            return {"msg": "couldn't find message!", "to_user": True}

    def rebuttify(self, conn, channel, msg, **kwargs):
        try:
            i = int(msg)-1
        except:
            return {"msg": "syntax: rebutt [message]", "to_user": True}
        try:
            return self._buttify(conn, channel, None, self.log[i]["in"], True)
        except:
            return {"msg": "couldn't find message!", "to_user": True}


if __name__ == "__main__":
    if len(sys.argv) == 2:
        buttbot(config_file=sys.argv[1]).start()
    else:
        buttbot().start()
