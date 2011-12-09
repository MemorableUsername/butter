import fnmatch
import irclib
import re
import yaml

def safe_split(s, t):
    bits = s.split(t, 1)
    if len(bits) == 1:
        return [bits[0], ""]
    else:
        return bits

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

class ircbot(irclib.SimpleIRCClient):
    def __init__(self, config="config"):
        irclib.SimpleIRCClient.__init__(self)
        if isinstance(config, str):
            config = self.load_config(config)

        conn     = config['connection']
        settings = config['settings']

        self.connect(conn['server'], conn['port'], conn['nick'],
                     password=conn.get('server_pass'),
                     username=conn.get('username'),
                     ircname=conn.get('realname'))
        self.nickserv_pass = conn.get('nickserv_pass')
        self.default_channels = conn.get('channels', [])

        self.channels_left = settings.get('max_channels', 5)
        self.enemies = ignore_list(settings.get('enemies', []))

    def load_config(self, config_file):
        f = open(config_file)
        config = yaml.load(f)
        f.close()
        return config

    def _dispatch_command(self, user, msg):
        command = msg.split(' ', 1)
        try:
            f = getattr(self, "do_"+command)
            return f(user, command[1])
        except:
            pass

    def _join(self, conn, channel):
        if self.channels_left > 0:
            conn.join(channel)
            self.channels_left -= 1

    def _parted(self, channel):
        if channel in self.next_butt:
            del self.next_butt[channel]
        self.channels_left += 1

    def on_welcome(self, conn, event):
        if self.nickserv_pass:
            conn.privmsg("NickServ", "IDENTIFY "+self.nickserv_pass)
        for channel in self.default_channels:
            self._join(conn, channel)

    def on_part(self, conn, event):
        self._parted(event.target())

    def on_kick(self, conn, event):
        self._parted(event.target())

    def on_pubmsg(self, conn, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]
        channel = event.target()

        if user in self.enemies: return

        global_prefix, global_args = safe_split(msg, " ")
        # First, check for local commands (i.e. "bot: do this")
        if re.match(conn.get_nickname()+r"\W*$", global_prefix):
            if len(global_args) == 0:
                return
            local_prefix, local_args = safe_split(global_args, " ")
            command = self.local_commands.get(local_prefix)
            if not command:
                command = self.default_local_command
                local_args = global_args

            if command:
                result = command(conn=conn, channel=channel, user=user,
                                 msg=local_args)
        # Now, check for global commands (i.e. "!dothis")
        else:
            command = self.global_commands.get(global_prefix)
            if not command:
                command = self.default_global_command
                global_args = msg

            if command:
                result = command(conn=conn, channel=channel, user=user,
                                 msg=global_args)

        if result:
            response = result["msg"]
            if result.get("to_user", False):
                response = user+": "+response

            conn.privmsg(channel, response)

    def on_privmsg(self, conn, event):
        msg = event.arguments()[0]
        user = event.source().split('!')[0]

        prefix, args = safe_split(msg, " ")
        command = self.local_commands.get(prefix)
        if not command:
            command = self.default_local_command
            args = msg
        if command:
            result = command(conn=conn, channel=None, user=user, msg=args)

        if result:
            conn.privmsg(user, result["msg"])

    def on_invite(self, conn, event):
        self._join(conn, event.arguments()[0])
