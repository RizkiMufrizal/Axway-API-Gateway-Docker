from ..processor import Processor
from core.docker import *

class SSHDProcessor(Processor) :
    '''
    Run a SSH daemon.
    '''
    KEY = 'sshd'

    def __init__(self, engine, config) :
        super(SSHDProcessor, self).__init__(engine, SSHDProcessor.KEY, config)

    def initial(self, container, node) :
        print "Adding SSHD"
        dockerExec(container["runtime"], ["mkdir", "/var/run/sshd"])
        if "authorized_keys" in node :
            # TODO: remove hardcoded root and use the value from the config
            dockerCpTo(container["runtime"], os.path.expanduser(node["authorized_keys"]), os.path.join("root", ".ssh", "authorized_keys"))
        

    def _getLaunchCmd(self, container, node) :
        return "/usr/sbin/sshd"
