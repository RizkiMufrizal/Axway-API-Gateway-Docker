from ..util.command import *

class StopLdap(Command) :
    def __init__(self, container, config) :
        super(StopLdap, self).__init__(config)
        scriptcmd = ["/stop.sh"]
        self.cmds.append((container["runtime"], scriptcmd, None))
