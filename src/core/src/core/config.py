import os
import json
import string
import re
import base64
import hashlib
import collections
from docker import getContainerIpAndHost
from util import *
from template import tmplExpandJson


class BuildConfig(object) :

    def __init__(self, conifgFilePath) :
        self.data = self._processConfig(conifgFilePath)
        self.gatewayContainerList = None
        self.analyticsContainerList = None

        if "name" not in self.data :
            self.name = os.path.splitext(os.path.basename(conifgFilePath))[0]
        else :
            self.name = self.data["name"]

        self.setRuntimeName(self.name)

        self.configHash = self._hashJson(self.data)

    def __getitem__(self, key) :
        return self.data[key]


    def summarize(self) :
        msg = ""
        if "description" in self.data :
            msg = self.data["description"] + "\n"

        msg += "Config Hash: %s\n" % self.configHash
        
        (nameLen, imgLen) = (3, 3) # For formatting get the longest image and container names
        for containers in self.data["containers"] : 
            if len(containers["name"]) > nameLen : 
                nameLen = len(containers["name"])
            if len(containers["image"]) > imgLen : 
                imgLen = len(containers["image"])

        for containers in self.data["containers"] : 
            msg += "\n%s (%s)" % (containers["name"].ljust(nameLen), containers["image"].ljust(imgLen))

            if "gatewayConfig" in containers :
                if ("isANM" in containers["gatewayConfig"]) and containers["gatewayConfig"]["isANM"] :
                    msg += " Admin Nodemanager"

                for group in containers["gatewayConfig"]["groups"] :
                    msg += "\n    %s" % group["name"]
                    for instance in group["instances"] :
                        msg += "\n        %s" % instance["name"]
        return msg
        

    def getContainer(self, name) :
        return self._getContainer(self.data["containers"], name)


    def getRuntimeNamePrefix(self) :
        return re.sub("[\-\s_]", "", self.name).lower() + "_"

    def setRuntimeName(self, name) :
        '''
        Update the containers runtime to reflect the project name.
        '''
        nameFormat = re.sub("[\-\s_]", "", name).lower() + "_%s_1"
        for container in self.data["containers"] :
            container["runtime"] = nameFormat % container["name"].lower()


    def _processConfig(self, conifgFilePath) :
        data = self._load(conifgFilePath)
        self._imports(os.path.dirname(conifgFilePath), data)
        self._injectDefaults(data)
        self.orderContainers(data)
        return data


    def _load(self, conifgFilePath) :
        print "Loading: %s" % conifgFilePath
        with open(conifgFilePath) as cfgFile :
            jsonStr = open(conifgFilePath).read()
            data = json.loads(jsonStr, object_pairs_hook=collections.OrderedDict)
            return tmplExpandJson(data)


    def _imports(self, configDir, dataDict) :
        '''
        Expand "import" entries in the json - basic templating.
        '''
        for key, value in dataDict.iteritems() :

            if isinstance(value, dict) :
                dataDict[key] = self._imports(configDir, value)
            elif isinstance(value, list) and not isinstance(value, str) :
                updated = []
                for obj in value :
                    if (isinstance(obj, dict) or isinstance(obj, list)) and not isinstance(obj, str) :
                        updated.append(self._imports(configDir, obj))
                    else :
                        updated.append(obj)
                dataDict[key] = updated


        # No cyclical checking so be a good citizen please
        if "import" in dataDict :
            if isinstance(dataDict["import"], list) and not isinstance(dataDict["import"], str) :
                imports = dataDict["import"]
            else:
                imports = [dataDict["import"]]

            for imp in imports :
                importPath = os.path.join(configDir, imp)
                importDict = self._load(importPath)
                importDict = self._imports(os.path.dirname(importPath), importDict)
                dataDict = dict(mergedicts(importDict, dataDict))

        return dataDict


    def _isANMContainer(self, container) :
        return ("gatewayConfig" in container) and ("isANM" in container["gatewayConfig"]) and container["gatewayConfig"]["isANM"]


    def gatewayANMContainer(self) :
        # Hack - first container is anm
        anm = None
        if len(self.gatewayContainers()) > 0 and self._isANMContainer(self.gatewayContainers()[0]) :
            anm = self.gatewayContainers()[0]
        return anm


    def analyticsContainer(self) :
        anc = None
        return anc 

    def gatewayContainers(self) :
        if self.gatewayContainerList is None :
            self.gatewayContainerList = self._gatewayContainers(self.data)
        return self.gatewayContainerList


    def analyticsContainers(self) :
        if self.analyticsContainerList is None :
            self.analyticsContainerList = self._analyticsContainers(self.data)
        return self.analyticsContainerList


    def gatewayContainersByGroup(self, group) :
        match = [] # tupe (group, container)
        allGatewayContainers = self.gatewayContainers()

        for container in allGatewayContainers:
            for grp in container["gatewayConfig"]["groups"] :
                if grp["name"] == group :
                    match.append((grp, container))

        return match


    def getGatewayContainerGroup(self, containerName, groupName) :
        container = self._getContainer(self.gatewayContainers(), containerName)
        group = None

        if container :
            for grp in container["gatewayConfig"] :
                if grp["name"] == groupName :
                    group = grp;
                    break
        return grp


    def getGatewayContainerGroupInstance(self, containerName, groupName, instanceName) :
        group = self.getGatewayContainerGroup(containerName, groupName)
        instance = None

        if group :
            for inst in group["instances"] :
                if inst["name"] == instanceName :
                    instance = inst;
                    break
        return inst


    def _gatewayContainers(self, data) :
        gatewayContainerList = []
        containers = data["containers"]

        for container in containers :
            if "gatewayConfig" in container :
                # First ANM container gets pushed to head
                if self._isANMContainer(container) and (
                    len(gatewayContainerList) == 0 or not self._isANMContainer(gatewayContainerList[0])):
                    gatewayContainerList.insert(0, container)
                else :
                    gatewayContainerList.append(container)

        return gatewayContainerList


    def _analyticsContainers(self, data) :
        analyticsContainerList = []
        containers = data["containers"]

        for container in containers :
            if "analyticsConfig" in container :
                    analyticsContainerList.append(container)

        return analyticsContainerList


    def _getContainer(self, containers, name) :
        for container in containers :
            if container["name"] == name :
                return container

        return None


    def _injectDefaults(self, dataDict) :
        # this does nothing!
        dnsContainer = self._getContainer(dataDict["containers"], "dns")

        '''
        dataDict["containers"].insert(0, {
                "name" : "dns",
                "hostname" : "dns",
                "image" : "dns",
                "containerLifecycle" : {
                    "noCommit" : True
                }
            })
        '''

        for container in self._gatewayContainers(dataDict) :
            cassandraPort = 9042
            managementPort = 8085
            servicePort = 8080
            jmxPort = 7199
            trafficPort = 8065
            portalPort = 8075
            oauthServicesPort = 8089

            # Add the default DNS link
            # we don't need this now container["links"].append("dns:dns")

            if "cassandraConfig" in container :
                DEFAULT_CASSANDRA = { 
                    "cassandraPort" : str(cassandraPort),
                    "jmxPort" : str(jmxPort)
                }
                cassandraConfig = dict(mergedicts(DEFAULT_CASSANDRA, container["cassandraConfig"]))
                container["cassandraConfig"] = cassandraConfig

            updatedGroups = []
            for group in container["gatewayConfig"]["groups"] :
                # Default Group Config
                if container["gatewayConfig"]["currentVersion"] < "7.5.1" :
                    # Prior to 7.5.1 cassandra was embedded with multiple clusters.
                    DEFAULT_GATEWAY_GROUP = { "cassandraPort" : str(cassandraPort) }
                    cassandraPort += 10000
                    group = dict(mergedicts(DEFAULT_GATEWAY_GROUP, group))
                updatedGroups.append(group)

                # Default Instance Config
                updatedInstances = []
                for instance in group["instances"] :
                    if container["gatewayConfig"]["currentVersion"] < "7.5.1" :
                        # Prior to 7.5.1 cassandra was embedded (jmxPort)
                        DEFAULT_GATEWAY_GROUP_INSTANCE = {
                            "managementPort" : str(managementPort),
                            "servicePort" : str(servicePort),
                            "jmxPort" : str(jmxPort),
                            "oauthServicesPort" : str(oauthServicesPort)
                        }
                        jmxPort += 10000
                    else :
                        # External (local) cassandra
                        DEFAULT_GATEWAY_GROUP_INSTANCE = {
                            "managementPort" : str(managementPort),
                            "servicePort" : str(servicePort),
                            "oauthServicesPort" : str(oauthServicesPort)
                        }

                    DEFAULT_GATEWAY_GROUP_INSTANCE_ENVSETTINGS = {
                            "env.PORT.OAUTH2.SERVICES" : str(oauthServicesPort)                            
                        }

                    if "hasAPIManager" in group and group["hasAPIManager"] :
                        DEFAULT_GATEWAY_GROUP_INSTANCE["trafficPort"] = str(trafficPort)
                        DEFAULT_GATEWAY_GROUP_INSTANCE["portalPort"] = str(portalPort)
                        # Auto increment
                        trafficPort += 10000
                        portalPort += 10000

                    # Auto increment
                    managementPort += 10000
                    servicePort += 10000
                    oauthServicesPort += 10000

                    instance = dict(mergedicts(DEFAULT_GATEWAY_GROUP_INSTANCE, instance))

                    # Update the env settings
                    if "envSettings" in instance :
                        instance["envSettings"] = dict(mergedicts(DEFAULT_GATEWAY_GROUP_INSTANCE_ENVSETTINGS, instance["envSettings"]))
                    else :
                        instance["envSettings"] = DEFAULT_GATEWAY_GROUP_INSTANCE_ENVSETTINGS

                    updatedInstances.append(instance)

                group["instances"] = updatedInstances
            container["gatewayConfig"]["groups"]  = updatedGroups


    def orderContainers(self, data) :
        orderedNames = []
        orderedContainers = []
        data["containers"] = self.sortContainers(data["containers"], None, orderedNames, orderedContainers)
    

    def sortContainers(self, containers, container, orderedNames, orderedContainers) :
        # it ain't perfect but it'll do for now
        if container == None :
            for container in containers :
                self.sortContainers(containers, container, orderedNames, orderedContainers)

        if container["name"] in orderedNames :
            return orderedContainers

        # Add Links first
        if "links" in container and len(container["links"]) > 0 :
            for link in container["links"] :
                name = string.split(link, ":", 1)[0]
                linkContainer = self._getContainer(containers, name)

                if linkContainer is None :
                    raise Exception("Container not defined: %s" % name)
                else :
                    self.sortContainers(containers, linkContainer, orderedNames, orderedContainers)

        # Add Container
        orderedContainers.append(container)
        orderedNames.append(container["name"])

        return orderedContainers


    def _hashJson(self, data) :
        h = hashlib.sha1(json.dumps(data)).digest()
        return "".join("{:02x}".format(ord(c)) for c in h)


class Config(BuildConfig) :
    def __init__(self, conifgFilePath) :
        super(Config, self).__init__(conifgFilePath)
        # Generate the containers runtime name in docker compose (simplistic will do for now)
        nameFormat = re.sub("[\-\s_]", "", self.name).lower() + "_%s_1"
        for container in self.data["containers"] :
            container["runtime"] = nameFormat % container["name"].lower()


    def summarize(self) :
        msg = ""
        if "description" in self.data :
            msg = self.data["description"] + "\n"
        
        msg += "Config Hash: %s\n" % self.configHash
        
        (nameLen, imgLen) = (3, 3) # For formatting get the longest image and container names
        for containers in self.data["containers"] : 
            if len(containers["runtime"]) > nameLen : 
                nameLen = len(containers["runtime"])
            if len(containers["image"]) > imgLen : 
                imgLen = len(containers["image"])

        for containers in self.data["containers"] : 
            msg += "\n%s (%s)" % (containers["runtime"].ljust(nameLen), containers["image"].ljust(imgLen))

            containerHostAndIp = getContainerIpAndHost(containers["runtime"])
            if containerHostAndIp :
                msg += " - [%s %s] " % (containerHostAndIp[0], containerHostAndIp[1])

            if "gatewayConfig" in containers :
                if ("isANM" in containers["gatewayConfig"]) and containers["gatewayConfig"]["isANM"] :
                    msg += " Admin Nodemanager"

                for group in containers["gatewayConfig"]["groups"] :
                    msg += "\n    %s" % group["name"]
                    for instance in group["instances"] :
                        msg += "\n        %s" % instance["name"]
        return msg
