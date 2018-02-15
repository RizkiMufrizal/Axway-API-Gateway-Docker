import uuid
import re
from core.docker import *
from core.util import *
from core.config import *
from ..util.command import *
from ....scripts.lib.scriptutil import *
import os

class BackupConfiguration(Command) :
    def __init__(self, container, config) :
        super(BackupConfiguration, self).__init__(config)            
        backupConfCmd = [
            "/scripts/backup.py", 
            "--srcdir", os.path.join(container["gatewayConfig"]["installPathCurrent"],"conf"), 
            "--name", "conf"] 
        backupGroupsCmd = [
            "/scripts/backup.py", 
            "--srcdir", os.path.join(container["gatewayConfig"]["installPathCurrent"],"groups"), 
            "--name","groups"] 
        self.cmds.append((container["runtime"], backupConfCmd, None))
        self.cmds.append((container["runtime"], backupGroupsCmd, None))

class ConfigureNodeManager(Command) :
    def __init__(self, container, config) :
        super(ConfigureNodeManager, self).__init__(config)
        anmContainer = self.config.gatewayANMContainer()

        additionalArgs = []
        if container["gatewayConfig"].get("signAlg", None) :
            additionalArgs.extend(["--sign_alg", container["gatewayConfig"]["signAlg"]])

        if container["gatewayConfig"].get("domainName", None) :
            additionalArgs.extend(["--domain_name", container["gatewayConfig"]["domainName"]])

        if container["gatewayConfig"].get("domainPassphrase", None) :
            additionalArgs.extend(["--domain_passphrase", container["gatewayConfig"]["domainPassphrase"]])

        if container["gatewayConfig"].get("keyPassphrase", None) :
            additionalArgs.extend(["--key_passphrase", container["gatewayConfig"]["keyPassphrase"]])

        if container["gatewayConfig"].get("port", None) :
            additionalArgs.extend(["--port", container["gatewayConfig"]["port"]])

        if container["gatewayConfig"].get("nmName", None) :
            additionalArgs.extend(["--name", container["gatewayConfig"]["nmName"]])

        if container["gatewayConfig"].get("metricsEnabled", None) :
            additionalArgs.extend(["--metrics_enabled", container["gatewayConfig"]["metricsEnabled"]])

        if container["gatewayConfig"].get("metricsDburl", None) :
            additionalArgs.extend(["--metrics_dburl", container["gatewayConfig"]["metricsDburl"]])

        if container["gatewayConfig"].get("metricsDbuser", None) :
            additionalArgs.extend(["--metrics_dbuser", container["gatewayConfig"]["metricsDbuser"]])

        if container["gatewayConfig"].get("metricsDbpass", None) :
            additionalArgs.extend(["--metrics_dbpass", container["gatewayConfig"]["metricsDbpass"]])

        if anmContainer["name"] != container["name"] and container["gatewayConfig"].get("isANM", False) :
            additionalArgs.extend(["--secondary_anm"])

	hostnameServer = container["gatewayConfig"]["IP"] + " " + container["gatewayConfig"]["node"]
        os.system("docker exec " + container["runtime"] + " bash -c 'echo \"" + hostnameServer + "\" >> /etc/hosts'")

        scriptcmd = [
            "/scripts/configure_nodemanager.py", 
            "--gwdir", container["gatewayConfig"]["installPathCurrent"], 
            "--anm_host", container["gatewayConfig"]["ANM"],
            "--current_version", container["gatewayConfig"]["currentVersion"]
            ] + additionalArgs
        self.cmds.append((container["runtime"], scriptcmd, None))


class CreateInstances(Command) :
    createdGroups = []

    def __init__(self, container, config) :
        super(CreateInstances, self).__init__(config)

        additionalGatewayArgs = []
        if container["gatewayConfig"].get("domainPassphrase", None) :
            additionalGatewayArgs.extend(["--domain_passphrase", container["gatewayConfig"]["domainPassphrase"]])

        for group in container["gatewayConfig"]["groups"] :
            additionalGroupArgs = []
            if group.get("passphrase", None) :
                additionalGroupArgs.extend(["--passphrase", group["passphrase"]])

            for instance in group["instances"] :
                additionalArgs = additionalGatewayArgs + additionalGroupArgs
                if not group["name"] in CreateInstances.createdGroups :
                    # Group passphrase has to be set after the creation of the first instance.
                    additionalArgs.append("--first")
                    CreateInstances.createdGroups.append(group["name"])
                
                scriptcmd = [
                    "/scripts/create_instance.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "-g", group["name"],
                    "-n", instance["name"],
                    "-m", instance["managementPort"],
                    "-s", instance["servicePort"],
                    "--current_version", container["gatewayConfig"]["currentVersion"],
                    ] + additionalArgs
                self.cmds.append((container["runtime"], scriptcmd, None))


class ConfigureEnvSettings(Command) :
    def __init__(self, container, config) :
        super(ConfigureEnvSettings, self).__init__(config)

        for group in container["gatewayConfig"]["groups"] :
            for instance in group["instances"] :

                if not "envSettings" in instance or len(instance["envSettings"]) == 0 :
                    continue

                propArgs = []
                envSettings = instance["envSettings"]
                for key in envSettings.keys() :
                    propArgs.extend(["-p", "%s=%s" % (key, str(envSettings.get(key)))])

                scriptcmd = [
                    "/scripts/configure_envsettings.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "-g", group["name"],
                    "-n", instance["name"]] + propArgs
                self.cmds.append((container["runtime"], scriptcmd, None))


class ConfigureCassandraPorts(Command) :
    seed_hosts = {}

    def __init__(self, container, config) :
        super(ConfigureCassandraPorts, self).__init__(config)

        if container["gatewayConfig"]["currentVersion"] < "7.2.0" :
            return
        
        if container["gatewayConfig"]["currentVersion"] < "7.5.1" :
            #
            # Legacy Embedded Cassandra Setup
            #
            for group in container["gatewayConfig"]["groups"] :
                for instance in group["instances"] :
                    if group["name"] not in ConfigureCassandraPorts.seed_hosts :
                        # First group with an instance is the seed host
                        ConfigureCassandraPorts.seed_hosts[group["name"]] = container["hostname"]

                    scriptcmd = [
                        "/scripts/configure_cassandraports_embedded.py", 
                        "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                        "--seed_host", ConfigureCassandraPorts.seed_hosts[group["name"]],
                        "-g", group["name"],
                        "-n", instance["name"],
                        "--cassandraPort", group["cassandraPort"],
                        "--jmxPort", instance["jmxPort"]]
                    self.cmds.append((container["runtime"], scriptcmd, None))


class StartInstances(Command) :
    def __init__(self, container, config) :
        super(StartInstances, self).__init__(config)
        for group in container["gatewayConfig"]["groups"] :
            for instance in group["instances"] :
                scriptcmd = [
                    "/scripts/manage_gateway.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "--start", 
                    "-g", group["name"],
                    "-n", instance["name"]]
                self.cmds.append((container["runtime"], scriptcmd, None))


class ConfigureAPIManager(Command) :
    def __init__(self, container, config) :
        super(ConfigureAPIManager, self).__init__(config)
       
        for group in container["gatewayConfig"]["groups"] :
            if not "hasAPIManager" in group or not group["hasAPIManager"] :
                continue

            if "hasOAuth" in group and group["hasOAuth"] :
                raise Exception("Both OAuth and API Manager being installed in group....why???")

            for instance in group["instances"] :
                scriptcmd = [
                    "/scripts/configure_apimanager.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "-g", group["name"],
                    "-n", instance["name"],
                    "--version", container["gatewayConfig"]["currentVersion"],
                    "--trafficPort", instance["trafficPort"],
                    "--portalPort", instance["portalPort"]]
                self.cmds.append((container["runtime"], scriptcmd, None))


class ConfigureOAuth(Command) :
    def __init__(self, container, config) :
        super(ConfigureOAuth, self).__init__(config)
       
        for group in container["gatewayConfig"]["groups"] :
            if not "hasOAuth" in group or not group["hasOAuth"] :
                continue

            for instance in group["instances"] :
                additionalArgs = []

                if instance.get("oauthAdmin", None) is not None :
                    additionalArgs.extend(["--admin", instance.get("oauthAdmin")])
                if instance.get("oauthAdminPassword", None) is not None :
                    additionalArgs.extend(["--adminpw", instance.get("oauthAdminPassword")])
                if instance.get("oauthType", None) is not None :
                    additionalArgs.extend(["--type", instance.get("oauthType")])

                scriptcmd = [
                    "/scripts/configure_oauth.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "-g", group["name"],
                    "-n", instance["name"],
                    "--version", container["gatewayConfig"]["currentVersion"],
                    "--port", instance.get("oauthServicesPort")] + additionalArgs
                self.cmds.append((container["runtime"], scriptcmd, None))


class ConfigureCassandraRepl(Command) :
    masterContainer = {}

    def __init__(self, container, config) :
        super(ConfigureCassandraRepl, self).__init__(config)

        if container["gatewayConfig"]["currentVersion"] < "7.2.0" :
            return

        if container["gatewayConfig"]["currentVersion"] > "7.5.1" :
            # Cassandra is no longer embedded.
            return

        # Set replication factor
        for group in container["gatewayConfig"]["groups"] :
            # Need to update the replication factor on the first node
            # and then nodetool repair/ring all containers with this group

            if group["name"] not in ConfigureCassandraRepl.masterContainer :
                # First group with an instance is the seed host
                ConfigureCassandraRepl.masterContainer[group["name"]] = container["hostname"]
                print "[Container: %s][Group: %s] Configuring Replication on host: %s" % (container["name"], group["name"], ConfigureCassandraRepl.masterContainer[group["name"]])
            else : 
                # This group is done
                print "[Container: %s][Group: %s] Replication already configured on host: %s" % (container["name"], group["name"], ConfigureCassandraRepl.masterContainer[group["name"]])
                continue

            hostsArgs = []
            containersWithGroup = self.config.gatewayContainersByGroup(group["name"])

            if len(containersWithGroup) <= 1 :
                print "No replication required for group %s as it is a single node group." % group["name"]
                continue

            for (replicaGroup, replicaContainer) in containersWithGroup :
                for instance in replicaGroup["instances"] :
                    groupHostName = self._getGroupHostName(replicaContainer["hostname"], replicaGroup["name"])
                    hostsArgs.extend(["--host", "%s:%s" % (groupHostName, instance["jmxPort"])])

            if "replicationFactor" in group :
                replicationFactor = group["replicationFactor"]
            else :
                replicationFactor = len(containersWithGroup)

            gwdir = container["gatewayConfig"]["installPathCurrent"]

            groupHostName = self._getGroupHostName(container["hostname"], group["name"])
            scriptcmd = [
                    "/scripts/configure_cassandrarepl_embedded.py", 
                    "--gwdir", gwdir,
                    "--primary_host", groupHostName,
                    "--primary_rpc_port", group["cassandraPort"],
                    "--group", group["name"],
                    "--instance", group["instances"][0]["name"],
                    "--repl_factor", str(replicationFactor)] + hostsArgs
            self.cmds.append((container["runtime"], scriptcmd, None))


    def _getGroupHostName(self, hostname, group) :
        return "%s_%s" % (hostname, re.sub("[,\-\s\*\.=#&\^%\$]", "", group).lower())


class ConfigureEntityStore(Command) :
    masterContainer = {}

    def __init__(self, container, config) :
        super(ConfigureEntityStore, self).__init__(config)

        if container["gatewayConfig"]["currentVersion"] < "7.2.0" :
            return # TODO: Support Configure Entity Store on 7.1.x

        for group in container["gatewayConfig"]["groups"] :
            # only need to update one instance per group as it's
            # deployed to the group at the end of this.

            if group["name"] not in ConfigureEntityStore.masterContainer :
                # First group with an instance is the seed host
                ConfigureEntityStore.masterContainer[group["name"]] = container["hostname"]
                print "[Container: %s][Group: %s] Configuring Entity Store on host: %s" % (container["name"], group["name"], ConfigureEntityStore.masterContainer[group["name"]])
            else : 
                # This group is done
                print "[Container: %s][Group: %s] Entity Store already configured on host: %s" % (container["name"], group["name"], ConfigureEntityStore.masterContainer[group["name"]])
                continue

            instance = getFirstInstanceInGroupIfExists(group, container["name"])
            if not instance:
                continue 

            args = []

            if container["gatewayConfig"]["currentVersion"] >= "7.5.1" :
                # 7.5.1+ use an external cassandra. (TODO: Support non-local/failover list)
                args.extend(["--cassandraHost", container["hostname"]])
                
            if container["gatewayConfig"]["currentVersion"] >= "7.5.0" :
                # 7.5.0+ replication factor is set in ES
                containersWithGroup = self.config.gatewayContainersByGroup(group["name"])
                if "replicationFactor" in group :
                    replicationFactor = group["replicationFactor"]
                else :
                    replicationFactor = len(containersWithGroup)
                args.extend(["--repl_factor", str(replicationFactor)])


            if len(args) > 0 :
                if group.get("passphrase", None) :
                    args.extend(["--passphrase", group["passphrase"]])

                scriptcmd = [
                        "/scripts/configure_entitystore.py", 
                        "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                        "-g", group["name"],
                        "-n", instance["name"],
                        "-s", instance["servicePort"]] + args

                self.cmds.append((container["runtime"], scriptcmd, None))


class ConfigureAPIManagerEntityStore(Command) :
    '''
    Configure addition entity store settings that api manager added.
    '''
    masterContainer = {}

    def __init__(self, container, config) :
        super(ConfigureAPIManagerEntityStore, self).__init__(config)

        if container["gatewayConfig"]["currentVersion"] < "7.2.2" :
            return # No API Manager

        for group in container["gatewayConfig"]["groups"] :
            if not group.get("hasAPIManager", False) :
                continue

            # only need to update one instance per group as it's
            # deployed to the group at the end of this.
            if group["name"] not in ConfigureAPIManagerEntityStore.masterContainer :
                # First group with an instance is the seed host
                ConfigureAPIManagerEntityStore.masterContainer[group["name"]] = container["hostname"]
                print "[Container: %s][Group: %s] Configuring API Manager Entity Store settings on host: %s" % (container["name"], group["name"], ConfigureAPIManagerEntityStore.masterContainer[group["name"]])
            else : 
                # This group is done
                print "[Container: %s][Group: %s] API Manager Entity Store settings  already configured on host: %s" % (container["name"], group["name"], ConfigureAPIManagerEntityStore.masterContainer[group["name"]])
                continue

            instance = getFirstInstanceInGroupIfExists(group, container["name"])
            if not instance:
                continue 

            args = []
            if "hasAPIManager" in group and group["hasAPIManager"] :
                if group.get("useEmbeddedLdap", False) :
                    args.extend(["--smtp"])
                else :
                    args.extend(["--ldap", "--smtp"])

            if group.get("passphrase", None) :
                args.extend(["--passphrase", group["passphrase"]])

            scriptcmd = [
                    "/scripts/configure_entitystore.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "-g", group["name"],
                    "-n", instance["name"],
                    "-s", instance["servicePort"]] + args

            self.cmds.append((container["runtime"], scriptcmd, None))

class ConfigureCassandraConsistency(Command) :
    masterContainer = {}

    def __init__(self, container, config) :
        super(ConfigureCassandraConsistency, self).__init__(config)

        if container["gatewayConfig"]["currentVersion"] < "7.2.0" :
            return

        for group in container["gatewayConfig"]["groups"] :
            # only need to update one instance per group as it's
            # deployed to the group at the end of this.

            if group["name"] not in ConfigureCassandraConsistency.masterContainer :
                ConfigureCassandraConsistency.masterContainer[group["name"]] = container["hostname"]
                print "[Container: %s][Group: %s] Configuring Cassandra Consistency on host: %s" % (container["name"], group["name"], ConfigureCassandraConsistency.masterContainer[group["name"]])
            else : 
                # This group is done
                print "[Container: %s][Group: %s] Cassandra Consistency already configured on host: %s" % (container["name"], group["name"], ConfigureCassandraConsistency.masterContainer[group["name"]])
                continue

            instance = getFirstInstanceInGroupIfExists(group, container["name"])
            if not instance:
                continue 

            args = []
            if "readConsistencyLevel" in group :
                args.extend(["--readConsistencyLevel", group["readConsistencyLevel"]])
            if "writeConsistencyLevel" in group :
                args.extend(["--writeConsistencyLevel", group["writeConsistencyLevel"]])
            if group.get("passphrase", None) :
                args.extend(["--passphrase", group["passphrase"]])
                
            scriptcmd = [
                    "/scripts/configure_cassandraconsistency.py", 
                    "--gwdir", container["gatewayConfig"]["installPathCurrent"],
                    "-g", group["name"],
                    "-n", instance["name"],
                    "-s", instance["servicePort"]] + args

            self.cmds.append((container["runtime"], scriptcmd, None))

class StopAllVshell(Command) :
    def __init__(self, container, config) :
        super(StopAllVshell, self).__init__(config)
       
        scriptcmd = [
            "/scripts/manage_gateway.py", 
            "--gwdir", container["gatewayConfig"]["installPathCurrent"],
            "--stop", 
            "--all", "--nm"]
        self.cmds.append((container["runtime"], scriptcmd, None))


class WaitForGateways(Command) :
    def __init__(self, container, config) :
        super(WaitForGateways, self).__init__(config)

        scriptcmd = [
            "/scripts/manage_gateway.py", 
            "--gwdir", container["gatewayConfig"]["installPathCurrent"],
            "--wait",  "--all", "--nm"]
        self.cmds.append((container["runtime"], scriptcmd, None))
