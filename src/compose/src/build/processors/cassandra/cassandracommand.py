import uuid
import re
from core.docker import *
from core.util import *
from core.config import *
from ..util.command import *


class ConfigureCassandraPorts(Command) :
    seed_host = None

    def __init__(self, container, config) :
        super(ConfigureCassandraPorts, self).__init__(config)


        if container["cassandraConfig"].get("seedHost",None) :
            self.seed_host = container["cassandraConfig"]["seedHost"]
        else:
            self.seed_host  = container["hostname"]             
            
        scriptcmd = [
            "/scripts/configure_cassandraports.py", 
            "--cassandraDir", container["cassandraConfig"]["cassandraDir"],
            "--seed_host", self.seed_host,
            "--cassandraPort", container["cassandraConfig"]["cassandraPort"]]        
        self.cmds.append((container["runtime"], scriptcmd, None))

class ModifyCassandraJVMSettings(Command) :
    def __init__(self, container, config) :
        super(ModifyCassandraJVMSettings, self).__init__(config)

        scriptcmd = [
            "/scripts/configure_cassandrajvmheap.xml", 
            "--cassandraDir", container["cassandraConfig"]["cassandraDir"]]
        self.cmds.append((container["runtime"], scriptcmd, None))


class StartCassandra(Command) :
    seed_host = None

    def __init__(self, container, config) :
        super(StartCassandra, self).__init__(config)
        scriptcmd = [
            "/scripts/manage_cassandra.py", 
            "--cassandraDir", container["cassandraConfig"]["cassandraDir"],
            "--cassandraPort", container["cassandraConfig"]["cassandraPort"],
            "--start"]
        self.cmds.append((container["runtime"], scriptcmd, None))
