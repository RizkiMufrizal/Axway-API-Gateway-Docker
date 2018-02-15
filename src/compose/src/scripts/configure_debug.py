#!/usr/bin/env python2.7
'''
Script for configuring debug on a gw instance 
'''
import os
import socket
import argparse
from lib.scriptutil import *
from lib.configimporterutil import *

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

def parseOptions() :
    global options

    parser = argparse.ArgumentParser()
    parser.add_argument("--gwdir")
    parser.add_argument("-u", "--username", default="admin")
    parser.add_argument("-p", "--password", default="changeme")
    parser.add_argument("-g", "--group")
    parser.add_argument("-n", "--instance")
    parser.add_argument("-s", "--svcPort", default="8080")
    parser.add_argument("--passphrase", default='', help="The group passphrase.")

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

def configureEntityStore() :
    frags = []
    args = {}
    frags.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/debugInstance.py"))

    importConfig(options, frags, **args)

    waitForPort(int(options.svcPort))


if __name__ == "__main__":
    parseOptions()
    configureEntityStore()

