from ..processor import Processor
from core.docker import *

class MessageProcessor(Processor) :
    '''
    This is intended as an example of how to write a processor.
    '''
    KEY = 'motd'

    def __init__(self, engine, config) :
        super(MessageProcessor, self).__init__(engine, MessageProcessor.KEY, config)

    def initial(self, container, node) :
        # In this case the node is not a map just a text string....motd might not be installed 
        # and as this is an example we're just appending to bashrc
        print "Adding message of the day"
        dockerExec(container["runtime"], ["bash", "-c", "echo \"echo %s\" >> ~/.bashrc" % node])

    def _getLaunchCmd(self, container, node) :
        return "echo \"You've started a container with a MOTD on `hostname -i`\""
