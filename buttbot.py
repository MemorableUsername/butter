import buttifier
import irclib

server = "irc.synirc.org"
port = 6667
nick = "buttebot"
channel = "#botsploitation"

class pybc_bot(irclib.SimpleIRCClient):
    def __init__(self, server, port, nick, channel):
        irclib.SimpleIRCClient.__init__(self)
        self.connect(server, port, nick)
        self.channel = channel

    def on_welcome(self, connection, event):
        connection.join(self.channel)

    def on_pubmsg(self, connection, event):
        msg = event.arguments()[0].split(' ', 1)
        user = event.source().split('!')[0]
        if msg[0] == "!butt":
            if len(msg) == 1:
                connection.action(self.channel, "glares at "+user)
            else:
                try:
                    connection.privmsg(self.channel, user+": "+
                                       buttifier.buttify(msg[1]))
                except:
                    connection.action(self.channel, "glares at "+user)

irc = pybc_bot(server, port, nick, channel)
irc.start()
