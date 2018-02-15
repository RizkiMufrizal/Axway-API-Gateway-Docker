from engine import Processor
from core.docker import *
from core.dockercompose import *
import re
import sys


class ContainerProcessor(Processor) :
    '''
    The entry point for processing a container.
    '''
    KEY = 'container'

    ATTRIBUTES = [
        "containerLifecycle", 
        "description",
        "links",
        "image",
        "hostname",
        "name",
        "import",
        "runtime",
        "ports",
        "volumes",
        "environment",
        "devices",
        "desktop",
        "privileged",
        "command",
        "mem_limit"]

    def __init__(self, engine, config) :
        super(ContainerProcessor, self).__init__(engine, ContainerProcessor.KEY, config)
        self.config = config

    def initial(self, container, node) :
        self.__process(container, node, 'initial')

    def buildPhase1(self, container, node) :
        self.__process(container, node, 'buildPhase1')

    def buildPhase2(self, container, node) :
        self.__process(container, node, 'buildPhase2')

    def buildPhase3(self, container, node) :
        self.__process(container, node, 'buildPhase3')

    def final(self, container, node) :
        self.__process(container, node, 'final')

    def launch(self, container, node) :
        launchCnfFd, launcCnfPath = tempfile.mkstemp()

        try :
            cmds = super(ContainerProcessor, self).launch(container, node)
            if cmds :
                os.write(launchCnfFd, "\n".join(cmds))
                os.write(launchCnfFd, "\ntail -f /dev/null")
                dockerCpTo(container["runtime"], launcCnfPath, "/launch.conf")
        finally : 
            os.close(launchCnfFd)



    def __process(self, container, node, action) :
        print "Processing container: %s" % node.get("name", node.get("image"))
        resp = []

        for key, value in node.iteritems() :
            if key in ContainerProcessor.ATTRIBUTES :
                pass # For now no need to do anything with these.
            else :
                r = self.engine.process(key, value, action)
                if r :
                    if isinstance(r, basestring) :
                        resp.append(r)
                    else :
                        resp.extend(r)

        return resp