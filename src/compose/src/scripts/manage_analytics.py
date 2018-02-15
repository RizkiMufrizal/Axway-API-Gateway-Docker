#!/usr/bin/env python2.7
'''
Script for starting/stopping instances.
'''
import os
import socket
import signal
import time
import threading
import argparse
from lib.scriptutil import *
from lib.ipalias import *

import subprocess
from subprocess import PIPE

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")
    
    parser.add_argument("--start", action="store_const", dest="action", const="start")
    parser.add_argument("--stop", action="store_const", dest="action", const="stop")
    parser.add_argument("--wait", action="store_const", dest="action", const="wait")
    parser.add_argument("--configure", action="store_const", dest="action", const="configure")

    parser.add_argument("--dburl", "--dburl", help="DB URL")
    parser.add_argument("--dbuser", "--dbuser", help="DB USER") 
    parser.add_argument("--dbpass", "--dbpass", help="DB PASS") 
    parser.add_argument("--current_version", "--current_version", help="Version") 

    parser.add_argument("-b", "--block", action="store_true", help="Don't exit after starting.")

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)
    
def manageAnalytics() :
    if options.action == 'start' :
        startAnalytics(options.gwdir)

    elif  options.action == 'stop' :
        print "Not supported yet"

    elif  options.action == 'wait' :
        print "Not supported yet"

    elif  options.action == 'configure' :
        configureAnalytics(options.gwdir, options.dburl, options.dbuser, options.dbpass)


def configureAnalytics(gwdir, dburl, dbuser, dbpass) :
    banner("Configuring Analytics on %s" % (hostname))
    posixdir = os.path.join(gwdir, "posix/bin/") 
    cmd = "echo | %s/configureserver --dburl=%s --dbuser=%s --dbpass=%s" % (posixdir,dburl,dbuser,dbpass) 
    execute("bash", ["-c", cmd])


def startAnalytics(gwdir) :
    banner("Starting Analytics on %s" % (hostname))

    managementPort = 8040 

    # Register this host with the dns server running on anm.
    configureResolvConf()
    registerWithDNS(hostname, ip)

    execute(os.path.join(gwdir, "posix/bin/analytics"), ["-d"])

    waitForPort(managementPort)


def unblock(signal, frame) :
    global block
    print "Exiting"
    block = False

if __name__ == "__main__":
    parseOptions()
    manageAnalytics()

    if options.block :
        global block
        block = options.block
        banner("Staying alive")
        signal.signal(signal.SIGINT, unblock)
        while block :
            time.sleep(5)
