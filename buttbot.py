import buttifier
import fnmatch
import irclib
import prob
import re
import sys
import yaml
from collections import deque

class ignore_list(list):
    regex_mode_ex = re.compile(r"^/(.*)/(i?)$")
    glob_mode_ex  = re.compile(r"[\*\?\[\]]")

    def __init__(self, enemies):
        for i in enemies:
            m = self.regex_mode_ex.search(i)
            if m:
                if len(m.group(2)) == 0:
                    self.append(re.compile(m.group(1)))
                else:
                    self.append(re.compile(m.group(1), re.I))
                continue
            elif self.glob_mode_ex.search(i):
                self.append(re.compile( fnmatch.translate(i) ))
            else:
                self.append(i)

    def __contains__(self, name):
        for i in self:
            if isinstance(i, str):
                if i == name: return True
            elif i.search(name):
                return True
        return False

class buttbot(irclib.SimpleIRCClient):
    def __init__(self, config_file="config"):
        irclib.SimpleIRCClient.__init__(self)
        f = open(config_file)
        config = yaml.load(f)
        f.close()

        conn     = config['connection']
        settings = config['settings']

        self.connect(conn['server'], conn['port'], conn['nick'],
                     password=conn.get('server_pass'),
                     username=conn.get('username'),
                     ircname=conn.get('realname'))
        self.nickserv_pass = conn.get('nickserv_pass')
        self.default_channels = conn.get('channels', [])

        self.command = settings['command']
        self.channels_left = settings.get('max_channels', 5)
        self.enemies = ignore_list(settings.get('enemies', []))
        self.rate = settings.get('rate', 30)
        self.max_log = settings.get('max_log', 100)

        self.next_butt = {}
        self.log = deque()

    def _join(self, conn, channel):
        if self.channels_left > 0:
            conn.join(channel)
            self.channels_left -= 1

    def _parted(self, channel):
        if channel in self.next_butt:
            del self.next_butt[channel]
        self.channels_left += 1

    def _buttify(self, conn, channel, user, msg, explicit):
        try:
            result = buttifier.buttify(msg, allow_single=explicit)
            self.log.appendleft(result)
            if len(self.log) > self.max_log:
                self.log.pop()
            if explicit:
                result = user+": "+result
            conn.privmsg(channel, result)
        except:
            if explicit:
                conn.action(channel, "can't butt the unbuttable!")
            return False
        return True

    def on_welcome(self, conn, event):
        if self.nickserv_pass:
            conn.privmsg("NickServ", "IDENTIFY "+self.nickserv_pass)
        for channel in self.default_channels:
            self._join(conn, channel)

    def on_join(self, conn, event):
        self.next_butt[event.target()] = prob.poissonvariate(self.rate)

    def on_part(self, conn, event):
        self._parted(event.target())

    def on_kick(self, conn, event):
        self._parted(event.target())

    def on_pubmsg(self, conn, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user in self.enemies: return

        bits = msg.split(' ', 1)
        if bits[0] == self.command:
            if len(bits) > 1:
                self._buttify(conn, channel, user, bits[1], True)
        elif re.match(conn.get_nickname()+r"\W*$", bits[0]):
            if len(bits) > 1:
                command = bits[1].split(' ', 1)
                if command[0] == "butt":
                    self._buttify(conn, channel, user, command[1], True)
                elif command[0] == "log":
                    try:
                        i = int(command[1])-1
                    except:
                        conn.privmsg(channel, user+": syntax: log [message]")
                    try:
                        conn.privmsg(channel, user+": "+self.log[i])
                    except:
                        conn.privmsg(channel, user+": couldn't find message!")
        elif channel in self.next_butt:
            if self.next_butt[channel] == 0:
                if self._buttify(conn, channel, user, msg, False):
                    self.next_butt[channel] = prob.poissonvariate(self.rate)
            self.next_butt[channel] -= 1
        else:
            self.next_butt[channel] = prob.poissonvariate(self.rate)

    def on_privmsg(self, conn, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        try:
            conn.privmsg(user, buttifier.buttify(msg))
        except: pass

    def on_invite(self, conn, event):
        self._join(conn, event.arguments()[0])

if __name__ == "__main__":
    if len(sys.argv) == 2:
        buttbot(config_file=sys.argv[1]).start()
    else:
        buttbot().start()
