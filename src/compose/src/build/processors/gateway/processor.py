from ..processor import Processor
import os
import sys
import re
from core.util import *
from core.docker import *
from gatewaycommand import *

class GatewayConfigProcessor(Processor) :
    '''
    The entry point for processing the gateway configuration.
    '''
    KEY = 'gatewayConfig'

    def __init__(self, engine, config) :
        super(GatewayConfigProcessor, self).__init__(engine, GatewayConfigProcessor.KEY, config)
        self.config = config

    def initial(self, container, node) :
        print "Setting up container"

    def buildPhase1(self, container, node) :
        ConfigureNodeManager(container, self.config).execute()
        CreateInstances(container, self.config).execute()
        ConfigureEnvSettings(container, self.config).execute()
        ConfigureCassandraPorts(container, self.config).execute()
        StartInstances(container, self.config).execute()
        ConfigureEntityStore(container, self.config).execute()

    def buildPhase2(self, container, node) :
        ConfigureOAuth(container, self.config).execute()
        ConfigureAPIManager(container, self.config).execute()

    def buildPhase3(self, container, node) :
        ConfigureCassandraRepl(container, self.config).execute()
        ConfigureAPIManagerEntityStore(container, self.config).execute()
        ConfigureCassandraConsistency(container, self.config).execute()

    def final(self, container, node) :
        WaitForGateways(container, self.config).execute()
        BackupConfiguration(container, self.config).execute()

    def _getLaunchCmd(self, container, node) :
        #checking if api mgr is turned on/off for the group
        nodeGroups = container["gatewayConfig"]["groups"]
        group = nodeGroups[0] if nodeGroups else None
        if group and "hasAPIManager" in group and group["hasAPIManager"] :
            hasApiMgr = True
        else: 
            hasApiMgr = False

        return ["/scripts/manage_gateway.py --gwdir %s --backoff --all" % node["installPathCurrent"], "/scripts/manage_gateway.py --gwdir %s --start --backupRecover %s --all --nm" % (node["installPathCurrent"], ("--apimgr" if hasApiMgr else "")),
                "/scripts/manage_gateway.py --gwdir %s --all --nm --wait" % node["installPathCurrent"]]


class StopAllVshellProcessor(Processor) :
    '''
    Processord for the stop vshell command.
    '''
    KEY = 'StopAllVshell'

    def __init__(self, engine, config) :
        super(StopAllVshellProcessor, self).__init__(engine, StopAllVshellProcessor.KEY, config)
        self.config = config

    def initial(self, container, node) :
        StopAllVshell(container, self.config).execute()


