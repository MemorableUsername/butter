import buttifier
import irclib
import random
import time
import re
import fnmatch
import yaml

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

        self.connect(config['server'], config['port'], config['nick'],
                     password=config.get('server_pass'),
                     username=config.get('username'),
                     ircname=config.get('realname'))
        self.command = config['command']

        self.nickserv_pass = config.get('nickserv_pass')
        self.default_channels = config.get('channels', [])
        self.channels_left = config.get('max_channels', 5)
        self.enemies = ignore_list(config.get('enemies', []))

        self.last_butt = {}

    def on_welcome(self, connection, event):
        if self.nickserv_pass:
            connection.privmsg("NickServ", "IDENTIFY "+self.nickserv_pass)
        for channel in self.default_channels:
            connection.join(channel)

    def on_pubmsg(self, connection, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user in self.enemies: return

        bits = msg.split(' ', 1)
        if bits[0] == self.command:
            if len(msg) > 1:
                try:
                    connection.privmsg(channel, user+": "+
                                       buttifier.buttify(bits[1], 
                                                         allow_single=True))
                except:
                    connection.action(channel, "can't butt the unbuttable!")
        else:
            now  = time.time()
            last = self.last_butt.get(channel, 0.0) # default to the epoch
            if now - last > 15 and random.random() < 0.05:
                try:
                    connection.privmsg(channel, buttifier.buttify(msg))
                    self.last_butt[channel] = now
                except: pass

    def on_privmsg(self, connection, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        try:
            connection.privmsg(user, buttifier.buttify(msg))
        except: pass

    def on_invite(self, connection, event):
        if self.channels_left > 0:
            connection.join(event.arguments()[0])
            self.channels_left -= 1

if __name__ == "__main__":
    buttbot().start()
