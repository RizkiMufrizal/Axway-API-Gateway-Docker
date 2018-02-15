from processors.processor import *
from core.docker import *
from core.dockercompose import *
from environment import *
import re
import sys
import tempfile
import os

class Engine(object) :
    '''
    The engine for processing the configuration.
    '''

    def __init__(self, config, rootDir, baseos, environment) :
        self.config = config
        self.processors = self.__getProcessors()
        self.rootDir = rootDir
        self.baseos = baseos
        self.environment = environment

        self.processorMap = {}
        for processorType in self.processors :
            processor = processorType(self, config)
            self.processorMap[processor.__getKey__()] = processor


    def clean(self) :
        pass


    def hasProcessor(self, key) :
        return key in self.processorMap


    def process(self, key, node, action = "initial") :
        print "Processing %s %s on %s" % (action, key, self.currentContainer["name"])
        if key in self.processorMap :
            method = getattr(self.processorMap[key], action)
            return method(self.currentContainer, node)
        else :
            raise Exception("Unknown config key: " + key)


    def __getProcessors(self, cls = None) :
        allEngines = []

        if cls is None :
            cls = Processor

        for engine in cls.__subclasses__():
            allEngines.append(engine)
            allEngines.extend(self.__getProcessors(engine))

        return allEngines

    def _isOutOfDate(self, container) :
        '''
        Checks if containers are up to date with the current config.
        '''
        old = False
        if "containerLifecycle" in container and "noCommit" in container["containerLifecycle"] and container["containerLifecycle"]["noCommit"] :
            # No commit so intrinsically not dirty.
            old = False
        else :
            # Check Image
            imageName = "%s_%s" % (self.config.name, container["name"])

            label = dockerInspect(imageName, template = "{{json .ContainerConfig.Labels.config}}", failOnError = False)

            if label is None :
                # Legacy location
                label = dockerInspect(imageName, template = "{{json .Config.Labels.config}}", failOnError = False)

            if label is not None :
                label = re.sub("[\"\n]", "", label)
            if label is None or self.config.configHash != label :
                old = True
                print "%s is out of date." % imageName
        return old


    def _containerImageExists(self, container) :
        '''
        Checks if container images exist.
        '''
        exists = True
        try :
            imageName = "%s_%s" % (self.config.name, container["name"])
            dockerInspect(imageName, failOnError = True)
        except :
            exists = False

        return exists


class BuilderEngine(Engine) :
    '''
    The engine for building the configuration.
    '''

    def __init__(self, config, rootDir, baseos, keepBuildContainers = False) :
        print "**** BuilderEngine.__init__ %s" % config
        super(BuilderEngine, self).__init__(config, rootDir, baseos, BuilderEnvironment(config, rootDir))
        self.keepBuildContainers = keepBuildContainers


    def build(self) :
        outOfDate = False
        for container in self.config["containers"] :
            outOfDate = outOfDate or self._isOutOfDate(container)

        if not outOfDate :
            print "Topology up to date."
        else :
            print "Rebuilding topology."
            self.clean()
            try :
                self.environment.up()
                # Build the container images
                for cmd in ["initial", "buildPhase1", "buildPhase2", "buildPhase3", "final", "launch"] :
                    for container in self.config["containers"] :
                        self.currentContainer = container
                        self.process("container", container, cmd)

                self._persist()
            finally :
                if not self.keepBuildContainers :
                    self.environment.clean()
                else :
                    print "Build topology is still deployed."


    def _persist(self) :
        images = []
        print "Persist the containers in this config"
        for container in self.config["containers"] :
            self.currentContainer = container
            images.append( self._exportImportContainer(container) )
            self._rmContainer(container)


    def _exportImportContainer(self, container) :
        name = container["name"]
        runtime = container["runtime"]
        imageName = "%s_%s_%s" % (self.config.name, name, self.baseos)
        tarAbsPath = os.path.join(self.rootDir, imageName + ".tar")
        options = []

        if "containerLifecycle" in container:
            if "beforeCommit" in container["containerLifecycle"] :
                beforeCommit = container["containerLifecycle"]["beforeCommit"]
                self.process(beforeCommit, None)

            # Get the changes
            if "commitChanges" in container["containerLifecycle"] :
                for change in container["containerLifecycle"]["commitChanges"] :
                    options.extend(["-c", change])

        # export then import to flatten the image
        dockerExport(runtime, tarAbsPath)
        dockerImport(tarAbsPath, imageName, options)

        return (imageName, name, container)


    def _rmContainer(self, container) :
        runtime = container["runtime"]
        dockerRm(runtime, ["-vf"])


    def clean(self) :
        self.environment.clean()

        for container in self.config["containers"] :
            if "containerLifecycle" in container and "noCommit" in container["containerLifecycle"] and container["containerLifecycle"]["noCommit"] :
                continue
            imageName = "%s_%s" % (self.config.name, container["name"])
            dockerRmi(imageName, ["-f"], failOnError = False)

class RunnerEngine(Engine) :
    '''
    The engine for running the configuration.
    '''

    def __init__(self, config, rootDir, baseos, overrides = {}) :
        super(RunnerEngine, self).__init__(config, rootDir, baseos, RunnerEnvironment(config, rootDir, baseos, overrides))



    def build(self) :
        print "Generating the docker-compose.yaml."
        self.environment.build()

    def clean(self) :
        self.environment.clean()
