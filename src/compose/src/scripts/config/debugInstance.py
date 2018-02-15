# Setup instance to run in debug mode 
import os

def configure(es, **kwargs) :
    print '--Configuring Entity Store in DEBUG mode'
    gwConfig = es.get("/[SystemSettings]name=Default System Settings")
    gwConfig.setStringField("tracelevel", "DEBUG")
    es.updateEntity(gwConfig)

