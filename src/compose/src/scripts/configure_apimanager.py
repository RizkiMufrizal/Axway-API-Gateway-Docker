#!/usr/bin/env python2.7
'''
Script for configuring apimanager
'''
import os
import socket
import argparse
from lib.scriptutil import *

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")
    parser.add_argument("--version", default="7.3.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="changeme")
    parser.add_argument("--adminPass", default="changeme")
    parser.add_argument("-g", "--group")
    parser.add_argument("-n", "--instance")
    parser.add_argument("--portalPort", default="8075")
    parser.add_argument("--trafficPort", default="8065")

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

    if not options.group :
        parser.error("No group specified.")

    if not options.instance :
        parser.error("No instance specified.")

def configureApiManager() :
    banner("""Configuring API Manager on %s: %s:%s
Traffic Port: %s
Portal Port:   %s""" % (hostname, options.group, options.instance, options.trafficPort, options.portalPort))

    if options.version <= "7.2.2" :
        try :
            execute(os.path.join(options.gwdir, "samples/scripts/run.sh"), [
                os.path.join(options.gwdir, "webapps/apiportal/conf/setup-apiportal.py"),
                "-g", options.group,
                "-n", options.instance,
                "--portalport", options.portalPort,
                "--username", options.username,
                "--password", options.password],
                cwd = os.path.join(options.gwdir, "samples/scripts"))
        except :
            print "SWALLOWING ERROR: setup-apiportal fails to restart the gateway at times. Keep going and hope."

        # Traffic port has to be set manually for 7.2.2
        configureEnvProperties(options.gwdir, options.group, options.instance, [("env.PORT.PORTAL.TRAFFIC", options.trafficPort)])

    elif options.version < "7.4.0" :
        try :
            execute(os.path.join(options.gwdir, "samples/scripts/run.sh"), [
                os.path.join(options.gwdir, "webapps/apiportal/conf/setup-apiportal.py"),
                "-g", options.group,
                "-n", options.instance,
                "--trafficport", options.trafficPort,
                "--portalport", options.portalPort,
                "--username", options.username,
                "--password", options.password],
                cwd = os.path.join(options.gwdir, "samples/scripts"))
        except :
            print "SWALLOWING ERROR: setup-apiportal fails to restart the gateway at times. Keep going and hope."

    else :
        execute(os.path.join(options.gwdir, "posix/bin/setup-apimanager"), [
            "-g", options.group,
            "-n", options.instance,
            "--trafficport", options.trafficPort,
            "--portalport", options.portalPort,
            "--username", options.username,
            "--password", options.password,
            "--adminPass", options.adminPass],
            cwd = os.path.join(options.gwdir, "posix/bin"))

        # Wait for it to come up.
        waitForPort(options.portalPort)
        waitForPort(options.trafficPort)

if __name__ == "__main__":
    parseOptions()
    configureApiManager()

