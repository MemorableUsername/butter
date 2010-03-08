import buttifier
import irclib
import random
import time
import re
import fnmatch

server = "irc.synirc.org"
port = 6667
nick = "buttebot"

class ignore_list(list):
    _regex_mode = re.compile(r"^/(.*)/(i?)$")
    _glob_mode = re.compile(r"[\*\?\[\]]")

    def __init__(self, filename):
        f = open(filename)
        for line in f:
            line = line.strip()
            m = self._regex_mode.search(line)
            if m:
                if len(m.group(2)) == 0:
                    self.append(re.compile(m.group(1)))
                else:
                    self.append(re.compile(m.group(1), re.I))
                continue
            elif self._glob_mode.search(line):
                self.append(re.compile( fnmatch.translate(line) ))
            else:
                self.append(line)
        f.close()

    def __contains__(self, name):
        for i in self:
            if isinstance(i, str):
                if i == name: return True
            elif i.search(name):
                return True
        return False



class buttbot(irclib.SimpleIRCClient):
    def __init__(self, server, port, nick, max_channels=5):
        irclib.SimpleIRCClient.__init__(self)
        self.connect(server, port, nick)
        self.channels_left = max_channels
        self.last_butt = 0.0 # the epoch

        self.ignore = ignore_list("ignore")

    def on_pubmsg(self, connection, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user in self.ignore: return

        bits = msg.split(' ', 1)
        if bits[0] == "!butte":
            if len(msg) > 1:
                try:
                    connection.privmsg(channel, user+": "+
                                       buttifier.buttify(bits[1], 
                                                         allow_single=True))
                except:
                    connection.action(channel, "can't butt the unbuttable!")
        else:
            now = time.time()
            if now - self.last_butt > 15 and random.random() < 0.05:
                try:
                    connection.privmsg(channel, buttifier.buttify(msg))
                    self.last_butt = now
                except:
                    pass

    def on_invite(self, connection, event):
        if self.channels_left > 0:
            connection.join(event.arguments()[0])
            self.channels_left -= 1

if __name__ == "__main__":
    irc = buttbot(server, port, nick)
    irc.start()
