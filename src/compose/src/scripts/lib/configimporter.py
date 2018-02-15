# JYTHON: Setup API Manager for testing with External LDAP directory
import os
import util
import imp
import tempfile
from optparse import OptionParser
import configutil

from vtrace import Tracer
from esapi import EntityStoreAPI
from topologyapi import TopologyAPI
from nmdeployment import NodeManagerDeployAPI

from com.vordel.api.topology.model import Topology
from com.vordel.es.xes import PortableESPKFactory

PRE740=False
try:
    # pre 740
    from com.vordel.api.deployment.model import DeploymentArchive
    PRE740=True
except ImportError:
    # 740 onwards...
    from com.vordel.archive.fed import DeploymentArchive
    from com.vordel.api.nm import NodeManagerAPIException, NodeManagerClient


def parseOptions() :
    parser = OptionParser()
    parser.add_option("--username", default="apiadmin")
    parser.add_option("--password", default="changeme")
    parser.add_option("-g", "--group")
    parser.add_option("-n", "--instance")
    parser.add_option("--passphrase", default='', help="The group passphrase.")
    parser.add_option("-f", "--file", action="append", type="string", dest="files")

    (options, args) = parser.parse_args()

    if not options.group :
        parser.error("No group specified.")

    if not options.instance :
        parser.error("No instance specified.")

    if len(options.files) == 0 :    
        parser.error("No fragments specified.")

    params = {}
    for arg in args :
        (k,v) = arg.split('=', 1)
        if k in params :
            if type(params[k]) == type(list()) :
                params[k].append(v)
            else :
                params[k] = [params[k], v]
        else :
            params[k]=v

    return (options, params)


class ConfigImporter(object) :

    def __init__(self, options, params) :
        self.options = options
        self.params = params
        (scheme, host, port) = configutil.getAdminNodeManagerSchemeHostPortFromTopology()
        self.nm_apiURL = "%s://%s:%s/api" % (scheme, host, port)
        if PRE740 == False:
            truststoreFile=None
            truststorePassword=None
            self.cc = NodeManagerClient.createConnectionContext(self.nm_apiURL,
                self.options.username, self.options.password,
                truststoreFile, truststorePassword)
        self.loadTopology()

    def loadTopology(self) :
        try:
            # first lets see if we can get the topology
            if PRE740:
                topologyAPI = TopologyAPI(self.nm_apiURL, self.options.username, self.options.password)
            else:
                topologyAPI = TopologyAPI(self.cc, False)
            topology = topologyAPI.getTopology()

            # Get the first Group and API Server in Topology
            if self.options.group == "":
                self.group = ArrayList(topology.getGroups(Topology.ServiceType.gateway)).get(0)
            else:
                self.group = topology.getGroupByName(self.options.group)
            if self.options.instance == "":
                self.service = ArrayList(self.group.getServices()).get(0)
            else:
                self.service = self.group.getServiceByName(self.options.instance)
        except IndexError, ex:
            raise Exception("Error getting topology. Has an API Server been configured? %s" % str(ex))


    def updateDeploymentArchive(self) :
        print '-Updating Deployment Archive'
        if PRE740:
            deployment = NodeManagerDeployAPI(self.nm_apiURL, self.options.username, self.options.password)
        else:
            deployment = NodeManagerDeployAPI(self.cc, False)

        archive = deployment.getDeploymentArchiveForServerByName(self.group.getName(), self.service.getName())
        es = deployment.getArchiveEntityStore(archive, self.options.passphrase)

        outputDir = tempfile.gettempdir() 
        componentEntityStores = archive.getComponentEntityStores(outputDir)
        primaryStore = EntityStoreAPI.wrap(componentEntityStores.get("PrimaryStore"), self.options.passphrase)

        try :
            newArchive = DeploymentArchive("%s/%s" % (outputDir, archive.getId()), archive.getPolicyProperties(), archive.getEnvironmentProperties())
            es = EntityStoreAPI.wrap(newArchive.getEntityStore(), self.options.passphrase)
        finally :
            primaryStore.close()

        try :
            self._importFragments(es)

            print '--Redeploying Updated Gateway'
            self.reportDeploy(Tracer(Tracer.INFO), deployment, self.group.getName(), archive, es)
        finally :
            es.close()


    def _importFragments(self, es) :
        for afile in self.options.files :
            if ".py" == str(os.path.splitext(os.path.basename(afile))[1]) :
                self._executConfigScript(es, afile)
            else :
                self._importXMLFragment(es, afile)

    def _importXMLFragment(self, es, fragment) :
        print "Importing Fragment: " + fragment
        es.importConf(fragment)

    def _executConfigScript(self, es, script) :
        print "Executing Config Script: " + script
        py = imp.load_source('temp.script', script)
        py.configure(es, **params)


    def reportDeploy(self, t, dep, group, archive, es):
        dep.updateArchiveConfiguration(archive, es)
        res = dep.deployToGroup(group, archive)     

        if isinstance(res, list) :
            for depRes in res :
                self.reportDeployErrors(t, depRes)
        else :
            self.reportDeployErrors(t, res)

    def reportDeployErrors(self, t, res) :
        failurecount = res.getErrorCount()
        if not res.getStatus():
            t.error("%i failures have occurred. " % failurecount)
            t.error("Failed to deploy: Reason: "+ res.getFailureReason())
        else:
            if failurecount > 0:
                if failurecount == 1: errString = "issue"
                else:                 errString = "issues"
                t.info("The deployment succeeded but %i %s recorded. " % (res.getErrorCount(), errString))
                for traceRecord in res.getTraceData().getTraceRecords():
                    if traceRecord.getLevel() <= 2:
                        t.info(traceRecord.getMessage())

# Mainline
if __name__ == "__main__":
    (options, params) = parseOptions()
    ConfigImporter(options, params).updateDeploymentArchive()
