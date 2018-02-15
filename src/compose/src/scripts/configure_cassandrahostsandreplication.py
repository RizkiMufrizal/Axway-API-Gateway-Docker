#!/usr/bin/env python2.7
'''
Script for modify entity store cassandra hosts setting for each gw 
'''
import os
import sys
from optparse import OptionParser
from com.vordel.es import EntityStoreException
from esapi import EntityStoreAPI


def parseOptions() :
    global options
    global es

    parser =  OptionParser()
    parser.add_option("--esFile")
    parser.add_option("--passphrase", default="")
    parser.add_option("--hostAndPort", action='append',  dest='hostportvals',help='specify host and port -  for example localhost:9042')

    (options, args) = parser.parse_args()

    if not os.path.isfile(options.esFile) :
        parser.error("A valid entity store file location was not specified: %s" % options.esFile)

    federatedFilePrefix  = "federated:file:"
    if federatedFilePrefix not in options.esFile:
        options.esFile = federatedFilePrefix + options.esFile

    try:
        print ("attempting to connect to entity store at url:%s" % options.esFile)
        es = EntityStoreAPI.create(options.esFile, options.passphrase, {})
    except ValueError, val:
        print ("Problem connecting to store. Unable to continue: ", val)
        exit(1)

def modifyCassandraSettings():

    try:
        print ("Looking for default CassandraSettings entity")
        defaultSettingsEntity = es.get("/[CassandraSettings]name=Cassandra Settings")
        if defaultSettingsEntity is not None:
            print ("Looking for entities of type CassandraServer in the CassandraSettings entity")
            cassandraServersPKs = es.listChildren(defaultSettingsEntity.getPK(), es.es.getTypeForName("CassandraServer"))
            if cassandraServersPKs:
                print ("Found entities of type CassandraServer in the CassandraSettings entity")
                for cassandraServerPK in cassandraServersPKs:
                    cassandraServerEntity = es.getEntity(cassandraServerPK)
                    print ("Deleting CassandraServer entity with name:%s" % cassandraServerEntity.getStringValue("name"))
                    es.cutEntity(cassandraServerEntity)
        else:
            print ("No CassandraSettings reference found - unable to continue")
            exit (1)

        for hostAndPort in options.hostportvals:
            host = hostAndPort.split(":")[0]
            port = hostAndPort.split(":")[1]

            if not host or not port:
                parser.error("host:port not passed in correctly")

            server = es.createEntity("CassandraServer")
            server.setStringField("name", host)
            server.setStringField("host", host)
            portAsInt = int(port)
            server.setIntegerField("port",portAsInt)
            es.addEntity(defaultSettingsEntity, server)
            print ("Added a Cassandra server entity with host %s and port %d to the CassandraSettings entity" % (host, portAsInt))
       
        #Now as we know we have valid hosts and ports, we determine the amount of hosts and set the replication factor. 
        keyspaceReplicationFactor = len(options.hostportvals)
        defaultSettingsEntity.setIntegerField("keySpaceReplicationFactor", keyspaceReplicationFactor)
        es.updateEntity(defaultSettingsEntity)
        print ("Keyspace replication factor set to %d" %keyspaceReplicationFactor )
        

    except EntityStoreException, ex:
        print ("Problem with entitystore operation: %s" % ex.getMessage())
        exit(1)

    finally:
        es.close()


if __name__ == "__main__":
    parseOptions()
    modifyCassandraSettings()

