class Processor(object) :
    '''
    Base class for processors that consume the configuration.
    '''    
    def __init__(self, engine, key, config) :
        self.engine = engine
        self.key = key

    def __getKey__(self) :
        return self.key

    
    def initial(self, container, node) :
        '''
        Preparation for build.
        '''
        pass


    def buildPhase1(self, container, node) :
        '''
        Build the container configuration.
        '''
        pass

    def buildPhase2(self, container, node) :
        '''
        Build the container configuration.
        '''
        pass

    def buildPhase3(self, container, node) :
        '''
        Build the container configuration.
        '''
        pass

    def final(self, container, node) :
        '''
        Configuration run after all containers have been built.
        '''
        pass

    def clean(self, container, node) :
        pass

    def _getLaunchCmd(self, container, node) :
        pass

    def launch(self, container, node) :
        '''
        Return the list of commands that this processor will launch on container start.
        (e.g. starting gateways, starting cassandra, etc). These are executed in side the
        container.
        '''
        cmds = []
        cmd = self._getLaunchCmd(container, node)
        
        if cmd :
            if isinstance(cmd, basestring) :
                cmds.append(cmd)
            else :
                cmds.extend(cmd)

        if isinstance(node, dict) :
            for key,value in node.iteritems() :
                if (self.engine.hasProcessor(key)) :
                    childCmds = self.engine.process(key, value, "launch")
                    if childCmds :
                        cmds.extend(childCmds)

        return cmds


