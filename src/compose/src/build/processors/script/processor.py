from ..processor import Processor
from core.docker import *

class ScriptProcessor(Processor) :
    '''
    Allow the execution of ad-hoc scripts during the build of the image
    or when the container is launched.
    Syntax:

    "script" : "<script to execute at initial phase>"
    "script" : ["<script to execute at initial phase>", "<script to execute at initial phase>"]
    "script" : {
        "initial" : ["<script to execute at initial phase>"],
        "buildPhase1" : ["<script to execute at buildPhase1>"],
        "buildPhase2" : ["<script to execute at buildPhase2>"],
        "buildPhase3" : ["<script to execute at buildPhase3>"],
        "final" : ["<script to execute at final phase>"],
        "launch" : ["<script to execute when container is launched.>"]
    }
    '''
    KEY = 'script'

    def __init__(self, engine, config) :
        super(ScriptProcessor, self).__init__(engine, ScriptProcessor.KEY, config)

    def initial(self, container, node) :
        self._execScript(container, node, "initial")

    def buildPhase1(self, container, node) :
        '''
        Build the container configuration.
        '''
        self._execScript(container, node, "buildPhase1")

    def buildPhase2(self, container, node) :
        '''
        Build the container configuration.
        '''
        self._execScript(container, node, "buildPhase2")

    def buildPhase3(self, container, node) :
        '''
        Build the container configuration.
        '''
        self._execScript(container, node, "buildPhase3")

    def final(self, container, node) :
        '''
        Configuration run after all containers have been built.
        '''
        self._execScript(container, node, "final")

    def _getLaunchCmd(self, container, node) :
        cmds = []
        scripts = self._getValue(node, "launch")

        for script in scripts :
            loc, path = os.path.split(script)
            if (path is None) :
                path = loc

            dockerCpTo(container["runtime"], script, os.path.join("/", path))
            dockerExec(container["runtime"], ["chmod", "+x", os.path.join("/", path)])
            cmds.append(os.path.join("/", path))

        return cmds


    def _execScript(self, container, node, cmd) :
        scripts = self._getValue(node, cmd)

        for script in scripts :
            loc, path = os.path.split(script)
            if (path is None) :
                path = loc

            dockerCpTo(container["runtime"], script, os.path.join("/", path))
            dockerExec(container["runtime"], ["chmod", "+x", os.path.join("/", path)])
            dockerExec(container["runtime"], [os.path.join("/", path)])


    def _getValue(self, node, cmd) :
        val = []
        if not isinstance(node, dict) and cmd == "initial" :
            if isinstance(node, basestring) :
                val = [node]
            else :
                val = node
        else :
            if cmd in node :
                val = node[cmd] if not isinstance(node[cmd], basestring) else [node[cmd]]
        return val