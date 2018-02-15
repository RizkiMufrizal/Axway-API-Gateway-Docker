#!/usr/bin/env python2.7
'''
Script for configuring envSettings.props
'''
import os
import socket
import string
import argparse
from lib.scriptutil import *


hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")
    parser.add_argument("-g", "--group")
    parser.add_argument("-n", "--instance")
    parser.add_argument("-p", "--property", action="append", type=str, dest="properties")

    (options, unknown) = parser.parse_known_args()

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not options.gwdir :
        parser.error("No gateway directory specified.")

    if not os.path.isdir(options.gwdir) :
        parser.error("Directory not found: %s" % options.gwdir)

    if not options.group :
        parser.error("No group specified.")

    if not options.instance :
        parser.error("No instance specified.")

    if not options.properties :
        parser.error("No properties specified.")

def configureEnvProperties() :
    envSettings = os.path.join(options.gwdir, "groups/topologylinks", "%s-%s" % (options.group, options.instance), "conf/envSettings.props")

    for prop in options.properties :
        propVal = string.split(prop, "=", 1)

        if (len(findInFile(envSettings, propVal[0] + "=")) > 0) :
            # Modify existing value
            matchStr = r'^%s=.*$' % propVal[0]
        else :
            # Append new value
            matchStr = r'\Z'

        replaceAll(envSettings, [(matchStr, '%s=%s\n' % (propVal[0], propVal[1]))])

if __name__ == "__main__":
    parseOptions()
    configureEnvProperties()

