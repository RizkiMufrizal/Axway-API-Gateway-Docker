from ..processor import Processor
from core.docker import *
from cassandracommand import *

class CassandraProcessor(Processor) :
    '''
    Configure the local cassandra.
    '''
    KEY = 'cassandraConfig'

    def __init__(self, engine, config) :
        super(CassandraProcessor, self).__init__(engine, CassandraProcessor.KEY, config)
        self.config = config

    def initial(self, container, node) :
        print "Configuring Cassandra"
        ConfigureCassandraPorts(container, self.config).execute()
        ModifyCassandraJVMSettings(container, self.config).execute()
        StartCassandra(container, self.config).execute()

    #def _getLaunchCmd(self, container, node) :
    #    if self.KEY in container:
    #        return " ".join([
    #            "/scripts/manage_cassandra.py", 
    #            "--cassandraDir", container["cassandraConfig"]["cassandraDir"],
    #            "--cassandraPort", container["cassandraConfig"]["cassandraPort"],
    #            "--start"])
    #    else:
    #        None
