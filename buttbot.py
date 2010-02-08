import buttifier
import irclib
import random
import time

server = "irc.synirc.org"
port = 6667
nick = "buttebot"

class buttbot(irclib.SimpleIRCClient):
    def __init__(self, server, port, nick, max_channels=5):
        irclib.SimpleIRCClient.__init__(self)
        self.connect(server, port, nick)
        self.channels_left = max_channels
        self.last_butt = 0.0 # the epoch

    def on_pubmsg(self, connection, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user[-3:-1] == 'bot': return

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

irc = buttbot(server, port, nick)
irc.start()
