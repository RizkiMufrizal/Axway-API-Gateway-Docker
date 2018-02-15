from core.docker import *
from core.dockercompose import *
from os.path import expanduser
import re
import sys
import os


class BuilderEnvironment(object) :

    def __init__(self, config, rootDir) :
        print "__init__ recevied config: %s" % config
        self.config = config
        self.rootDir = rootDir
        self.buildProjectName = "build_" + self.config.name
        self.config.setRuntimeName(self.buildProjectName)

        # Safe location for servers folder
        if os.access(os.path.join(self.rootDir), os.W_OK) :
            self.buildProjectFolder = os.path.join(self.rootDir, "servers", "build", self.buildProjectName)
        else :
            self.buildProjectFolder = os.path.expanduser(os.path.join("~", ".axway-compose", "servers", "build", self.buildProjectName))

        self.standardTestVolumes = [
            "%s:%s" % (os.path.join(self.rootDir, "scripts"), "/scripts")
            ]

    def up(self) :
        self.__generateDockerCompose()
        dockerComposeUp(self.buildProjectFolder)


    def clean(self) :
        try :
            if os.path.exists(os.path.join(self.buildProjectFolder, "docker-compose.yml")) :
                dockerComposeClean(self.buildProjectFolder)
        except:
            pass


    def __generateDockerCompose(self) :
        '''
        Generate the docker compose used for building the environment.
        Using docker compose for simpler support of parallel builds.
        '''

        dockerComposePath = os.path.join(self.buildProjectFolder, "docker-compose.yml")
        print "Generating docker compose for build %s" % dockerComposePath

        mkdir_p(os.path.dirname(dockerComposePath))
        with open(dockerComposePath, "w") as dockerCompose :

            dockerCompose.write("version: '2'\n")
            dockerCompose.write("services:\n")

            compose = {}
            for container in self.config["containers"] :
                compose["hostname"] = container["hostname"]
                image = container["image"]

                nodemanagerPort = container["gatewayConfig"]["port"]
                np = str(nodemanagerPort) + ":" + str(nodemanagerPort)
                compose["ports"] = []
                compose["ports"].append(str(np))

                compose["volumes"] = self.standardTestVolumes
                if "volumes" in container :
                    compose["volumes"].extend(container["volumes"])

                compose["links"] = []
                if "links" in container :
                    compose["links"].extend(container["links"])

                compose["labels"] = ["config=%s" % self.config.configHash]   # Add the hash to allow change detection
                if "labels" in container :
                    compose["labels"].extend(container["labels"])

                if "gatewayConfig" in container :
                    # No-op startup for gateways so they can be configured.
                    compose["command"] = "tail -f /dev/null"

                if "containerLifecycle" in container and "buildRunCommand" in container["containerLifecycle"]  :
                    compose["command"] = container["containerLifecycle"]["buildRunCommand"]

                # Multinode cassandra needs to customize ip addresses, to do this the container needs to be privileged. For ease
                # we will just make all gateway containers privileged
                compose["privileged"] = "gatewayConfig" in container
                frag = self.__dockerComposeFragment(container["name"], image, compose)

                print "Writing frag: %s" % frag
                dockerCompose.write(frag + "\n")


    def __dockerComposeFragment(self, name, image, compose) :
        nodeStr = """
    %s:
        image: %s""" % (name, image)

        for key,value in compose.iteritems() :
            if isinstance(value, list) and not isinstance(value, str):
                if  len(value) > 0 :
                    s ="        %s:" % key
                    for v in value :
                        # Quote port values
                        if key == "ports" and not v.startswith("\""):
                            v = "\"%s\"" % v

                        s = "%s\n            - %s" % (s, v)
                else :
                    continue

            elif isinstance(value, str) :
                s ="        %s: %s" % (key, value)

            elif isinstance(value, bool) :
                s ="        %s: %s" % (key, str(value).lower())

            else :
                s ="        %s: %s" % (key, str(value))

            nodeStr = "%s\n%s" % (nodeStr, s)

        nodeStr = nodeStr + "\n"
        return nodeStr


class RunnerEnvironment(object) :
    CASSANDRA_HOSTS = ["cassandra-m","cassandra-s1","cassandra-s2"]
    CONFIG_KEY = [
        "working_dir",
        "entrypoint",
        "command",
        "user",
        "hostname",
        "domainname",
        "mac_address",
        "mem_limit",
        "memswap_limit",
        "privileged",
        "restart",
        "stdin_open",
        "tty",
        "cpu_shares",
        "cpuset",
        "read_only",
        "volume_driver"
    ]

    def __init__(self, config, rootDir, baseos, overrides = {}) :
        self.config = config
        self.rootDir = rootDir
        self.overrides = overrides
        self.baseos = baseos

        if os.access(os.path.join(self.rootDir), os.W_OK) :
            self.projectFolder = os.path.join(self.rootDir, "..", "..", "..", "compose-generated", "servers", self.config.name)
        else :
            self.projectFolder = os.path.expanduser(os.path.join("~", ".axway-compose", "servers", self.config.name))

        # Add the scripts
        self.standardTestVolumes = [
            "%s:%s" % (os.path.join(rootDir, "scripts"), "/scripts")
            ]

    def build(self):
        self.__generateDockerCompose()

    def up(self) :
        self.clean()
        self.__generateDockerCompose()
        self.clean() # Kludge for CI where it recreates the folders.
        dockerComposeUp(self.projectFolder)

        # TODO: Refactor into processors
        # On the gateways wait for them to come up
        #WaitForGateways(self.config).execute()


    def clean(self) :
        '''
        Clean any running containers for this config.
        '''
        try :
            if os.path.exists(os.path.join(self.projectFolder, "docker-compose.yml")) :
                dockerComposeClean(self.projectFolder)
        except:
            pass

    def __generateDockerCompose(self) :
        dockerComposePath = os.path.join(self.projectFolder, "docker-compose.yml")
        print "Generating docker compose %s" % dockerComposePath

        commandLineOverrides = self.__dockerComposeOverrides()

        mkdir_p(os.path.dirname(dockerComposePath))
        with open(dockerComposePath, "w") as dockerCompose :

            dockerCompose.write("version: '2'\n")
            dockerCompose.write("services:\n")

            extVolumes = []
            for index, container in enumerate(self.config["containers"]) :
                self.__buildContainer(index,container,dockerCompose,extVolumes,commandLineOverrides)
            self.__cassandraStaticHosts(dockerCompose,extVolumes)
            self.__topLevelVolumes(dockerCompose,extVolumes)
    
    def __buildContainer(self,index,container,dockerCompose,extVolumes,commandLineOverrides):
        compose = {}
        for key in RunnerEnvironment.CONFIG_KEY :
            if key in container :
                compose[key] = container[key]
        image = "%s_%s_%s" % (self.config.name, container["name"], self.baseos)
        if "containerLifecycle" in container and "noCommit" in container["containerLifecycle"] and container["containerLifecycle"]["noCommit"] :
            image = container["image"]

        # Multinode cassandra needs to customize ip addresses, to do this the container needs to be privileged. For ease
        # we will just make all gateway containers privileged
        compose["privileged"] = "gatewayConfig" in container
        compose["#volumes"] = []
        self.__dockerVolumes(container,compose,dockerCompose,extVolumes)
        # Volume overrides
        if container["name"] in commandLineOverrides and "#volumes" in commandLineOverrides[container["name"]]:
            compose["#volumes"].extend(commandLineOverrides[container["name"]]["#volumes"])

        compose["links"] = []
        if "links" in container :
            compose["links"].extend(container["links"])

        for cas_host in self.CASSANDRA_HOSTS:
            compose["links"].append(cas_host)
        
        if "ports" in container :
            compose["ports"].extend(container["ports"])

        # Port overrides
        if container["name"] in commandLineOverrides and "ports" in commandLineOverrides[container["name"]]:
            compose["ports"].extend(commandLineOverrides[container["name"]]["ports"])

        compose["environment"] = []
        compose["devices"] = []

        # Allow for desktop interaction
        if container.get("desktop", False) or (container["name"] in commandLineOverrides and commandLineOverrides[container["name"]].get("desktop", False)):
            compose["#volumes"].append("/tmp/.X11-unix:/tmp/.X11-unix")
            compose["environment"].append("DISPLAY=unix%s" % os.getenv("DISPLAY", ":0.0"))
            compose["devices"].append("/dev/snd:/dev/snd")

        # Cassandra Hard Coded Cluster
        gwBackoffSecs = (len(self.CASSANDRA_HOSTS) + index) * 60 # Backoff 60 secs after the last cassandra node
        compose["environment"].append("START_BACKOFF_SECS=%d # starts after Cassandra cluster and 60s after previous instance" % gwBackoffSecs)
        compose["environment"].append("CASSANDRA_HOSTS=cassandra-m,cassandra-s1,cassandra-s2")

        # API GW LICENSE 
        licInfo = 'To set the license run: export APIGW_LICENSE="$(cat /path/to/licenses/lic.lic | gzip | base64)" on the docker host'
        compose["environment"].append("APIGW_LICENSE #%s" % licInfo)
        
        compose["restart"] = "on-failure:2"
        frag = self.__dockerComposeFragment(container["name"], image, compose)
        dockerCompose.write(frag + "\n")

    def __topLevelVolumes(self,dockerCompose,extVolumes):
        dockerCompose.write("# volumes:\n")
        for vol in extVolumes:
            dockerCompose.write("#    %s:\n" % vol)
            dockerCompose.write("#        external: true\n")

    def __cassandraStaticHosts(self,dockerCompose,extVolumes):

         for index, cas_host in enumerate(self.CASSANDRA_HOSTS):
            compose = {}
            compose["hostname"] = cas_host 
            compose["environment"] = []
            compose["environment"].append("START_BACKOFF_SECS=%d # prevents race between nodes joining the cluster" % int(index * 60))
            compose["environment"].append("SEEDS=cassandra-m") 
            compose["environment"].append("MAX_HEAP_SIZE=1G")
            compose["environment"].append("HEAP_NEWSIZE=400m")
            compose["restart"] = "on-failure:2"
            compose["#volumes"] = []
            self.__dockerVolume(compose,extVolumes,"Cassandra data volume",cas_host+ "_DATA",os.path.join(os.sep,"opt","cassandra","data"))
            self.__dockerVolume(compose,extVolumes,"Cassandra logs volume",cas_host + "_LOGS",os.path.join(os.sep,"opt","cassandra","logs"))
            frag = self.__dockerComposeFragment(cas_host,"cassandra_%s" % self.baseos, compose)
            dockerCompose.write(frag + "\n")
    
    def __dockerVolumes(self,container,compose,dockerCompose,extVolumes):
         # compose["#volumes"].extend(self.standardTestVolumes)
        if "#volumes" in container :
            compose["#volumes"].extend(container["#volumes"])

        volume1_comment = "Configuring volume for Node Manager conf (modified using API Gateway Manager web application)"
        volume2_comment = "Configuring volume for Node Manager trace (modified using API Gateway Manager web application)"
        volume3_comment = "Configuring volume for Node Manager logs (includes Domain and Transaction logs modified using API Gateway Manager web application)"
        volume4_comment = "Configuring volume for Node Manager events (modified using API Gateway Manager web application)"
        volume5_comment = "Configuring volume for API Gateway Group Configuration, data, logging and trace."
        volume6_comment = "Configuring volume for API Gateway user data eg. ActiveMQ, File-based filters, Ehcache etc"
        if "gatewayConfig" in container and "groups" in container["gatewayConfig"] :
            for group in container["gatewayConfig"]["groups"] :
                for instance in group["instances"]:
                    # Container conf volume
                    container_path = os.path.join(container["gatewayConfig"]["installPathCurrent"],"conf")
                    vol_name = container["name"] + "_CONF_DATA"
                    self.__dockerVolume(compose,extVolumes,volume1_comment,vol_name,container_path)
                    # Node Manager trace volume
                    container_path = os.path.join(container["gatewayConfig"]["installPathCurrent"],"trace")
                    vol_name = container["name"] + "_TRACE_DATA" 
                    self.__dockerVolume(compose,extVolumes,volume2_comment,vol_name,container_path)
                    # Node Manager logs volume
                    container_path = os.path.join(container["gatewayConfig"]["installPathCurrent"],"logs")
                    vol_name = container["name"] + "_LOGS_DATA" 
                    self.__dockerVolume(compose,extVolumes,volume3_comment,vol_name,container_path)
                    # Node Manager events volume
                    container_path = os.path.join(container["gatewayConfig"]["installPathCurrent"],"events")
                    vol_name = container["name"] + "_EVENTS_DATA" 
                    self.__dockerVolume(compose,extVolumes,volume4_comment,vol_name,container_path)
                    # Node Manager groups volume
                    container_path = os.path.join(container["gatewayConfig"]["installPathCurrent"],"groups")
                    vol_name = container["name"] + "_GROUP_DATA" 
                    self.__dockerVolume(compose,extVolumes,volume5_comment,vol_name,container_path)
                    # User data volume
                    container_path = "/custom_path/to/userdata/"
                    vol_name = container["name"] + "_USER_DATA" 
                    self.__dockerVolume(compose,extVolumes,volume6_comment,vol_name,container_path)

    def __dockerVolume(self,compose, extVolumes,comment, vol_name, container_path):
        volume_string =  "# %s # %s:%s" % (comment,vol_name,container_path)
        extVolumes.append(vol_name) 
        if volume_string not in compose["#volumes"]:
            compose["#volumes"].append(volume_string)

    def __dockerComposeOverrides(self, ports=None, volumes=None, desktops=None) :
        commandLineOverrides = {}

        if self.overrides.get("ports", None) is not None:
            for portDef in self.overrides["ports"] :
                toks = string.split(portDef, ":", 3)
                if len(toks) < 2 :
                    raise Exception("Invalid port override format.")

                (containerName, containerPort, hostPort) = (toks[0], toks[1], None if len(toks) < 3 else ':'.join(toks[2:]))

                if self.config.getContainer(containerName) is None:
                    raise Exception("Invalid container name in port override: " + portDef)

                if not containerName in commandLineOverrides :
                    commandLineOverrides[containerName] = {}

                if not "ports" in commandLineOverrides[containerName] :
                    commandLineOverrides[containerName]["ports"] = []

                if hostPort :
                    commandLineOverrides[containerName]["ports"].append("\"%s:%s\"" % (containerPort, hostPort))
                else :
                    commandLineOverrides[containerName]["ports"].append("\"%s\"" % (containerPort))


        if self.overrides.get("#volumes", None) is not None:
            for volDef in self.overrides["#volumes"] :
                toks = string.split(volDef, ":", 3)
                if len(toks) < 2 :
                    raise Exception("Invalid volume override format.")

                (containerName, containerPath, hostPath) = (toks[0], toks[len(toks) - 1], None if len(toks) < 3 else toks[1])

                if self.config.getContainer(containerName) is None:
                    raise Exception("Invalid container name in volume override: " + volDef)

                if not containerName in commandLineOverrides :
                    commandLineOverrides[containerName] = {}

                if not "#volumes" in commandLineOverrides[containerName] :
                    commandLineOverrides[containerName]["#volumes"] = []

                if hostPath :
                    commandLineOverrides[containerName]["#volumes"].append("\"%s:%s\"" % (hostPath, containerPath))
                else :
                    commandLineOverrides[containerName]["#volumes"].append("\"%s\"" % (containerPath))

        if self.overrides.get("desktops", None) is not None:
            print "Remember to run `xhost +` to allow desktop interaction."
            for desktop in self.overrides["desktops"] :
                toks = string.split(desktop, ":", 2)
                (containerName, desktopEnabled) = (toks[0], False if len(toks) < 2 else toks[1] in ["true", "True", "1", "yes", "y"])

                if self.config.getContainer(containerName) is None:
                    raise Exception("Invalid container name in desktop override: " + desktop)

                if not containerName in commandLineOverrides :
                    commandLineOverrides[containerName] = {}

                if not "desktop" in commandLineOverrides[containerName] :
                    commandLineOverrides[containerName]["desktop"] = []

                commandLineOverrides[containerName]["desktop"].append(desktopEnabled)


        return commandLineOverrides


    def __dockerComposeFragment(self, name, image, compose) :
        nodeStr = """
    %s:
        image: %s""" % (name, image)

        for key,value in compose.iteritems() :
            if isinstance(value, list) and not isinstance(value, str):
                if  len(value) > 0 :
                    s ="        %s:" % key
                    for v in value :
                        # Quote port values
                        if key == "ports" and not v.startswith("\""):
                            v = "\"%s\"" % v
                        if not v.startswith("#") :
                            s = "%s\n        - %s" % (s, v)
                        else:
                            k = v[1:].rfind("#")
                            commnent  = v[1:k]
                            value  = v[k+2:]
                            s = "%s\n        # %s\n        # - %s" % (s,commnent,value)
                else :
                    continue

            elif isinstance(value, str) :
                s ="        %s: %s" % (key, value)

            elif isinstance(value, bool) :
                s ="        %s: %s" % (key, str(value).lower())
            else :
                s ="        %s: %s" % (key, str(value))

            nodeStr = "%s\n%s" % (nodeStr, s)

        nodeStr = nodeStr + "\n"
        return nodeStr
