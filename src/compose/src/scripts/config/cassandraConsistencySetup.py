# Setup API Manager for testing with External SMTP Server
import os
import util
import tempfile
import sys
from com.vordel.es.xes import PortableESPKFactory
from com.vordel.es import EntityStoreException

def configure(es, **kwargs) :
    print '--Configuring Entity Store Read/Write consistency'
    __configureConsistency(es, "API Server", kwargs["readConsistencyLevel"], kwargs["writeConsistencyLevel"])
    __configureConsistency(es, "API Portal", kwargs["readConsistencyLevel"], kwargs["writeConsistencyLevel"])

def __configureConsistency(es, kpsCollection, readConsistencyLevel, writeConsistencyLevel):
    kpsCassandraDatasourcePK = PortableESPKFactory.newInstance().createPortableESPK("""
        <key type='KPSRoot'><id field='name' value='Key Property Stores'/>
            <key type='KPSPackage'><id field='name' value='%s'/>
                <key type='KPSDataSourceGroup'><id field='name' value='Data Sources'/>
                    <key type='KPSCassandraDataSource'><id field='name' value='Cassandra Storage'/></key>
                </key>
            </key>
        </key>""" % kpsCollection)
    try :
        kpsCassandraDatasource = es.getEntity(kpsCassandraDatasourcePK)
        kpsCassandraDatasource.setStringField("readConsistencyLevel", readConsistencyLevel)
        kpsCassandraDatasource.setStringField("writeConsistencyLevel", writeConsistencyLevel)
        es.updateEntity(kpsCassandraDatasource)
    except EntityStoreException, ex:
        print >> sys.stderr, "Couldn not configure consistencey for %s: %s " % (kpsCollection, ex.getMessage())
