
import os
import time
import threading

import kaechatlib

class ShellThread(threading.Thread):

    def __init__(self, frame, timeout, channel, dosend, command):
        threading.Thread.__init__(self)
        self.frame = frame
        self.timeout = timeout
        self.channel = channel
        self.dosend = dosend
        self.command = command
        if dosend and (channel[0] != '('):
            self.echo = self._send
        else:
            self.echo = self._echo

    def _echo(self, text):
        self.frame.echo(text, channel=self.channel, event=kaechatlib.NOTICE_EV)

    def _send(self, text):
        self.frame.client.notice(self.channel, text)
        self.frame.echo(text, channel=self.channel, event=kaechatlib.NOTICE_EV)

    def run(self):
        st = time.clock()
        try:
            f = os.popen(self.command, "r")
            for line in f:
                t = time.clock() - st
                if t >= self.timeout:
                    self.frame.echo("Program stopped due to timeout.",
                        channel=self.channel, event=kaechatlib.NOTICE_EV)
                    break
                self.echo(line)
            r = f.close()
            self.frame.echo("Program exited with code %d" % (r or 0),
                channel=self.channel, event=kaechatlib.NOTICE_EV)
        except (OSError, IOError) as e:
            self.frame.echo("Exception: %s" % str(e),
                channel=self.channel, event=kaechatlib.NOTICE_EV)

@kaechatlib.chat_command
def _sh(frame, cmd, args, args_eol):
    """/sh [(-t TIMEOUT|-c CHANNEL|-s)] COMMAND

    Run COMMAND in the system shell and print it's output to a channel.

    If `-t TIMEOUT' is specified, it's the number of seconds to wait for the \
    process. If the process takes more than TIMEOUT, it's killed. If not \
    specified, defaults to 10 seconds, to avoid accidental runs of long running \
    programs.

    If `-c CHANNEL' is specified, output goes to CHANNEL (note that the output is \
    only "echoed" to the textbox; it's not actually sent to the server, unless \
    `-s' is specified. If not specified, sends to '(shell)' channel.

    If `-s' is specified, and a (non-special) CHANNEL was specified, the output \
    of the COMMAND is sent as messages to the channel. WARNING: BE CAREFUL WITH \
    THIS OPTION! YOU CAN EASILY GET YOU BANNED FROM CHANNELS, AND EVEN NETWORKS \
    IF THE COMMAND YOU RUN FLOODS WITH OUTPUT! Only use for commands with short \
    output like `uname', `uptime', etc. In particular, DON'T EVEN THINK ABOUT \
    RUNNING PROGRAMS LIKE `yes'!
    """
    timeout = 10
    channel = "(shell)"
    send = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-t":
            i += 1
            if i >= len(args):
                kaechatlib.usage(frame, cmd, "Missing parameter to `-t'.")
                return
            try:
                timeout = int(args[i])
            except ValueError:
                kaechatlib.usage(frame, cmd, "Timeout must be an integer.")
                return
        elif a == "-c":
            i += 1
            if i >= len(args):
                kaechatlib.usage(frame, cmd, "Missing parameter to `-c'.")
                return
            channel = args[i]
        elif a == "-s":
            send = True
        else:
            break
        i += 1
    if i >= len(args):
        kaechatlib.usage(frame, cmd, "Missing command.")
        return
    command = args_eol[i]
    t = ShellThread(frame, timeout, channel, send, command)
    t.start()

kaechatlib.chat_command_alias("!", "sh")
