import buttifier
import fnmatch
import irclib
import prob
import re
import sys
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

        self.next_butt = {}

    def _next_butt(self):
        return prob.poissonvariate(self.rate) + self.min_rate

    def on_welcome(self, conn, event):
        if self.nickserv_pass:
            conn.privmsg("NickServ", "IDENTIFY "+self.nickserv_pass)
        for channel in self.default_channels:
            conn.join(channel)

    def on_join(self, conn, event):
        self.next_butt[event.target()] = prob.poissonvariate(self.rate)

    def on_pubmsg(self, conn, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user in self.enemies: return

        bits = msg.split(' ', 1)
        if bits[0] == self.command:
            if len(msg) > 1:
                try:
                    conn.privmsg(channel, user+": "+buttifier.buttify(
                            bits[1], allow_single=True))
                except:
                    conn.action(channel, "can't butt the unbuttable!")
        else:
            if self.next_butt[channel] == 0:
                try:
                    conn.privmsg(channel, buttifier.buttify(msg))
                    self.next_butt[channel] = prob.poissonvariate(self.rate)
                except: pass

            self.next_butt[channel] -= 1

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
    if len(sys.argv) == 2:
        buttbot(config=sys.argv[1])
    else:
        buttbot().start()
