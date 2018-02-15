import sys
import traceback
from core.docker import *

class Command(object) :
    '''
    Simple command executor.
    '''
    def __init__(self, config) :
        self.config = config
        self.cmds = []

    def execute(self) :
        for (node, cmd, options) in self.cmds :
            try :
                dockerExec(node, cmd, options)
            except :
                print '\033[1m\033[31m%s' % ('-'*60)
                print "[%s]: Error executing command: %s " % (node, " ".join(cmd))
                traceback.print_exc(file=sys.stdout)
                print '%s\n\033[0m' % ('-'*60)
                raise
