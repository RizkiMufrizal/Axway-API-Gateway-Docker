# Setup API Manager for testing with External SMTP Server
import os
import util
import tempfile
import string
import sys
from com.vordel.es.xes import PortableESPKFactory
from com.vordel.es import EntityStoreException

def configure(es, **kwargs) :
    print '--Configuring Entity Store replication factor'

    if kwargs["cassandraHosts"] and type(kwargs["cassandraHosts"]) != type(list()) :
        cassandraHosts = [kwargs["cassandraHosts"]]
    else :
        cassandraHosts = kwargs["cassandraHosts"]
    _configureServer(es, kwargs["repl_factor"], cassandraHosts )


def _configureServer(es, replicationFactor, cassandraHosts = []):
    kpsCassandraSettingsPK = PortableESPKFactory.newInstance().createPortableESPK("""
        <key type='CassandraSettings'><id field='name' value='Cassandra Settings'/></key>""")
    try :
        kpsCassandraSettings = es.getEntity(kpsCassandraSettingsPK)

        if replicationFactor is not None :
            print "Setting Replication factor to: %s" % str(replicationFactor)
            kpsCassandraSettings.setStringField("keySpaceReplicationFactor", replicationFactor)
            es.updateEntity(kpsCassandraSettings)

        # Setup the server details
        if len(cassandraHosts) > 0 :
            defaultServer = es.get("/[CassandraSettings]name=Cassandra Settings/[CassandraServer]host=localhost,port=9042")
            if defaultServer is not None:
                es.es.deleteEntity(defaultServer.getPK())

            # add servers
            for cassandraHost in cassandraHosts:
                (host, port) = _splitHostPort(cassandraHost)
                server = es.createEntity("CassandraServer")
                server.setStringField("name", host)
                server.setStringField("host", host)
                server.setIntegerField("port", port)
                es.addEntity(kpsCassandraSettings, server)
                print ("Added Cassandra server details: %s:%d" % (host, port))
    except EntityStoreException, ex:
        print >> sys.stderr, "Could not configure cassandra: %s " % (ex.getMessage())


def _splitHostPort(host) :
    toks = string.split(host, ":", 1)
    return (toks[0], 9042 if len(toks) < 2 else int(toks[1]))
