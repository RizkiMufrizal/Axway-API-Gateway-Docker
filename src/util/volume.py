#!/usr/bin/env python2.7
#
#
"""Axway APIGateway Docker Volume Management Tool

Usage:
    volume.py --create --nodeName <nodeName> 
    volume.py --delete --nodeName <nodeName>

Options:
    --create               Create a set of volumes required to run apigw
    --delete               Delete a set of volumes required to run apigw
    --nodeName <nodeName>  Sets the nodename used as a prefix for the container
"""

import sys
import os
import argparse
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "../core/src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../compose/src"))

from scripts.lib.scriptutil import *
from core.util import banner

VERSION = "0.1.0"
GW_VOLUMES = ["CONF_DATA","TRACE_DATA","LOGS_DATA","EVENTS_DATA","GROUP_DATA","USER_DATA"]

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_const", dest="action", const="create")
    parser.add_argument("--delete", action="store_const", dest="action", const="delete")
    parser.add_argument("--driver", default="docker")
    parser.add_argument("--nodeName", help="Specific nodeName")

    (options, unknown) = parser.parse_known_args()

    if not options.nodeName :
        parser.error("No node name specified.")


def createVolumes(nodeName,driver):
 	banner("Creating volumes for %s on %s " % (nodeName,driver))
 	for volSuffix in GW_VOLUMES:
 		volName = "%s_%s" % (nodeName,volSuffix)
 		createVolumeAgnostic(nodeName,volName,driver)

def createVolumeAgnostic(nodeName,volName,driver):
    print ("Creating volume %s" % volName)      
    if not volumeExists(nodeName,volName,driver):            
        if createVolume(nodeName,volName,driver):
            print "Volume %s created" % volName
        else:
            print "Failed to create %s " % volName
    else:
        print "Volume %s already exists" % volName

def deleteVolumes(nodeName,driver):
    banner("Deleting volumes for %s on %s" % (nodeName,driver))
    for volSuffix in GW_VOLUMES:
    	volName = "%s_%s" % (nodeName,volSuffix)
    	print ("Deleting volume %s" % volName)
        if volumeExists(nodeName,volName,driver):
        	
            if deleteVolume(volName,driver):
        		print "Volume %s deleted" % volName
            else:
                print "Failed to delete %s " % volName
        else: 
        	print "Volume %s does not exists" % volName 

def createVolume(nodeName,volName,driver):
    if driver == "docker":
	    return not execute("docker",["volume","create","--name","%s" % volName],noOutput=True)
    elif driver == "bluemix":
        if not fileShareExists(nodeName):
            createBluemixFs(nodeName)
        return not execute("cf",["ic","volume","create",volName,bluemixFsName(nodeName)], failOnError=False,noOutput=True)

def bluemixFsName(nodeName):
    return "apigw_%s" %nodeName 

def createBluemixFs(nodeName):

    rc = execute("cf",["ic","volume","fs-create",bluemixFsName(nodeName),"20","4"], failOnError=False,noOutput=True)
    while True:
        if fileShareExists(nodeName):
            break
        print "Waiting for Bluemix Fileshare"
        time.sleep( 2 )
    return rc 

def volumeExists(nodeName,volName,driver):
    if driver == "docker":
	    return not execute("docker",["volume","inspect",volName], failOnError=False,noOutput=True) 
    elif driver == "bluemix":
        return fileShareExists(nodeName) and bluemixVolumeExists(volName)        
        
                 

def fileShareExists(nodeName):
    return not execute("cf",["ic","volume","fs-inspect",bluemixFsName(nodeName)], failOnError=False,noOutput=True)     


def bluemixVolumeExists(volName):
    return not execute("cf",["ic","volume","inspect",volName], failOnError=False,noOutput=True) 

def deleteVolume(volName,driver):
    if driver == "docker":
 	    return not execute("docker",["volume","rm",volName],noOutput=True)
    elif driver == "bluemix":
        return not execute("cf",["ic","volume","rm",volName], failOnError=False,noOutput=True) 

def manageVolumes():
	if options.action == 'create' :
		createVolumes(options.nodeName,options.driver)	
	elif options.action == 'delete' :
		deleteVolumes(options.nodeName,options.driver)

if __name__ == "__main__":
    parseOptions()
    manageVolumes()
